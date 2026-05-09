"""Phase 4 demo — Phase 0 → Phase 2 → Phase 3 → Phase 4 itinerary synthesis."""
from common import load_environment

load_environment()

import asyncio
import sys

import groq

from phase0 import intake
from phase2 import fan_out
from phase3 import reconcile_budget
from phase4 import synthesize


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


async def run(request_text: str) -> None:
    print(f"Input: {request_text}\n")

    # intake is sync
    trip = intake(request_text)
    print(f"=== TripRequest: {trip.duration_days} days in {', '.join(trip.cities)} "
          f"(${trip.budget_usd:,.0f}) ===\n")

    client = groq.AsyncGroq()

    research, logistics = await fan_out(trip, client)
    print(f"Phase 2: {len(research.pois)} POIs, "
          f"{len(logistics.city_allocations)} city allocations\n")

    budget_result = await reconcile_budget(trip, research, logistics, client=client)
    print(f"Phase 3: converged={budget_result.converged}, "
          f"final ${budget_result.final_breakdown.total_estimated_usd:,.0f} "
          f"vs ${budget_result.final_breakdown.budget_usd:,.0f}\n")

    itinerary = await synthesize(
        trip,
        budget_result.final_research,
        budget_result.final_logistics,
        budget_result.final_breakdown,
        client=client,
    )

    print("=== DraftItinerary (Phase 4) ===")
    print(f"Title: {itinerary.title}")
    print(f"Summary: {itinerary.summary}\n")

    for day in itinerary.days:
        print(f"--- Day {day.day_number} — {day.city} — {day.theme} ---")
        if day.transit_notes:
            print(f"  Transit: {day.transit_notes}")
        if day.morning:
            print(f"  Morning:   {' • '.join(day.morning)}")
        if day.afternoon:
            print(f"  Afternoon: {' • '.join(day.afternoon)}")
        if day.evening:
            print(f"  Evening:   {' • '.join(day.evening)}")
        if day.crowd_advisory:
            print(f"  Crowd tip: {day.crowd_advisory}")
        print(f"  Day cost:  ${day.estimated_cost_usd:,.0f}")
        print()

    print("Highlights:")
    for h in itinerary.highlights:
        print(f"  • {h}")
    print()

    print("Practical notes:")
    for n in itinerary.practical_notes:
        print(f"  • {n}")
    print()

    print(f"Total estimated cost: ${itinerary.total_estimated_cost_usd:,.0f}")


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    asyncio.run(run(request_text))


if __name__ == "__main__":
    main()
