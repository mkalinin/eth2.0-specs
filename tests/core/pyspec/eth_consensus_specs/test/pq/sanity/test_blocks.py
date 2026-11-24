from eth_consensus_specs.test.context import spec_state_test, with_phases
from eth_consensus_specs.test.helpers.block import build_empty_block_for_next_slot
from eth_consensus_specs.test.helpers.constants import PQ
from eth_consensus_specs.test.helpers.state import state_transition_and_sign_block


def get_full_attestation(spec, state, data, round):
    """
    An aggregate of every attestation committee member for ``data``, signed in
    ``round``.
    """
    epoch = spec.get_attestation_epoch(state, data)
    committee_bits = spec.AttestationCommitteeBits()
    size = 0
    for index in range(spec.ATTESTATION_COMMITTEES_PER_ROUND):
        members = len(spec.get_attestation_committee(state, epoch, spec.CommitteeIndex(index)))
        if members > 0:
            committee_bits[index] = True
            size += members
    return spec.Attestation(
        aggregation_bits=spec.AggregationBits(data=[True] * size),
        data=data,
        committee_bits=committee_bits,
        round=round,
    )


@with_phases([PQ])
@spec_state_test
def test_empty_block_transition(spec, state):
    pre_slot = state.slot
    pre_height = state.target_checkpoint.height

    yield "pre", state

    block = build_empty_block_for_next_slot(spec, state)
    signed_block = state_transition_and_sign_block(spec, state, block)

    yield "blocks", [signed_block]
    yield "post", state

    assert state.slot == pre_slot + 1
    # Without attestations the height does not move, and the genesis block
    # is filled in as the target of height 1
    assert state.target_checkpoint.height == pre_height
    assert state.target_checkpoint.root == block.parent_root
    assert state.justified_checkpoint.height == 0


@with_phases([PQ])
@spec_state_test
def test_full_target_vote_justifies_height(spec, state):
    yield "pre", state

    block = build_empty_block_for_next_slot(spec, state)
    block_state = state.copy()
    spec.process_slots(block_state, block.slot)
    target = block_state.target_checkpoint.copy()
    data = spec.AttestationData(target=target, timeout=False, finality=spec.HeightCheckpoint())
    round = spec.compute_round_at_slot(block.slot)
    block.body.attestations.append(get_full_attestation(spec, block_state, data, round))
    signed_block = state_transition_and_sign_block(spec, state, block)

    yield "blocks", [signed_block]
    yield "post", state

    # Every active validator voted for the target, so the block justifies it
    # and opens the next height, with the block as its target
    assert state.justified_checkpoint == target
    assert [pending.checkpoint for pending in state.pending_finality] == [target]
    assert state.target_checkpoint.height == target.height + 1
    assert state.target_slot == block.slot
    assert state.previous_target_checkpoint == target
    # Progress starts afresh at the new height
    assert not any(state.progress_participation)
    for index in range(len(state.validators)):
        assert spec.has_flag(state.round_participation[index], spec.PROGRESS_FLAG_INDEX)
