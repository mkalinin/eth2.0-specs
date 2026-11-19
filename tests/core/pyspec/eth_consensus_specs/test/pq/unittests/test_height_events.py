"""Pending finality retention across justification and finalization."""

from importlib import import_module

from eth_consensus_specs.test import context


def test_pending_finality_retains_two_newest_justifications(preset):
    spec = import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")
    state = spec.BeaconState()
    state.validators.append(
        spec.Validator(
            effective_balance=spec.MAX_EFFECTIVE_BALANCE, exit_epoch=spec.FAR_FUTURE_EPOCH
        )
    )
    state.inactivity_scores.append(0)
    state.progress_participation = spec.HeightParticipation(data=[spec.Boolean(value=False)])
    assert spec.PENDING_FINALITY_WINDOW == 2
    assert spec.PendingFinalities.LIMIT == 2

    for height, retained in [(1, [1]), (2, [1, 2]), (3, [2, 3])]:
        state.target_checkpoint = spec.HeightCheckpoint(
            height=height, root=spec.Root(bytes([height]) * 32)
        )
        state.target_slot = spec.Slot(height)
        state.target_participation = spec.HeightParticipation(data=[spec.Boolean(value=True)])
        spec.process_height_events(state)
        assert [int(item.checkpoint.height) for item in state.pending_finality] == retained
        assert state.justified_checkpoint.height == height
        assert state.target_checkpoint.height == height + 1
        assert state.finalized_checkpoint.height == 0

    # Finalizing the oldest retained entry frees a slot without dropping the newer one.
    state.pending_finality[0].participation[0] = spec.Boolean(value=True)
    spec.process_height_events(state)
    assert state.finalized_checkpoint.height == 2
    assert state.finalized_slot == 2
    assert [int(item.checkpoint.height) for item in state.pending_finality] == [3]

    state.target_checkpoint.root = spec.Root(b"\x04" * 32)
    state.target_participation[0] = spec.Boolean(value=True)
    spec.process_height_events(state)
    assert [int(item.checkpoint.height) for item in state.pending_finality] == [3, 4]
    assert state.finalized_checkpoint.height == 2
