"""Gossip validation of FG attestations on ``attestation_{subnet_id}``."""

from dataclasses import fields
from importlib import import_module
from typing import get_origin

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.keys import privkeys
from eth_consensus_specs.test.helpers.pq.fork import (
    register_xmss_pubkeys,
    upgrade_registered_to_pq,
)

ATTESTER = 1

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.fixture
def spec(preset):
    return import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")


def set_fork_epoch(spec, monkeypatch, epoch):
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=spec.Epoch(epoch)))


@pytest.fixture(autouse=True)
def fork_at_genesis(spec, monkeypatch):
    set_fork_epoch(spec, monkeypatch, 0)


@pytest.fixture
def state(spec):
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    balances = [eip8483.MAX_EFFECTIVE_BALANCE] * 64
    pre = create_genesis_state(eip8483, balances, eip8483.MAX_EFFECTIVE_BALANCE)
    state = upgrade_registered_to_pq(spec, pre)
    spec.process_slots(state, state.slot + 1)
    return state


def make_store(spec, head_root, head_state):
    block = spec.BeaconBlock(slot=head_state.slot)
    return spec.Store(
        time_ms=spec.Uint64(0),
        genesis_time_ms=spec.Uint64(0),
        justified_checkpoint=spec.HeightCheckpoint(),
        finalized_checkpoint=spec.HeightCheckpoint(),
        proposer_boost_root=spec.Root(),
        blocks={head_root: block},
        block_states={head_root: head_state},
        latest_messages={},
        payloads={},
        payload_timeliness_vote={},
        payload_data_availability_vote={},
        max_height=spec.Height(0),
        block_receipt_times={},
        payload_receipt_times={},
        latest_confirmed=spec.ForkChoiceNode(
            root=head_root, payload_status=spec.PAYLOAD_STATUS_PENDING
        ),
        saved_confirmations={},
        locks=set(),
        head_vote_messages={},
        head_vote_message_receipt_times={},
        head_vote_committees={},
    )


def make_seen(spec):
    return spec.Seen(
        **{field.name: (get_origin(field.type) or field.type)() for field in fields(spec.Seen)}
    )


def committee_round(spec, committee_index, slot):
    # The round of the latest slot of the committee at or before ``slot``
    round = spec.compute_round_at_slot(slot)
    while round > 0 and spec.compute_attestation_committee_slot(round, committee_index) > slot:
        round -= 1
    return spec.Round(round)


def sign(spec, state, data, attester=ATTESTER, committee_index=None, round=None, slot=None):
    if committee_index is None:
        committee_index = attester % spec.ATTESTATION_COMMITTEES_PER_ROUND
    if slot is None:
        slot = 2 * spec.SLOTS_PER_ROUND
    if round is None:
        round = committee_round(spec, committee_index, spec.Slot(slot))
    domain = spec.get_domain(
        state, spec.DOMAIN_FINALITY_ATTESTER, spec.get_attestation_epoch(state, data)
    )
    signing_root = spec.compute_signing_root(data, domain)
    leaf_index = spec.compute_xmss_attestation_leaf_index(round)
    return spec.SingleAttestation(
        committee_index=committee_index,
        attester_index=attester,
        data=data,
        signature=spec.xmss.Sign(privkeys[attester], leaf_index, signing_root),
        round=round,
    )


def validate(spec, monkeypatch, store, attestation, head_root, seen=None, slot=None):
    head = spec.ForkChoiceNode(root=head_root, payload_status=spec.PAYLOAD_STATUS_EMPTY)
    monkeypatch.setattr(spec, "get_head", lambda _store: head)
    if seen is None:
        seen = make_seen(spec)
    if slot is None:
        # A slot after the first round, so every committee has a started slot
        slot = 2 * spec.SLOTS_PER_ROUND
    time_ms = spec.compute_time_at_slot_ms(spec.Uint64(0), spec.Slot(slot))
    subnet = spec.compute_subnet_for_attestation(attestation.committee_index)
    spec.validate_attestation_gossip(seen, store, attestation, time_ms, subnet)
    return seen


def add_target_state(spec, store, state, height):
    # The post-state of a block that opened ``height``
    target_state = state.copy()
    target_state.target_checkpoint = spec.HeightCheckpoint(height=height, root=spec.Root())
    store.block_states[state.target_checkpoint.root] = target_state


def current_data(spec, state):
    return spec.AttestationData(
        target=state.target_checkpoint.copy(), timeout=False, finality=spec.HeightCheckpoint()
    )


