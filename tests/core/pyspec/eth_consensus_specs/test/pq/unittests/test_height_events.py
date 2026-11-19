"""Justification, finalization and pending finality retention in ``process_height_events``."""

from importlib import import_module

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.pq.fork import upgrade_registered_to_pq

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.fixture
def spec(preset):
    return import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")


def checkpoint(spec, height, root_byte):
    return spec.HeightCheckpoint(height=height, root=spec.Root(bytes([root_byte]) * 32))


def state_at(spec, height, justified_height, finalized_height, slot_offset=0):
    """
    A state at ``height`` whose current target has a quorum of target votes.
    """
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    pre = create_genesis_state(
        eip8483, [eip8483.MAX_EFFECTIVE_BALANCE] * 64, eip8483.MAX_EFFECTIVE_BALANCE
    )
    state = upgrade_registered_to_pq(spec, pre)
    count = len(state.validators)
    no, yes = spec.Boolean(False), spec.Boolean(True)  # noqa: FBT003
    state.target_checkpoint = checkpoint(spec, height, height)
    state.target_slot = state.slot
    state.slot += slot_offset
    state.justified_checkpoint = checkpoint(spec, justified_height, justified_height)
    state.finalized_checkpoint = checkpoint(spec, finalized_height, finalized_height)
    state.pending_finality = spec.PendingFinalities(
        data=[
            spec.PendingFinality(
                checkpoint=checkpoint(spec, h, h),
                participation=spec.HeightParticipation(data=[no] * count),
            )
            for h in range(finalized_height + 1, justified_height + 1)
        ]
    )
    state.target_participation = spec.HeightParticipation(data=[yes] * count)
    state.progress_participation = spec.HeightParticipation(data=[yes] * count)
    return state


@pytest.mark.parametrize(
    ("justified_height", "finalized_height", "justifies"),
    [
        # The previous height is justified and not finalized
        (2, 1, False),
        # The previous height is justified and finalized
        (2, 2, True),
        # The previous height is not justified
        (1, 1, True),
        (1, 0, True),
        # Height 0 does not count as a justified previous height
        (0, 0, True),
    ],
)
def test_target_quorum_waits_for_justified_predecessor(
    spec, justified_height, finalized_height, justifies
):
    state = state_at(spec, 3, justified_height, finalized_height)
    spec.process_height_events(state)
    if justifies:
        assert state.justified_checkpoint == checkpoint(spec, 3, 3)
        assert state.pending_finality[-1].checkpoint == checkpoint(spec, 3, 3)
        assert state.target_checkpoint.height == 4
    else:
        # Before the timeout delay the height does not move
        assert state.justified_checkpoint == checkpoint(spec, 2, 2)
        assert state.target_checkpoint == checkpoint(spec, 3, 3)


def test_blocked_quorum_falls_through_to_timeout(spec):
    state = state_at(spec, 3, 2, 1, slot_offset=spec.TIMEOUT_DELAY_SLOTS)
    spec.process_height_events(state)
    assert state.justified_checkpoint == checkpoint(spec, 2, 2)
    assert [p.checkpoint for p in state.pending_finality] == [checkpoint(spec, 2, 2)]
    assert state.target_checkpoint.height == 4


def test_pending_finality_retains_two_newest_justifications(spec):
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

    # Each justified height follows a height that timed out, so the gate lets
    # it justify while the older justifications are not finalized
    for height, retained in [(1, [1]), (3, [1, 3]), (5, [3, 5])]:
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
    assert state.finalized_checkpoint.height == 3
    assert state.finalized_slot == 3
    assert [int(item.checkpoint.height) for item in state.pending_finality] == [5]

    state.target_checkpoint = spec.HeightCheckpoint(height=7, root=spec.Root(b"\x07" * 32))
    state.target_participation[0] = spec.Boolean(value=True)
    spec.process_height_events(state)
    assert [int(item.checkpoint.height) for item in state.pending_finality] == [5, 7]
    assert state.finalized_checkpoint.height == 3
