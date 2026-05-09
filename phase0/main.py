"""Phase 0 demo — parse a natural-language travel request into a TripRequest."""
from common import load_environment

load_environment()

import sys

from phase0 import intake


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    print(f"Input: {request_text}\n")

    trip = intake(request_text)
    print(trip.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
