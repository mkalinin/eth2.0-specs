"""Generate and validate standard Gloas proposer-slashing cases."""

from tests.generators.compliance_runners.state_transition.proposer_slashing.coverage import (
    materialize_profile,
)
from tests.generators.compliance_runners.state_transition.proposer_slashing.validation import (
    main as validate,
)


def main() -> int:
    materialize_profile("standard")
    print()
    return validate()


if __name__ == "__main__":
    raise SystemExit(main())
