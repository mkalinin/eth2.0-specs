"""Inclusion of attestations for the previous target."""

from importlib import import_module

import pytest

from eth_consensus_specs.test import context
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.pq.fork import upgrade_registered_to_pq

from .test_height_events import full_attestation

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.fixture
def spec(preset, monkeypatch):
    spec = import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")
    monkeypatch.setattr(spec, "config", spec.config._replace(PQ_FORK_EPOCH=spec.Epoch(0)))
    monkeypatch.setattr(spec.stark, "VerifyAggregates", lambda statements, proof: True)
    return spec


def checkpoint(spec, height, root_byte):
    return spec.HeightCheckpoint(height=height, root=spec.Root(bytes([root_byte]) * 32))


@pytest.fixture
def state(spec):
    """
    A state at height 3 whose previous target is height 2, in the epoch after
    it, with height 1 justified and pending.
    """
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    pre = create_genesis_state(
        eip8483, [eip8483.MAX_EFFECTIVE_BALANCE] * 64, eip8483.MAX_EFFECTIVE_BALANCE
    )
    state = upgrade_registered_to_pq(spec, pre)
    spec.process_slots(state, spec.Slot(spec.SLOTS_PER_EPOCH + 1))
    count = len(state.validators)
    no = spec.Boolean(value=False)
    state.previous_target_checkpoint = checkpoint(spec, 2, 2)
    state.previous_target_slot = spec.Slot(1)
    state.target_checkpoint = checkpoint(spec, 3, 3)
    state.target_slot = spec.Slot(spec.SLOTS_PER_EPOCH)
    state.justified_checkpoint = checkpoint(spec, 1, 1)
    state.pending_finality = spec.PendingFinalities(
        data=[
            spec.PendingFinality(
                checkpoint=checkpoint(spec, 1, 1),
                participation=spec.HeightParticipation(data=[no] * count),
            )
        ]
    )
    return state


def test_upgrade_has_no_previous_target(spec):
    eip8483 = import_module(f"eth_consensus_specs.eip8483.{context.DEFAULT_TEST_PRESET}")
    pre = create_genesis_state(
        eip8483, [eip8483.MAX_EFFECTIVE_BALANCE] * 64, eip8483.MAX_EFFECTIVE_BALANCE
    )
    state = upgrade_registered_to_pq(spec, pre)
    assert state.previous_target_checkpoint == spec.HeightCheckpoint()
    # A row naming the empty previous target is not includable
    data = spec.AttestationData(target=spec.HeightCheckpoint())
    assert not spec.is_previous_target_attestation_data(state, data)


def test_advance_height_keeps_the_previous_target(spec, state):
    target, target_slot = state.target_checkpoint.copy(), state.target_slot
    spec.advance_height(state)
    assert state.previous_target_checkpoint == target
    assert state.previous_target_slot == target_slot
    assert state.target_checkpoint.height == 4


def test_previous_target_counts_only_for_pending_finality(spec, state):
    data = spec.AttestationData(
        target=state.previous_target_checkpoint, timeout=False, finality=checkpoint(spec, 1, 1)
    )
    before = state.copy()
    spec.process_attestation(state, full_attestation(spec, state, data))
    signers = spec.get_attesting_indices(state, full_attestation(spec, state, data))
    assert len(signers) > 0
    assert all(state.pending_finality[0].participation[i] for i in signers)
    # No progress, target, flag or balance change
    assert state.progress_participation == before.progress_participation
    assert state.target_participation == before.target_participation
    assert state.round_participation == before.round_participation
    assert state.balances == before.balances


def test_current_target_still_credits_flags(spec, state):
    data = spec.AttestationData(
        target=state.target_checkpoint, timeout=False, finality=checkpoint(spec, 1, 1)
    )
    before = state.copy()
    spec.process_attestation(state, full_attestation(spec, state, data))
    assert state.round_participation != before.round_participation
    assert state.target_participation != before.target_participation


def test_target_two_heights_back_is_not_included(spec, state):
    data = spec.AttestationData(target=checkpoint(spec, 1, 1), timeout=False)
    assert not spec.is_valid_attestation_data(state, data)
    with pytest.raises(AssertionError):
        spec.process_attestation(state, full_attestation(spec, state, data))


def test_previous_target_uses_its_epoch_committees(spec, state):
    # A validator that became eligible in the current epoch is in the
    # committees of the current target's epoch, not of the previous target's
    late = len(state.validators) - 1
    state.validators[late].activation_eligibility_epoch = spec.Epoch(1)
    previous = spec.AttestationData(target=state.previous_target_checkpoint)
    current = spec.AttestationData(target=state.target_checkpoint)
    assert spec.get_attestation_epoch(state, previous) == 0
    assert spec.get_attestation_epoch(state, current) == 1
    index = spec.CommitteeIndex(late % spec.ATTESTATION_COMMITTEES_PER_ROUND)
    assert late not in spec.get_attestation_committee(state, spec.Epoch(0), index)
    assert late in spec.get_attestation_committee(state, spec.Epoch(1), index)
    signers = spec.get_attesting_indices(state, full_attestation(spec, state, previous))
    assert late not in signers
