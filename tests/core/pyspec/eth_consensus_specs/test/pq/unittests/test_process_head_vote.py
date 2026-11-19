"""Head votes and their support bits in block processing."""

from importlib import import_module

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.keys import privkeys
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
    balances = [eip8483.MAX_EFFECTIVE_BALANCE] * 64
    pre = create_genesis_state(eip8483, balances, eip8483.MAX_EFFECTIVE_BALANCE)
    state = upgrade_registered_to_pq(spec, pre)
    spec.process_slots(state, spec.Slot(3))
    return state


def signed_vote(spec, state, slot, payload_status=None):
    data = spec.HeadVoteData(
        slot=slot,
        beacon_block_root=spec.get_block_root_at_slot(state, spec.Slot(slot)),
        payload_status=spec.PAYLOAD_STATUS_EMPTY if payload_status is None else payload_status,
    )
    voters = sorted(set(spec.get_head_vote_committee(state, spec.Slot(slot))))[:2]
    messages = [
        spec.HeadVoteMessage(
            validator_index=index,
            data=data,
            signature=spec.get_head_vote_signature(state, data, privkeys[index]),
        )
        for index in voters
    ]
    return spec.get_aggregate_head_vote(state, messages)


def prove_head_votes(spec, state, votes):
    # The block's proof of the signatures of its head votes, in order
    statements = [spec.get_head_vote_statement(state, vote) for vote in votes]
    signatures = [
        [
            spec.get_head_vote_signature(state, vote.data, privkeys[index])
            for index in vote.voter_indices
        ]
        for vote in votes
    ]
    return spec.AttestationProof(data=spec.stark.ProveAggregates(statements, signatures))


@pytest.mark.parametrize(
    ("slot", "is_supported", "valid"),
    [(2, True, True), (2, False, True), (1, True, False), (1, False, True)],
)
def test_support_requires_previous_slot_vote(spec, state, slot, is_supported, valid):
    vote = signed_vote(spec, state, slot)
    if valid:
        spec.process_head_vote(state, vote, is_supported)
    else:
        with pytest.raises(AssertionError):
            spec.process_head_vote(state, vote, is_supported)


@pytest.mark.parametrize("is_supported", [False, True])
def test_same_slot_vote_records_participation(spec, state, is_supported):
    # Give slot 2 its own block so that its votes are for the block of their slot
    state.block_roots[2 % spec.SLOTS_PER_HISTORICAL_ROOT] = spec.Root(b"\x22" * 32)
    earlier = signed_vote(spec, state, 1)
    spec.process_head_vote(state, earlier, is_supported=False)
    assert not any(any(bits) for bits in state.head_vote_participation)

    vote = signed_vote(spec, state, 2, spec.PAYLOAD_STATUS_PENDING)
    spec.process_head_vote(state, vote, is_supported)
    committee = spec.get_head_vote_committee(state, spec.Slot(2))
    expected = [index in vote.voter_indices for index in committee]
    for index, bits in enumerate(state.head_vote_participation):
        recorded = [bool(bit) for bit in bits]
        if index == spec.SLOTS_PER_EPOCH + 2:
            assert any(expected)
            assert recorded == expected
        else:
            assert not any(recorded)


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
        spec.process_head_vote(state, vote, is_supported=True)
    else:
        with pytest.raises(AssertionError):
            spec.process_head_vote(state, vote, is_supported=True)


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
    index = spec.get_head_vote_committee(state, spec.Slot(2))[0]
    message = spec.HeadVoteMessage(
        validator_index=index,
        data=data,
        signature=spec.get_head_vote_signature(state, data, privkeys[index]),
    )
    valid = root_kind == "sibling" or (root_kind == "same_slot") == (
        status == spec.PAYLOAD_STATUS_PENDING
    )
    assert spec.is_valid_head_vote_message(state, message) == valid
    aggregate = spec.HeadVote(
        data=data,
        voter_indices=spec.HeadVoteCommitteeIndices(data=[index]),
    )
    if valid:
        spec.process_head_vote(state, aggregate, is_supported=True)
    else:
        with pytest.raises(AssertionError):
            spec.process_head_vote(state, aggregate, is_supported=True)


@pytest.mark.parametrize(
    ("support", "valid"),
    [([False, True], True), ([True, True], False), ([False], False), ([False, True, False], False)],
)
def test_operations_check_support_bits(spec, state, support, valid):
    body = spec.BeaconBlockBody()
    # A vote of two slots ago followed by a vote of the previous slot
    body.head_votes.append(signed_vote(spec, state, 1))
    body.head_votes.append(signed_vote(spec, state, 2))
    body.head_vote_support = spec.HeadVoteSupport(data=support)
    body.proof = prove_head_votes(spec, state, body.head_votes)
    if valid:
        spec.process_operations(state, body)
    else:
        with pytest.raises(AssertionError):
            spec.process_operations(state, body)
