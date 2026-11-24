"""Signed payment votes and unsigned head vote declarations."""

from importlib import import_module
from itertools import islice

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.block import build_empty_block
from eth_consensus_specs.test.helpers.constants import EIP8483, PREVIOUS_FORK_OF
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
        proof = spec.VRFProof(data=get_vrf_proof(index, data.slot))
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
    return spec.stark_prove_aggregates(statements, signatures)


def test_stalled_dynasty_uses_frozen_stake_and_slot_opening(spec, state):
    slot = state.slot
    proof = spec.VRFProof(data=get_vrf_proof(0, slot))
    state.ac_snapshots[0] = spec.ACSnapshot(weights=spec.ACWeights(data=[1]))
    index = spec.ValidatorIndex(0)
    assert spec.get_head_vote_weight(state, slot, index, proof) == spec.HEAD_VOTE_COMMITTEE_SIZE
    state.validators[0].slashed = True
    state.validators[0].exit_epoch = spec.Epoch(0)
    assert spec.get_head_vote_weight(state, slot, index, proof) == spec.HEAD_VOTE_COMMITTEE_SIZE
    assert spec.get_head_vote_weight(state, slot + 1, index, proof) == 0
    next_proof = spec.VRFProof(data=get_vrf_proof(0, slot + 1))
    assert spec.get_head_vote_weight(state, slot + 1, index, next_proof) == (
        spec.HEAD_VOTE_COMMITTEE_SIZE
    )
    new_validator_proof = spec.VRFProof(data=get_vrf_proof(1, slot))
    assert spec.is_valid_vrf_proof(state, 1, slot, new_validator_proof)
    assert spec.get_head_vote_weight(state, slot, spec.ValidatorIndex(1), new_validator_proof) == 0


