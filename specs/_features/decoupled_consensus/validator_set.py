from dataclasses import dataclass

from .type import Gwei, ValidatorIndex


@dataclass
class ValidatorSet:
    validator_indices: set[ValidatorIndex]
    balances: dict[ValidatorIndex, Gwei]

    def is_active_validator(self, index: ValidatorIndex) -> bool:
        # Stub
        return index in self.validator_indices

    def get_active_validators(self) -> set[ValidatorIndex]:
        return {v for v in self.validator_indices if self.is_active_validator(v)}

    def get_balance(self, index: ValidatorIndex) -> Gwei:
        return self.balances[index]
