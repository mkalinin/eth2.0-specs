"""Generate and validate standard Gloas parent-execution-payload cases."""

from tests.generators.compliance_runners.state_transition.parent_execution_payload.coverage import (
    materialize_profile,
)
from tests.generators.compliance_runners.state_transition.parent_execution_payload.validation import (
    main as validate,
)


def main() -> int:
    materialize_profile("standard")
    print()
    return validate()


if __name__ == "__main__":
    raise SystemExit(main())
