"""Assignment of attestation committees to the slots of a round."""

from importlib import import_module
from itertools import pairwise

import pytest

pytestmark = pytest.mark.usefixtures("fake_xmss")


@pytest.mark.parametrize("preset_name", ["minimal", "mainnet"])
def test_committee_slots_load_and_gaps(preset_name):
    spec = import_module(f"eth_consensus_specs.pq.{preset_name}")
    committees = int(spec.ATTESTATION_COMMITTEES_PER_ROUND)
    slots_per_round = int(spec.SLOTS_PER_ROUND)
    per_slot = committees // slots_per_round
    subnets = min(per_slot, int(spec.config.ATTESTATION_SUBNET_COUNT_PQ))
    rounds = 4 * slots_per_round
    duties = {index: [] for index in range(committees)}
    for round in range(rounds):
        start = int(spec.compute_start_slot_at_round(spec.Round(round)))
        by_slot = {}
        for index in range(committees):
            slot = int(
                spec.compute_attestation_committee_slot(
                    spec.Round(round), spec.CommitteeIndex(index)
                )
            )
            assert start <= slot < start + slots_per_round
            by_slot.setdefault(slot, []).append(index)
            duties[index].append(slot)
        # Every slot carries the same number of committees and every subnet
        assert sorted(by_slot) == list(range(start, start + slots_per_round))
        for members in by_slot.values():
            assert len(members) == per_slot
            assert (
                len(
                    {
                        int(spec.compute_subnet_for_attestation(spec.CommitteeIndex(i)))
                        for i in members
                    }
                )
                == subnets
            )
    gaps = set()
    for slots in duties.values():
        # Every committee votes in every slot of a round
        assert {slot % slots_per_round for slot in slots} == set(range(slots_per_round))
        gaps.update(b - a for a, b in pairwise(slots))
    assert min(gaps) == slots_per_round - 1
    assert max(gaps) == slots_per_round + 1
