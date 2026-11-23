"""Signed payment votes and unsigned head vote declarations."""

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


def test_same_slot_vote_records_participation(spec, state):
    # Give slot 2 its own block so that its votes are for the block of their slot
    state.block_roots[2 % spec.SLOTS_PER_HISTORICAL_ROOT] = spec.Root(b"\x22" * 32)
    earlier = signed_vote(spec, state, 1)
    spec.process_head_vote(state, earlier)
    assert not any(any(bits) for bits in state.head_vote_participation)

    vote = signed_vote(spec, state, 2, spec.PAYLOAD_STATUS_PENDING)
    spec.process_head_vote(state, vote)
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
    index = spec.get_head_vote_committee(state, spec.GENESIS_SLOT)[0]
    message = spec.HeadVoteMessage(
        validator_index=index,
        data=data,
        signature=spec.get_head_vote_signature(state, data, privkeys[index]),
    )
    valid = not canonical or status == spec.PAYLOAD_STATUS_PENDING
    assert spec.is_valid_head_vote_message(state, message) == valid
    aggregate = spec.HeadVote(
        data=data,
        voter_indices=spec.HeadVoteCommitteeIndices(data=[index]),
    )
    if valid:
        spec.process_head_vote(state, aggregate)
    else:
        with pytest.raises(AssertionError):
            spec.process_head_vote(state, aggregate)
    for slot, bits in enumerate(state.head_vote_participation):
        expected = [False] * spec.HEAD_VOTE_COMMITTEE_SIZE
        if canonical and valid and slot == spec.SLOTS_PER_EPOCH:
            committee = spec.get_head_vote_committee(state, spec.GENESIS_SLOT)
            expected = [member == index for member in committee]
        assert [bool(bit) for bit in bits] == expected


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
        ([1, 2, 3], [False] * 3, False),
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


def test_last_eligible_block_credits_previous_epoch_once(spec, state):
    state.block_roots[2] = spec.Root(b"\x22" * 32)
    # Two validators hold the whole committee so their aggregate reaches quorum.
    state.head_vote_committee_window[spec.SLOTS_PER_EPOCH + 2] = spec.HeadVoteCommittee(
        data=[0, 1] * (spec.HEAD_VOTE_COMMITTEE_SIZE // 2)
    )
    withdrawal = spec.BuilderPendingWithdrawal(amount=1)
    state.builder_pending_payments[spec.SLOTS_PER_EPOCH + 2].withdrawal = withdrawal
    vote = signed_vote(spec, state, 2, spec.PAYLOAD_STATUS_PENDING)
    expected = [i in vote.voter_indices for i in spec.get_head_vote_committee(state, 2)]
    spec.process_slots(state, spec.Slot(2 * spec.SLOTS_PER_EPOCH - 1))
    assert not state.builder_pending_withdrawals
    spec.process_head_vote(state, vote)
    assert [bool(bit) for bit in state.head_vote_participation[2]] == expected
    before = state.hash_tree_root()
    spec.process_head_vote(state, vote)
    assert state.hash_tree_root() == before
    spec.process_slots(state, spec.Slot(2 * spec.SLOTS_PER_EPOCH))
    assert list(state.builder_pending_withdrawals) == [withdrawal]
    with pytest.raises(AssertionError):
        spec.process_head_vote(state, vote)


def test_declaration_slot_and_full_pool_bound(spec, state, monkeypatch):
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=1))
    state.slot = spec.Slot(spec.SLOTS_PER_EPOCH)
    body = spec.BeaconBlockBody()
    spec.process_operations(state, body)
    for index in range(spec.HEAD_VOTE_COMMITTEE_SIZE):
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