def test_current_target_is_accepted(spec, state, monkeypatch):
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    seen = validate(spec, monkeypatch, store, sign(spec, state, current_data(spec, state)), head)
    assert len(seen.attestation_validator_rounds) == 1


def test_non_current_target_is_ignored(spec, state, monkeypatch):
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    data = current_data(spec, state)
    data.target.height += 1
    with pytest.raises(spec.GossipIgnore, match="not for the current or previous target"):
        validate(spec, monkeypatch, store, sign(spec, state, data), head)


def test_previous_target_is_accepted(spec, state, monkeypatch):
    previous = spec.HeightCheckpoint(height=1, root=spec.Root(b"\x05" * 32))
    state.previous_target_checkpoint = previous
    state.target_checkpoint.height = spec.Height(2)
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    data = spec.AttestationData(target=previous, timeout=False, finality=spec.HeightCheckpoint())
    seen = validate(spec, monkeypatch, store, sign(spec, state, data), head)
    assert len(seen.attestation_validator_rounds) == 1
    # Two heights back is ignored
    state.previous_target_checkpoint = spec.HeightCheckpoint(height=1, root=spec.Root(b"\x06" * 32))
    with pytest.raises(spec.GossipIgnore, match="not for the current or previous target"):
        validate(spec, monkeypatch, store, sign(spec, state, data), head)


def test_head_on_branch_split_before_target_is_ignored(spec, state, monkeypatch):
    # The head's branch has another target, and on it the attester has exited,
    # so checking its committee there would wrongly reject the attestation.
    data = current_data(spec, state)
    attestation = sign(spec, state, data)
    branch = state.copy()
    branch.target_checkpoint.root = spec.Root(b"\x02" * 32)
    branch.validators[ATTESTER].exit_epoch = spec.Epoch(0)
    head = spec.Root(b"\x03" * 32)
    store = make_store(spec, head, branch)
    with pytest.raises(spec.GossipIgnore, match="not for the current or previous target"):
        validate(spec, monkeypatch, store, attestation, head)


def test_wrong_committee_is_rejected(spec, state, monkeypatch):
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    wrong = (ATTESTER + 1) % spec.ATTESTATION_COMMITTEES_PER_ROUND
    attestation = sign(spec, state, current_data(spec, state), committee_index=wrong)
    with pytest.raises(spec.GossipReject, match="not a member of the committee"):
        validate(spec, monkeypatch, store, attestation, head)


def test_target_height_must_match_target_block(spec, state, monkeypatch):
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    add_target_state(spec, store, state, state.target_checkpoint.height)
    validate(spec, monkeypatch, store, sign(spec, state, current_data(spec, state)), head)
    data = current_data(spec, state)
    data.target.height += 1
    with pytest.raises(spec.GossipReject, match="did not open the target height"):
        validate(spec, monkeypatch, store, sign(spec, state, data), head)


def test_target_block_that_opened_no_height_is_rejected(spec, state, monkeypatch):
    state.target_checkpoint.height = spec.Height(2)
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    # The target block's own state has a filled-in target, so it opened no height
    store.block_states[state.target_checkpoint.root] = state.copy()
    with pytest.raises(spec.GossipReject, match="did not open the target height"):
        validate(spec, monkeypatch, store, sign(spec, state, current_data(spec, state)), head)


def test_first_round_before_committee_slot_is_ignored(spec, state, monkeypatch):
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    committee_index = next(
        index
        for index in range(spec.ATTESTATION_COMMITTEES_PER_ROUND)
        if spec.compute_attestation_committee_slot(spec.GENESIS_ROUND, index) > spec.GENESIS_SLOT
    )
    # Timing is checked before signer membership, independently of registry size.
    attestation = sign(spec, state, current_data(spec, state), committee_index=committee_index)
    with pytest.raises(spec.GossipIgnore, match="no slot of the attestation committee"):
        validate(spec, monkeypatch, store, attestation, head, slot=spec.GENESIS_SLOT)


def test_stale_row_does_not_take_the_round(spec, state, monkeypatch):
    state.target_checkpoint.height = spec.Height(5)
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    stale = current_data(spec, state)
    stale.target.height -= 1
    stale.target.root = spec.Root(b"\x04" * 32)
    seen = make_seen(spec)
    with pytest.raises(spec.GossipIgnore, match="not for the current or previous target"):
        validate(spec, monkeypatch, store, sign(spec, state, stale), head, seen=seen)
    assert len(seen.attestation_validator_rounds) == 0
    validate(
        spec, monkeypatch, store, sign(spec, state, current_data(spec, state)), head, seen=seen
    )
    assert len(seen.attestation_validator_rounds) == 1


