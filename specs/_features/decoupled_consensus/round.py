from .preset import SLOTS_PER_ROUND
from .time import get_current_slot
from .type import Millis, Round, Slot

EMPTY_ROUND = Round(2**64 - 1)


def compute_round_at_slot(slot: Slot) -> Round:
    return slot // SLOTS_PER_ROUND


def get_current_round(time: Millis, genesis_time: Millis) -> Round:
    return compute_round_at_slot(get_current_slot(time, genesis_time))
