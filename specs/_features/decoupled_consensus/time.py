from time import time

from .preset import GENESIS_SLOT, SECONDS_PER_SLOT
from .type import Millis, Slot


def get_current_time() -> Millis:
    return Millis(time() * 1000)


def get_current_slot(time: Millis, genesis_time: Millis) -> Slot:
    return (time - genesis_time) // 1000 // SECONDS_PER_SLOT


def get_previous_slot(time: Millis, genesis_time: Millis) -> Slot:
    current_slot = get_current_slot(time, genesis_time)
    if current_slot > GENESIS_SLOT:
        return current_slot - 1
    else:
        return GENESIS_SLOT


def get_slot_start_time(slot: Slot, genesis_time: Millis) -> Millis:
    return genesis_time + slot * SECONDS_PER_SLOT * 1000
