"""Signed payment votes and unsigned head vote declarations."""

from importlib import import_module
from itertools import islice

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.keys import get_vrf_proof, privkeys
from eth_consensus_specs.test.helpers.pq.fork import upgrade_registered_to_pq

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.fixture
def spec(preset, monkeypatch):
    spec = import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")
    config = {**spec.config._asdict(), "PQ_FORK_EPOCH": spec.Epoch(0)}
    monkeypatch.setattr(spec, "config", spec.config.__class__(**config))
    return spec


@pytest.fixture
def state(spec):
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    balances = [eip8483.MAX_EFFECTIVE_BALANCE] * (2 * spec.HEAD_VOTE_PAYMENT_TARGET)
    pre = create_genesis_state(eip8483, balances, eip8483.MAX_EFFECTIVE_BALANCE)
    state = upgrade_registered_to_pq(spec, pre)
    spec.process_slots(state, spec.Slot(3))
    return state


def elected_messages(spec, state, data):
    for raw_index in range(len(state.validators)):
        index = spec.ValidatorIndex(raw_index)
        proof = spec.VRFProof(data=get_vrf_proof(index))
        if spec.get_head_vote_weight(state, data.slot, index, proof) > 0:
            yield spec.HeadVoteMessage(
                validator_index=index,
                data=data,
                signature=spec.get_head_vote_signature(state, data, privkeys[index]),
                proof=proof,
            )


def signed_vote(spec, state, slot, payload_status=None, count=2):
    data = spec.HeadVoteData(
        slot=slot,
        beacon_block_root=spec.get_block_root_at_slot(state, spec.Slot(slot)),
        payload_status=spec.PAYLOAD_STATUS_EMPTY if payload_status is None else payload_status,
    )
    messages = list(islice(elected_messages(spec, state, data), count))
    return spec.get_aggregate_head_vote(state, messages)


def prove_head_votes(spec, state, votes):
    # The block's proof of the signatures of its head votes, in order
    statements = [spec.get_head_vote_statement(state, vote) for vote in votes]
    signatures = [
        [
            spec.get_head_vote_signature(state, vote.data, privkeys[credential.validator_index])
            for credential in vote.credentials
        ]
        for vote in votes
    ]
    return spec.AttestationProof(data=spec.stark.ProveAggregates(statements, signatures))


def test_stalled_era_uses_frozen_stake_and_slot_opening(spec, state):
    slot = state.slot
    proof = spec.VRFProof(data=get_vrf_proof(0))
    # A different bottom sibling makes this opening slot-specific.
    proof[1] = spec.Bytes32(b"\x95" * 32)
    state.validators[0].vrf_root = spec.compute_merkle_branch_root(
        proof[0], proof[1:], spec.VRF_TREE_DEPTH, slot
    )
    state.head_vote_lotteries[0] = spec.HeadVoteLottery(
        weights=spec.HeadVoteWeights(data=[1]), total_weight=1
    )
    index = spec.ValidatorIndex(0)
    assert spec.get_head_vote_weight(state, slot, index, proof) == spec.HEAD_VOTE_COMMITTEE_SIZE
    state.validators[0].slashed = True
    state.validators[0].exit_epoch = spec.Epoch(0)
    assert not spec.process_era(state)
    assert spec.get_head_vote_weight(state, slot, index, proof) == spec.HEAD_VOTE_COMMITTEE_SIZE
    assert spec.get_head_vote_weight(state, slot + 1, index, proof) == 0
    new_validator_proof = spec.VRFProof(data=get_vrf_proof(1))
    assert spec.is_valid_vrf_proof(state, 1, slot, new_validator_proof)
    assert spec.get_head_vote_weight(state, slot, spec.ValidatorIndex(1), new_validator_proof) == 0


