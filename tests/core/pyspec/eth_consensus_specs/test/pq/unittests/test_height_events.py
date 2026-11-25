"""Justification, finalization and pending finality retention in ``process_height_events``."""

from importlib import import_module

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.block import build_empty_block
from eth_consensus_specs.test.helpers.constants import EIP8483, PREVIOUS_FORK_OF
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.pq.fork import upgrade_registered_to_pq
from eth_consensus_specs.test.helpers.state import state_transition_and_sign_block

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
    state = state_at(spec, 3, 2, 1, slot_offset=spec.TIMEOUT_DELAY_SLOTS + 1)
    # The current dynasty's block was finalized before the timeout opened a height.
    state.dynasty_start_slot = spec.Slot(1)
    state.finalized_slot = spec.Slot(1)
    spec.process_height_events(state)
    assert state.justified_checkpoint == checkpoint(spec, 2, 2)
    assert [p.checkpoint for p in state.pending_finality] == [checkpoint(spec, 2, 2)]
    assert state.target_checkpoint.height == 4
    assert state.dynasty == 1
    assert state.dynasty_start_slot == state.slot


def test_predecessor_finalized_in_the_same_event_opens_the_gate(spec):
    # Height 2 is justified and not finalized when the event starts; its
    # finality quorum, the target quorum of height 3 and the timeout all hold
    state = state_at(spec, 3, 2, 1, slot_offset=spec.TIMEOUT_DELAY_SLOTS)
    state.pending_finality[0].participation = spec.HeightParticipation(
        data=[spec.Boolean(value=True)] * len(state.validators)
    )
    spec.process_height_events(state)
    # Finalizing 2 first lets 3 justify; with the finality of the block entry
    # the quorum would be blocked and the height would only time out
    assert state.finalized_checkpoint == checkpoint(spec, 2, 2)
    assert state.justified_checkpoint == checkpoint(spec, 3, 3)
    assert [p.checkpoint for p in state.pending_finality] == [checkpoint(spec, 3, 3)]
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
    assert state.dynasty == 0
    assert [int(item.checkpoint.height) for item in state.pending_finality] == [5]

    state.target_checkpoint = spec.HeightCheckpoint(height=7, root=spec.Root(b"\x07" * 32))
    state.target_participation[0] = spec.Boolean(value=True)
    spec.process_height_events(state)
    assert [int(item.checkpoint.height) for item in state.pending_finality] == [5, 7]
    assert state.finalized_checkpoint.height == 3


def full_attestation(spec, state, data):
    """An aggregate of every attestation committee member for ``data``."""
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
    )


def test_one_block_finalizes_predecessor_and_justifies_height(spec, monkeypatch):
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=spec.Epoch(0)))
    monkeypatch.setitem(PREVIOUS_FORK_OF, spec.fork, EIP8483)
    monkeypatch.setattr(spec.stark, "VerifyAggregates", lambda statements, proof: True)
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    pre = create_genesis_state(
        eip8483, [eip8483.MAX_EFFECTIVE_BALANCE] * 64, eip8483.MAX_EFFECTIVE_BALANCE
    )
    state = upgrade_registered_to_pq(spec, pre)
    record = spec.FinalitySigningRecord(
        targets={}, timeouts={}, finality_locks={}, entries={}, rounds=set()
    )

    def apply_block_with_client_votes(slot, entry_state):
        spec.process_slots(state, spec.Slot(slot))
        data = spec.get_finality_attestation_data(record, state.target_checkpoint, entry_state)
        block = build_empty_block(spec, state, spec.Slot(slot))
        block.body.attestations.append(full_attestation(spec, state, data))
        spec.process_block(state, block)
        return data

    # Height 1 justifies; its block is the target of height 2
    data = apply_block_with_client_votes(1, state.copy())
    assert data.finality == spec.HeightCheckpoint.empty()
    assert state.justified_checkpoint.height == 1
    assert state.finalized_checkpoint.height == 0
    assert state.dynasty == 0
    entry_state = state.copy()

    # The votes for height 2 carry the justified predecessor as finality pair;
    # the block that includes them finalizes 1 and justifies 2 at once
    data = apply_block_with_client_votes(2, entry_state)
    assert data.finality == entry_state.justified_checkpoint
    assert state.finalized_checkpoint == entry_state.justified_checkpoint
    assert state.justified_checkpoint == data.target
    assert state.target_checkpoint.height == 3
    assert state.dynasty == 1
    assert state.dynasty_start_slot == 2
    assert state.ac_snapshots[2].weights == state.ac_snapshots[0].weights

    # Height 2's target predates dynasty 1, so its finalization does not advance it.
    apply_block_with_client_votes(3, state.copy())
    assert state.finalized_checkpoint.height == 2
    assert state.dynasty == 1

    apply_block_with_client_votes(4, state.copy())
    assert state.finalized_checkpoint.height == 3
    assert state.dynasty == 2
    assert state.previous_dynasty_start_slot == 2
    assert state.dynasty_start_slot == 4


