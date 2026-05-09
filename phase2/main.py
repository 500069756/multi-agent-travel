"""Phase 2 demo — Phase 0 intake, then parallel Research + Logistics fan-out."""
from common import load_environment

load_environment()

import asyncio
import sys

from phase0 import intake
from phase2 import fan_out


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


async def run(request_text: str) -> None:
    print(f"Input: {request_text}\n")

    trip = intake(request_text)
    print("=== TripRequest (Phase 0) ===")
    print(trip.model_dump_json(indent=2))
    print()

    research, logistics = await fan_out(trip)

    print("=== ResearchOutput (Phase 2A) ===")
    print(research.model_dump_json(indent=2))
    print()

    print("=== LogisticsPlan (Phase 2B) ===")
    print(logistics.model_dump_json(indent=2))


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    asyncio.run(run(request_text))


if __name__ == "__main__":
    main()