def test_lottery_rollover_retains_duty_state(spec, state):
    # Disjoint snapshots make selection from the wrong side of the cursor visible.
    first = spec.HeadVoteLottery(weights=spec.HeadVoteWeights(data=[1, 0]), total_weight=1)
    second = spec.HeadVoteLottery(weights=spec.HeadVoteWeights(data=[0, 1]), total_weight=1)
    state.head_vote_lotteries[0] = first
    state.head_vote_lotteries[1] = second
    state.head_vote_sealed_lottery = first
    size = spec.HEAD_VOTE_COMMITTEE_SIZE
    state.era = spec.Era(size - 2)
    state.era_start_slot = spec.Slot(1)
    state.finalized_checkpoint.height = spec.Height(1)
    assert not spec.process_era(state)
    state.finalized_slot = spec.Slot(1)
    assert spec.process_era(state)
    spec.process_head_vote_lottery_rotation(state)
    assert state.era == size - 1
    assert state.head_vote_lotteries[2] == first
    slot = state.slot
    proof = spec.VRFProof(data=get_vrf_proof(1))
    lanes = spec.compute_head_vote_lanes(
        second, spec.Uint64(1), slot, spec.ValidatorIndex(1), proof[0]
    )
    assert len(lanes) == size
    expected = sum(lane < size - 1 for lane in lanes)
    assert spec.get_head_vote_weight(state, slot, spec.ValidatorIndex(1), proof) == expected

    spec.process_slots(state, slot + 1)
    assert not spec.process_era(state)
    state.finalized_slot = slot
    assert spec.process_era(state)
    spec.process_head_vote_lottery_rotation(state)
    assert state.era == size
    assert spec.get_head_vote_weight(state, slot, spec.ValidatorIndex(1), proof) == expected

    # The voted head admitted this credential at T - 1. An including chain that
    # recorded era zero for the same duty still uses only batch zero.
    data = spec.HeadVoteData(
        slot=slot,
        beacon_block_root=spec.get_block_root_at_slot(state, slot),
        payload_status=spec.PAYLOAD_STATUS_EMPTY,
    )
    message = spec.HeadVoteMessage(
        validator_index=1,
        data=data,
        proof=proof,
        signature=spec.get_head_vote_signature(state, data, privkeys[1]),
    )
    aggregate = spec.get_aggregate_head_vote(state, [message])
    spec.process_head_vote(state, aggregate)
    state.head_vote_era_history[slot % len(state.head_vote_era_history)] = spec.Era(0)
    with pytest.raises(AssertionError):
        spec.process_head_vote(state, aggregate)

    new_proof = spec.VRFProof(data=get_vrf_proof(1))
    assert spec.get_head_vote_weight(state, state.slot, spec.ValidatorIndex(1), new_proof) == size
    assert (
        spec.compute_head_vote_lanes(
            second, spec.Uint64(1), state.slot, spec.ValidatorIndex(1), new_proof[0]
        )
        != lanes
    )


def test_same_slot_vote_records_participation(spec, state):
    # Give slot 2 its own block so that its votes are for the block of their slot
    state.block_roots[2 % spec.SLOTS_PER_HISTORICAL_ROOT] = spec.Root(b"\x22" * 32)
    earlier = signed_vote(spec, state, 1)
    spec.process_head_vote(state, earlier)
    assert not any(any(bits) for bits in state.head_vote_participation)

    vote = signed_vote(spec, state, 2, spec.PAYLOAD_STATUS_PENDING)
    spec.process_head_vote(state, vote)
    expected = [credential.validator_index for credential in vote.credentials]
    for index, voters in enumerate(state.head_vote_participation):
        assert list(voters) == (expected if index == spec.SLOTS_PER_EPOCH + 2 else [])


@pytest.mark.parametrize(
    ("status", "valid"),
    [
        ("PAYLOAD_STATUS_EMPTY", False),
        ("PAYLOAD_STATUS_FULL", False),
        ("PAYLOAD_STATUS_PENDING", True),
    ],
)
def test_same_slot_vote_must_be_pending(spec, state, status, valid):
    # Give slot 2 its own block so that its votes are for the block of their slot
    state.block_roots[2 % spec.SLOTS_PER_HISTORICAL_ROOT] = spec.Root(b"\x22" * 32)
    vote = signed_vote(spec, state, 2, getattr(spec, status))
    if valid:
        spec.process_head_vote(state, vote)
    else:
        with pytest.raises(AssertionError):
            spec.process_head_vote(state, vote)


