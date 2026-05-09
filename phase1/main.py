"""Phase 1 demo — Phase 0 intake, then orchestrator builds the MasterPlan."""
from common import load_environment

load_environment()

import sys

from phase0 import intake
from phase1 import plan


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    print(f"Input: {request_text}\n")

    trip = intake(request_text)
    print("=== TripRequest (Phase 0) ===")
    print(trip.model_dump_json(indent=2))
    print()

    master = plan(trip)
    print("=== MasterPlan (Phase 1) ===")
    print(master.model_dump_json(indent=2))
    print()

    print("=== Execution order ===")
    for i, wave in enumerate(master.execution_order(), 1):
        print(f"Wave {i}: {' || '.join(wave)}")


if __name__ == "__main__":
    main()
