from tests.generators.compliance_runners.state_transition.builder_pending_payments.coverage import (
    materialize_profile,
)
from tests.generators.compliance_runners.state_transition.builder_pending_payments.validation import (
    main as validate,
)


def main():
    materialize_profile("standard")
    return validate()


if __name__ == "__main__":
    raise SystemExit(main())
