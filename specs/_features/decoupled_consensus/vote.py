from dataclasses import dataclass

from .type import Root, Round, Slot, ValidatorIndex


@dataclass
class AvailableChainVote:
    slot: Slot
    root: Root
    validator_index: ValidatorIndex


@dataclass
class StabilizationVote:
    round: Round
    root: Root
    validator_index: ValidatorIndex