def test_snapshot_total_can_exceed_uint16(spec, state):
    slot = state.slot
    proof = spec.VRFProof(data=get_vrf_proof(0, slot))
    index = spec.ValidatorIndex(0)
    weight = int(spec.MAX_EFFECTIVE_BALANCE_ELECTRA // spec.EFFECTIVE_BALANCE_INCREMENT)
    assert spec.is_valid_vrf_proof(state, index, slot, proof)
    state.ac_snapshots[0] = spec.ACSnapshot(weights=spec.ACWeights(data=[weight] * 32))
    assert spec.get_head_vote_weight(state, slot, index, proof) <= weight


def test_ac_snapshot_rollover_retains_only_previous_dynasty(spec, state, monkeypatch):
    monkeypatch.setitem(PREVIOUS_FORK_OF, spec.fork, EIP8483)
    # Disjoint snapshots make selection on the wrong side of the interpolation index visible.
    first = spec.ACSnapshot(weights=spec.ACWeights(data=[1, 0]))
    second = spec.ACSnapshot(weights=spec.ACWeights(data=[0, 1]))
    state.ac_snapshots[0] = first
    state.ac_snapshots[1] = second
    state.ac_snapshots[2] = first
    size = spec.HEAD_VOTE_COMMITTEE_SIZE
    state.dynasty = spec.Dynasty(size - 2)
    state.dynasty_start_slot = spec.Slot(1)
    spec.advance_dynasty(state)
    assert state.dynasty == size - 1
    slot = state.slot
    proof = spec.VRFProof(data=get_vrf_proof(1, slot))
    seat_indices = spec.compute_ac_seat_indices(
        second, spec.Uint64(1), slot, spec.ValidatorIndex(1), proof[0]
    )
    assert len(seat_indices) == size
    expected = sum(seat_index < size - 1 for seat_index in seat_indices)
    assert spec.get_head_vote_weight(state, slot, spec.ValidatorIndex(1), proof) == expected

    spec.process_slots(state, slot + 2)
    spec.advance_dynasty(state)
    assert state.dynasty == size
    assert spec.get_head_vote_weight(state, slot, spec.ValidatorIndex(1), proof) == expected

    # The pre-rollover duty remains eligible immediately after rollover.
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

    new_proof = spec.VRFProof(data=get_vrf_proof(1, state.slot))
    assert spec.get_head_vote_weight(state, state.slot, spec.ValidatorIndex(1), new_proof) == size
    assert (
        spec.compute_ac_seat_indices(
            second, spec.Uint64(1), state.slot, spec.ValidatorIndex(1), new_proof[0]
        )
        != seat_indices
    )

    # The entry block can include the outgoing duty before it advances the
    # dynasty and captures the replacement in the retired descriptor's entry.
    spec.process_slots(state, slot + 4)
    quorum = spec.HeightParticipation(data=[spec.Boolean(value=True)] * len(state.validators))
    checkpoint = spec.HeightCheckpoint(height=2, root=spec.Root(b"\x02" * 32))
    state.justified_checkpoint = checkpoint
    state.target_checkpoint = spec.HeightCheckpoint(height=3, root=spec.Root(b"\x03" * 32))
    state.target_participation = quorum
    state.pending_finality.append(
        spec.PendingFinality(checkpoint=checkpoint, slot=slot + 2, participation=quorum)
    )
    block = build_empty_block(spec, state)
    block.body.head_votes.append(aggregate)
    block.body.proof = prove_head_votes(spec, state, block.body.head_votes)

    # A height entry finalizing an older dynasty leaves the interpolation index unchanged.
    older_finality = state.copy()
    older_finality.pending_finality[0].slot = slot + 1
    spec.process_block(older_finality, block)
    assert older_finality.target_checkpoint.height == 4
    assert older_finality.dynasty == size
    assert older_finality.ac_snapshots[0] == first

    spec.process_block(state, block)
    assert state.dynasty == size + 1
    assert len(state.ac_snapshots) == 3
    assert sum(int(weight) for weight in state.ac_snapshots[0].weights) > 1
    assert state.ac_snapshots[1] == second
    assert state.ac_snapshots[2] == first
    assert spec.get_head_vote_weight(state, slot, spec.ValidatorIndex(1), proof) == 0

    # Its child rejects the same duty although the payment epoch is still open.
    epoch = spec.get_current_epoch(state)
    assert state.ac_snapshots[0].capture_epoch == epoch
    assert spec.get_randao_mix(state, epoch) != spec.Bytes32()
    spec.process_slots(state, state.slot + 1)
    child = build_empty_block(spec, state)
    spec.process_block(state.copy(), child)
    child.body.head_votes.append(aggregate)
    child.body.proof = block.body.proof
    with pytest.raises(AssertionError):
        spec.process_block(state.copy(), child)

    # Capture fixes the weights; only the next full epoch's mix seals them.
    captured = state.ac_snapshots[0].weights.copy()
    state.validators[0].slashed = True
    seed_epoch_start = spec.compute_start_slot_at_epoch(epoch + 1)
    if state.slot < seed_epoch_start:
        spec.process_slots(state, seed_epoch_start)
    assert state.ac_snapshots[0].seed == spec.Bytes32()
    mix = spec.Bytes32(b"\x37" * 32)
    state.randao_mixes[(epoch + 1) % spec.EPOCHS_PER_HISTORICAL_VECTOR] = mix
    spec.process_slots(state, spec.compute_start_slot_at_epoch(epoch + 2))
    assert state.ac_snapshots[0].seed == mix
    assert state.ac_snapshots[0].weights == captured


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
            proof := spec.VRFProof(data=get_vrf_proof(index, data.slot)),
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
            proof := spec.VRFProof(data=get_vrf_proof(index, data.slot)),
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


def test_block_credential_limit_counts_across_aggregates(spec, state):
    vote = signed_vote(spec, state, 1, count=spec.HEAD_VOTE_PAYMENT_TARGET)
    assert len(vote.credentials) == spec.HEAD_VOTE_PAYMENT_TARGET
    body = spec.BeaconBlockBody()
    body.head_votes.append(vote)
    body.head_votes.append(vote)
    body.proof = prove_head_votes(spec, state, body.head_votes)
    spec.verify_block_body_operation_limits(body)
    spec.process_operations(state.copy(), body)

    body.head_votes.append(signed_vote(spec, state, 1, count=1))
    body.proof = prove_head_votes(spec, state, body.head_votes)
    with pytest.raises(spec.GossipReject, match="too many head vote credentials"):
        spec.verify_block_body_operation_limits(body)
    with pytest.raises(AssertionError):
        spec.process_operations(state.copy(), body)


def test_block_proof_covers_aggregates_not_declarations(spec, state):
    # A signed aggregate of an earlier slot counts for payments only through the
    # block's proof; the declarations of the previous slot carry no signature
    # and add no statement to it
    body = spec.BeaconBlockBody()
    vote = signed_vote(spec, state, 1, count=1)
    body.head_votes.append(vote)
    body.head_vote_declarations.append(
        spec.HeadVoteDeclaration(validator_index=1234, beacon_block_root=spec.Root(b"\x01" * 32))
    )
    body.head_vote_support_bits = spec.HeadVoteSupportBits(data=[True])
    body.proof = prove_head_votes(spec, state, body.head_votes)
    spec.process_operations(state.copy(), body)

    # Keep the nonempty proof but change the aggregate's signing identity.
    other = next(islice(elected_messages(spec, state, vote.data), 1, None))
    body.head_votes[0] = spec.get_aggregate_head_vote(state, [other])
    with pytest.raises(AssertionError):
        spec.process_operations(state.copy(), body)
    body.proof = prove_head_votes(spec, state, body.head_votes)
    spec.process_operations(state, body)