@pytest.mark.parametrize("root_kind", ["older", "same_slot", "sibling"])
@pytest.mark.parametrize("status", [0, 1, 2])
def test_head_vote_status_uses_canonical_slot_evidence(spec, state, root_kind, status):
    older = spec.get_block_root_at_slot(state, spec.Slot(0))
    state.block_roots[1 % spec.SLOTS_PER_HISTORICAL_ROOT] = spec.Root(b"\x11" * 32)
    same_slot = spec.Root(b"\x22" * 32)
    sibling = spec.Root(b"\x33" * 32)
    state.block_roots[2 % spec.SLOTS_PER_HISTORICAL_ROOT] = same_slot
    root = {"older": older, "same_slot": same_slot, "sibling": sibling}[root_kind]
    data = spec.HeadVoteData(slot=2, beacon_block_root=root, payload_status=status)
    opening = next(
        (index, proof)
        for index in range(len(state.validators))
        if spec.get_head_vote_weight(
            state,
            data.slot,
            spec.ValidatorIndex(index),
            proof := spec.VRFProof(data=get_vrf_proof(index)),
        )
    )
    index, proof = opening
    message = spec.HeadVoteMessage(
        validator_index=index,
        data=data,
        signature=spec.get_head_vote_signature(state, data, privkeys[index]),
        proof=proof,
    )
    valid = root_kind == "sibling" or (root_kind == "same_slot") == (
        status == spec.PAYLOAD_STATUS_PENDING
    )
    assert (spec.get_head_vote_message_weight(state, message) > 0) == valid
    aggregate = spec.HeadVote(
        data=data,
        credentials=spec.HeadVoteCredentials(
            data=[spec.HeadVoteCredential(validator_index=index, proof=proof)]
        ),
    )
    if valid:
        spec.process_head_vote(state, aggregate)
    else:
        with pytest.raises(AssertionError):
            spec.process_head_vote(state, aggregate)


@pytest.mark.parametrize("canonical", [False, True])
@pytest.mark.parametrize("status", [0, 1, 2])
def test_genesis_vote_status_and_participation_require_canonical_root(
    spec, state, canonical, status
):
    root = spec.get_block_root_at_slot(state, spec.GENESIS_SLOT)
    if not canonical:
        root = spec.Root(b"\xff" * 32)
    data = spec.HeadVoteData(slot=0, beacon_block_root=root, payload_status=status)
    opening = next(
        (index, proof)
        for index in range(len(state.validators))
        if spec.get_head_vote_weight(
            state,
            data.slot,
            spec.ValidatorIndex(index),
            proof := spec.VRFProof(data=get_vrf_proof(index)),
        )
    )
    index, proof = opening
    message = spec.HeadVoteMessage(
        validator_index=index,
        data=data,
        signature=spec.get_head_vote_signature(state, data, privkeys[index]),
        proof=proof,
    )
    valid = not canonical or status == spec.PAYLOAD_STATUS_PENDING
    assert (spec.get_head_vote_message_weight(state, message) > 0) == valid
    aggregate = spec.HeadVote(
        data=data,
        credentials=spec.HeadVoteCredentials(
            data=[spec.HeadVoteCredential(validator_index=index, proof=proof)]
        ),
    )
    if valid:
        spec.process_head_vote(state, aggregate)
    else:
        with pytest.raises(AssertionError):
            spec.process_head_vote(state, aggregate)
    for slot, voters in enumerate(state.head_vote_participation):
        expected = [index] if canonical and valid and slot == spec.SLOTS_PER_EPOCH else []
        assert list(voters) == expected


@pytest.mark.parametrize("expired", [False, True])
@pytest.mark.parametrize("status", [0, 1, 2])
def test_genesis_payload_status_at_history_expiry(spec, state, expired, status):
    root = spec.get_block_root_at_slot(state, spec.GENESIS_SLOT)
    state.slot = spec.Slot(spec.SLOTS_PER_HISTORICAL_ROOT + int(expired))
    if expired:
        state.block_roots[0] = spec.Root(b"\xff" * 32)
    data = spec.HeadVoteData(slot=0, beacon_block_root=root, payload_status=status)
    # Once genesis expires, this predicate has no canonical evidence for it.
    # Inclusion and receipt enforce vote freshness separately.
    expected = expired or status == spec.PAYLOAD_STATUS_PENDING
    assert spec.is_head_vote_payload_status_valid(state, data) == expected


