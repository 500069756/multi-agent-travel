"""Phase 5 demo — full chain (Phase 0 → 2 → 3 → 4) then Review & Validation."""
from common import load_environment

load_environment()

import asyncio
import sys

import groq

from phase0 import intake
from phase2 import fan_out
from phase3 import reconcile_budget
from phase4 import synthesize
from phase5 import review


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


async def run(request_text: str) -> None:
    print(f"Input: {request_text}\n")

    # intake is sync
    trip = intake(request_text)
    print(f"Phase 0: TripRequest — {trip.duration_days} days, "
          f"{', '.join(trip.cities)}, ${trip.budget_usd:,.0f}\n")

    client = groq.AsyncGroq()

    research, logistics = await fan_out(trip, client)
    print(f"Phase 2: {len(research.pois)} POIs, "
          f"{len(logistics.city_allocations)} city allocations\n")

    budget_result = await reconcile_budget(trip, research, logistics, client=client)
    print(f"Phase 3: converged={budget_result.converged}, "
          f"final ${budget_result.final_breakdown.total_estimated_usd:,.0f}\n")

    itinerary = await synthesize(
        trip,
        budget_result.final_research,
        budget_result.final_logistics,
        budget_result.final_breakdown,
        client=client,
    )
    print(f"Phase 4: DraftItinerary with {len(itinerary.days)} days, "
          f"total ${itinerary.total_estimated_cost_usd:,.0f}\n")

    result = await review(trip, itinerary, client=client)

    print("=== ReviewResult (Phase 5) ===")
    print(f"Overall: {result.overall}")
    if result.revision_target:
        print(f"Revision target: {result.revision_target}")
    print()

    print("--- Checks ---")
    for c in result.checks:
        status = "PASS" if c.passed else "FAIL"
        print(f"  [{status}] ({c.severity}) {c.name}: {c.reason}")
    print()

    if result.failures:
        print("--- Failures ---")
        for f in result.failures:
            print(f"  • {f}")
        print()

    if result.suggestions:
        print("--- Suggestions ---")
        for s in result.suggestions:
            print(f"  • {s}")


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    asyncio.run(run(request_text))


if __name__ == "__main__":
    main()