def test_other_round_is_ignored(spec, state, monkeypatch):
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    committee_index = ATTESTER % spec.ATTESTATION_COMMITTEES_PER_ROUND
    round = committee_round(spec, committee_index, spec.Slot(2 * spec.SLOTS_PER_ROUND))
    attestation = sign(spec, state, current_data(spec, state), round=round - 1)
    with pytest.raises(spec.GossipIgnore, match="round is not the round"):
        validate(spec, monkeypatch, store, attestation, head)


def test_signature_at_another_leaf_is_rejected(spec, state, monkeypatch):
    head = spec.Root(b"\x01" * 32)
    store = make_store(spec, head, state)
    attestation = sign(spec, state, current_data(spec, state))
    other = sign(spec, state, current_data(spec, state), round=attestation.round + 1)
    attestation.signature = other.signature
    with pytest.raises(spec.GossipReject, match="invalid attestation signature"):
        validate(spec, monkeypatch, store, attestation, head)


@pytest.fixture
def fork_transition(spec, monkeypatch):
    # The fork activates at epoch 1; the genesis block is the last Heze block
    set_fork_epoch(spec, monkeypatch, 1)
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    balances = [eip8483.MAX_EFFECTIVE_BALANCE] * 64
    heze_state = create_genesis_state(eip8483, balances, eip8483.MAX_EFFECTIVE_BALANCE)
    # The pre-fork states that gossip upgrades carry the registrations
    register_xmss_pubkeys(eip8483, heze_state)
    fork_slot = spec.compute_start_slot_at_epoch(spec.Epoch(1))
    pre = heze_state.copy()
    eip8483.process_slots(pre, fork_slot)
    heze_root = pre.latest_block_header.hash_tree_root()
    upgraded = upgrade_registered_to_pq(spec, pre)
    assert upgraded.target_checkpoint == spec.HeightCheckpoint(height=1, root=heze_root)
    return heze_state, heze_root, upgraded, fork_slot


def add_block(spec, store, root, slot, block_state):
    store.blocks[root] = spec.BeaconBlock(slot=slot)
    store.block_states[root] = block_state


def test_height_one_with_pre_fork_head_is_accepted(spec, monkeypatch, fork_transition):
    heze_state, heze_root, upgraded, fork_slot = fork_transition
    store = make_store(spec, heze_root, heze_state)
    store.blocks[heze_root] = spec.BeaconBlock(slot=heze_state.slot)
    data = current_data(spec, upgraded)
    slot = fork_slot + 2 * spec.SLOTS_PER_ROUND
    attestation = sign(spec, upgraded, data, slot=slot)
    seen = validate(spec, monkeypatch, store, attestation, heze_root, slot=slot)
    assert len(seen.attestation_validator_rounds) == 1


def test_height_one_with_post_fork_head(spec, monkeypatch, fork_transition):
    heze_state, heze_root, upgraded, fork_slot = fork_transition
    head_state = upgraded.copy()
    spec.process_slots(head_state, fork_slot + 1)
    head = spec.Root(b"\x05" * 32)
    store = make_store(spec, head, head_state)
    add_block(spec, store, heze_root, heze_state.slot, heze_state)
    slot = fork_slot + 2 * spec.SLOTS_PER_ROUND
    data = current_data(spec, head_state)
    validate(spec, monkeypatch, store, sign(spec, head_state, data, slot=slot), head, slot=slot)
    # A pre-fork block is the target of height 1 only
    data.target.height = spec.Height(2)
    with pytest.raises(spec.GossipReject, match="did not open the target height"):
        validate(spec, monkeypatch, store, sign(spec, head_state, data, slot=slot), head, slot=slot)


def test_pre_fork_duty_is_ignored(spec, monkeypatch, fork_transition):
    _, _, upgraded, fork_slot = fork_transition
    head_state = upgraded.copy()
    spec.process_slots(head_state, fork_slot + 1)
    head = spec.Root(b"\x05" * 32)
    store = make_store(spec, head, head_state)
    round = spec.compute_round_at_slot(fork_slot)
    committee_index = next(
        index
        for index in range(spec.ATTESTATION_COMMITTEES_PER_ROUND)
        if spec.compute_attestation_committee_slot(round, index) > fork_slot
    )
    attestation = sign(
        spec, head_state, current_data(spec, head_state), committee_index=committee_index
    )
    with pytest.raises(spec.GossipIgnore, match="no slot of the attestation committee"):
        validate(spec, monkeypatch, store, attestation, head, slot=fork_slot)
