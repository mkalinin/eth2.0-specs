"""Generate and validate standard Gloas payload-attestation cases."""

from tests.generators.compliance_runners.state_transition.payload_attestation.coverage import (
    materialize_profile,
)
from tests.generators.compliance_runners.state_transition.payload_attestation.validation import (
    main as validate,
)


def main() -> int:
    materialize_profile("standard")
    print()
    return validate()


if __name__ == "__main__":
    raise SystemExit(main())
