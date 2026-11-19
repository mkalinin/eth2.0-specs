"""Persistent FG signing records and repeated attestation selection."""

from importlib import import_module

import pytest

from eth_consensus_specs.test import context

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.fixture
def spec(preset):
    return import_module(f"eth_consensus_specs.pq.{context.DEFAULT_TEST_PRESET}")


@pytest.fixture
def record(spec):
    return spec.FinalitySigningRecord(
        targets={}, timeouts={}, finality_locks={}, entries={}, rounds=set()
    )


def checkpoint(spec, height, root_byte):
    return spec.HeightCheckpoint(height=height, root=spec.Root(bytes([root_byte]) * 32))


@pytest.mark.parametrize("justify_target", [False, True])
def test_repeated_target_suppresses_duplicate(spec, record, justify_target):
    target = checkpoint(spec, 1, 1)
    empty = spec.HeightCheckpoint.empty()
    finalized_height = spec.Height(0)
    data = spec.get_finality_attestation_data(record, target, empty, finalized_height)
    assert data is not None
    assert data.target == target
    assert not data.timeout
    assert data.finality == empty
    spec.record_finality_attestation(record, data, spec.Round(len(record.rounds)))

    assert record.targets == {target.height: target.root}
    assert record.entries == {target.height: {target.root}}
    assert record.timeouts == {}
    assert record.finality_locks == {}
    justified = target if justify_target else empty
    assert spec.get_finality_attestation_data(record, target, justified, finalized_height) is None


def test_distinct_targets_timeout_and_suppress_finality(spec, record):
    first = checkpoint(spec, 1, 1)
    second = checkpoint(spec, 1, 2)
    third = checkpoint(spec, 1, 3)
    empty = spec.HeightCheckpoint.empty()
    finalized_height = spec.Height(0)
    data = spec.get_finality_attestation_data(record, first, empty, finalized_height)
    assert data is not None
    spec.record_finality_attestation(record, data, spec.Round(len(record.rounds)))

    assert spec.get_finality_vote(record, first, finalized_height) == first
    assert spec.get_finality_vote(record, second, finalized_height) == empty
    data = spec.get_finality_attestation_data(record, second, second, finalized_height)
    assert data is not None
    assert data.target == second
    assert data.timeout
    assert data.finality == empty
    spec.record_finality_attestation(record, data, spec.Round(len(record.rounds)))

    assert record.targets == {first.height: first.root}
    assert record.timeouts == {first.height: {second.root}}
    assert record.entries == {first.height: {first.root, second.root}}
    assert spec.get_finality_vote(record, first, finalized_height) == empty
    assert spec.get_finality_vote(record, second, finalized_height) == empty
    assert spec.get_height_vote(record, first, empty) == (first, True)
    for target in (first, second):
        assert spec.get_finality_attestation_data(record, target, empty, finalized_height) is None

    data = spec.get_finality_attestation_data(record, third, empty, finalized_height)
    assert data is not None
    assert data.target == third
    assert data.timeout
    spec.record_finality_attestation(record, data, spec.Round(len(record.rounds)))
    assert record.timeouts == {first.height: {second.root, third.root}}


def test_finality_lock_allows_same_root_and_rejects_distinct_root(spec, record):
    locked = checkpoint(spec, 1, 1)
    conflicting = checkpoint(spec, 1, 2)
    target = checkpoint(spec, 2, 3)
    empty = spec.HeightCheckpoint.empty()
    finalized_height = spec.Height(0)
    data = spec.get_finality_attestation_data(record, target, locked, finalized_height)
    assert data is not None
    assert data.finality == locked
    spec.record_finality_attestation(record, data, spec.Round(len(record.rounds)))
    assert record.finality_locks == {locked.height: locked.root}

    assert spec.get_finality_vote(record, locked, finalized_height) == locked
    assert spec.get_finality_vote(record, conflicting, finalized_height) == empty
    next_target = checkpoint(spec, 3, 4)
    data = spec.get_finality_attestation_data(record, next_target, locked, finalized_height)
    assert data is not None
    assert data.finality == locked
    data = spec.get_finality_attestation_data(record, next_target, conflicting, finalized_height)
    assert data is not None
    assert data.finality == empty

    assert spec.get_finality_attestation_data(record, conflicting, empty, finalized_height) is None
    data = spec.get_finality_attestation_data(record, locked, empty, finalized_height)
    assert data is not None
    assert data.target == locked
    assert not data.timeout
    spec.record_finality_attestation(record, data, spec.Round(len(record.rounds)))
    assert spec.get_finality_attestation_data(record, locked, locked, finalized_height) is None


def test_candidate_finality_constrains_height_vote_before_removal(spec, record):
    target = checkpoint(spec, 1, 1)
    conflicting = checkpoint(spec, 1, 2)
    finalized_height = spec.Height(0)
    assert spec.get_finality_attestation_data(record, target, conflicting, finalized_height) is None
    data = spec.get_finality_attestation_data(record, target, target, finalized_height)
    assert data is not None
    assert data.target == target
    assert not data.timeout
    assert data.finality == spec.HeightCheckpoint.empty()
    spec.record_finality_attestation(record, data, spec.Round(len(record.rounds)))
    assert record.finality_locks == {}


def test_second_attestation_in_a_round_is_refused(spec, record):
    # An attestation is signed at the XMSS leaf of its round
    data = spec.AttestationData(
        target=spec.HeightCheckpoint(height=1, root=spec.Root(b"\x01" * 32)),
        timeout=False,
        finality=spec.HeightCheckpoint(),
    )
    spec.record_finality_attestation(record, data, spec.Round(3))
    other = data.copy()
    other.target = spec.HeightCheckpoint(height=2, root=spec.Root(b"\x02" * 32))
    with pytest.raises(AssertionError):
        spec.record_finality_attestation(record, other, spec.Round(3))
    spec.record_finality_attestation(record, other, spec.Round(4))
    assert record.rounds == {spec.Round(3), spec.Round(4)}