def run_heights(spec, monkeypatch, withheld, delay, keep_previous):
    """
    Run 68 minimal slots of real blocks in which every validator votes in its
    duty slot with the FG client, the first ``withheld`` validators sign no
    finality pair, and votes reach the pool ``delay`` slots after they are
    cast. Proposers include every pooled vote the state accepts; with
    ``keep_previous`` the pool also keeps votes for the previous target.
    Return the height, justified height and finalized height at the end.
    """
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=spec.Epoch(0)))
    monkeypatch.setitem(PREVIOUS_FORK_OF, spec.fork, EIP8483)
    monkeypatch.setattr(spec.stark, "VerifyAggregates", lambda statements, proof: True)
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    pre = create_genesis_state(
        eip8483, [eip8483.MAX_EFFECTIVE_BALANCE] * 64, eip8483.MAX_EFFECTIVE_BALANCE
    )
    state = upgrade_registered_to_pq(spec, pre)
    count = len(state.validators)
    # The post-state of each block, keyed by block root; the upgraded genesis
    # state is the entry state of height 1
    entry_states = {state.target_checkpoint.root: state.copy()}
    records = {
        v: spec.FinalitySigningRecord(
            targets={}, timeouts={}, finality_locks={}, entries={}, rounds=set()
        )
        for v in range(count)
    }
    pool = []
    in_flight = []
    for slot in range(1, 69):
        # Include the pooled votes that the block's state accepts
        pre_state = state.copy()
        spec.process_slots(pre_state, spec.Slot(slot))
        block = build_empty_block(spec, state, spec.Slot(slot))
        groups = {}
        for attestation in pool:
            if spec.is_valid_attestation_data(pre_state, attestation.data):
                groups.setdefault(
                    (spec.hash_tree_root(attestation.data), attestation.round), []
                ).append(attestation)
        for group in groups.values():
            block.body.attestations.append(spec.get_aggregate_attestation(pre_state, group))
        signed = state_transition_and_sign_block(spec, state, block)
        root = signed.message.hash_tree_root()
        entry_states[root] = state.copy()

        # Validators with a duty in this slot vote from the new block
        target = state.target_checkpoint.copy()
        if target.root == spec.Root():
            target.root = root
        entry = entry_states[target.root]
        current_round = spec.compute_round_at_slot(spec.Slot(slot))
        new = []
        for v in range(count):
            index = spec.CommitteeIndex(v % spec.ATTESTATION_COMMITTEES_PER_ROUND)
            if spec.compute_attestation_committee_slot(current_round, index) != slot:
                continue
            data = spec.get_finality_attestation_data(records[v], target, entry)
            if data is None:
                continue
            if v < withheld:
                data.finality = spec.HeightCheckpoint.empty()
            spec.record_finality_attestation(records[v], data, current_round)
            new.append(
                spec.SingleAttestation(
                    committee_index=index, attester_index=v, data=data, round=current_round
                )
            )
        in_flight.append((slot + delay, new))
        arrived = [a for due, batch in in_flight if due <= slot for a in batch]
        in_flight = [(due, batch) for due, batch in in_flight if due > slot]
        lowest = state.target_checkpoint.height - (1 if keep_previous else 0)
        pool = [a for a in pool + arrived if a.data.target.height >= lowest]

    return (
        state.target_checkpoint.height,
        state.justified_checkpoint.height,
        state.finalized_checkpoint.height,
    )


@pytest.mark.parametrize(
    ("withheld", "delay", "keep_previous", "expected"),
    [
        # height, justified height, finalized height after 68 slots
        (0, 0, False, (23, 22, 21)),
        # A quarter of the validators sign no finality pair: the target quorum
        # waits for the finality quorum of its predecessor at each height
        (16, 0, False, (18, 17, 16)),
        # Votes arrive one slot late: the last finality votes of a height
        # land after it is justified, and count only as votes for the
        # previous target
        (16, 1, False, (17, 15, 0)),
        (16, 1, True, (17, 15, 15)),
    ],
)
def test_gate_and_client_finalize_over_many_heights(
    spec, monkeypatch, withheld, delay, keep_previous, expected
):
    if spec.config.PRESET_BASE != "minimal":
        pytest.skip("the expected heights are for the minimal schedule")
    assert run_heights(spec, monkeypatch, withheld, delay, keep_previous) == expected