@pytest.mark.parametrize(
    ("heads", "support", "valid"),
    [
        ([1, 2], [False, True], True),
        ([1, 1], [False, True], False),
        ([1, 2], [True], False),
        ([1, 2, 3], [False] * 3, True),
    ],
)
def test_operations_check_declarations(spec, state, heads, support, valid):
    body = spec.BeaconBlockBody()
    for head in heads:
        body.head_vote_declarations.append(
            spec.HeadVoteDeclaration(
                validator_index=1234, beacon_block_root=spec.Root(bytes([head]) * 32)
            )
        )
    body.head_vote_support_bits = spec.HeadVoteSupportBits(data=support)
    if valid:
        spec.process_operations(state, body)
        assert not any(any(bits) for bits in state.head_vote_participation)
    else:
        with pytest.raises(AssertionError):
            spec.process_operations(state, body)


@pytest.mark.parametrize("shortfall", [0, 1])
def test_last_eligible_block_credits_previous_epoch_once(spec, state, shortfall):
    state.block_roots[2] = spec.Root(b"\x22" * 32)
    withdrawal = spec.BuilderPendingWithdrawal(amount=1)
    state.builder_pending_payments[spec.SLOTS_PER_EPOCH + 2].withdrawal = withdrawal
    count = spec.HEAD_VOTE_PAYMENT_TARGET - shortfall
    vote = signed_vote(spec, state, 2, spec.PAYLOAD_STATUS_PENDING, count)
    expected = [credential.validator_index for credential in vote.credentials]
    assert len(expected) == count
    assert (
        sum(
            spec.get_head_vote_weight(
                state, vote.data.slot, credential.validator_index, credential.proof
            )
            for credential in vote.credentials
        )
        >= spec.HEAD_VOTE_PAYMENT_TARGET
    )
    spec.process_slots(state, spec.Slot(2 * spec.SLOTS_PER_EPOCH - 1))
    assert not state.builder_pending_withdrawals
    spec.process_head_vote(state, vote)
    assert list(state.head_vote_participation[2]) == expected
    before = state.hash_tree_root()
    spec.process_head_vote(state, vote)
    assert state.hash_tree_root() == before
    spec.process_slots(state, spec.Slot(2 * spec.SLOTS_PER_EPOCH))
    assert list(state.builder_pending_withdrawals) == ([] if shortfall else [withdrawal])
    with pytest.raises(AssertionError):
        spec.process_head_vote(state, vote)


def test_declaration_slot_and_full_pool_bound(spec, state, monkeypatch):
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=1))
    state.slot = spec.Slot(spec.SLOTS_PER_EPOCH)
    body = spec.BeaconBlockBody()
    spec.process_operations(state, body)
    for index in range(2 * spec.HEAD_VOTE_COMMITTEE_SIZE):
        for status in (spec.PAYLOAD_STATUS_EMPTY, spec.PAYLOAD_STATUS_FULL):
            body.head_vote_declarations.append(
                spec.HeadVoteDeclaration(validator_index=index, payload_status=status)
            )
            body.head_vote_support_bits.append(False)
    with pytest.raises(AssertionError):
        spec.process_operations(state, body)
    state.slot += 1
    spec.process_operations(state, body)
    body.head_vote_declarations.append(spec.HeadVoteDeclaration(validator_index=index + 1))
    body.head_vote_support_bits.append(False)
    with pytest.raises(AssertionError):
        spec.process_operations(state, body)


@pytest.mark.parametrize("valid_proof", [True, False])
def test_block_proof_covers_aggregates_not_declarations(spec, state, valid_proof):
    # A signed aggregate of an earlier slot counts for payments only through the
    # block's proof; the declarations of the previous slot carry no signature
    # and add no statement to it
    body = spec.BeaconBlockBody()
    body.head_votes.append(signed_vote(spec, state, 1))
    body.head_vote_declarations.append(
        spec.HeadVoteDeclaration(validator_index=1234, beacon_block_root=spec.Root(b"\x01" * 32))
    )
    body.head_vote_support_bits = spec.HeadVoteSupportBits(data=[True])
    body.proof = prove_head_votes(spec, state, body.head_votes)
    if valid_proof:
        spec.process_operations(state, body)
    else:
        # A proof of no statements does not cover the aggregate
        body.proof = spec.AttestationProof()
        with pytest.raises(AssertionError):
            spec.process_operations(state, body)
