"""Generate and validate standard ``process_pending_deposits`` cases."""

from __future__ import annotations

from tests.generators.compliance_runners.state_transition.pending_deposits.coverage import (
    materialize_profile,
)
from tests.generators.compliance_runners.state_transition.pending_deposits.validation import (
    main as validate,
)


def main() -> int:
    materialize_profile("standard")
    print()
    return validate()


if __name__ == "__main__":
    raise SystemExit(main())
