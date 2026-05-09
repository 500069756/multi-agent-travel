"""Phase 6 demo — full pipeline (Phase 0 → 5) ending in formatted user-facing markdown."""
from common import load_environment

load_environment()

import asyncio
import sys
from pathlib import Path

import groq

from phase0 import intake
from phase2 import fan_out
from phase3 import reconcile_budget
from phase4 import synthesize
from phase5 import review
from phase6 import deliver


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "trip_plan.md"


async def run(request_text: str) -> None:
    print(f"Input: {request_text}\n")

    # intake is sync
    trip = intake(request_text)
    print(f"[Phase 0] {trip.duration_days} days · {', '.join(trip.cities)} · "
          f"${trip.budget_usd:,.0f}")

    client = groq.AsyncGroq()

    research, logistics = await fan_out(trip, client)
    print(f"[Phase 2] {len(research.pois)} POIs · "
          f"{len(logistics.city_allocations)} city allocations")

    budget_result = await reconcile_budget(trip, research, logistics, client=client)
    print(f"[Phase 3] converged={budget_result.converged} · "
          f"${budget_result.final_breakdown.total_estimated_usd:,.0f}")

    itinerary = await synthesize(
        trip,
        budget_result.final_research,
        budget_result.final_logistics,
        budget_result.final_breakdown,
        client=client,
    )
    print(f"[Phase 4] {len(itinerary.days)}-day itinerary drafted")

    review_result = await review(trip, itinerary, client=client)
    print(f"[Phase 5] review: {review_result.overall}")

    document = deliver(
        trip,
        itinerary,
        budget_result.final_logistics,
        budget_result.final_breakdown,
        review_result,
    )

    OUTPUT_FILE.write_text(document, encoding="utf-8")
    print(f"[Phase 6] wrote {OUTPUT_FILE.name} ({len(document):,} chars)\n")
    print("=" * 72)
    print(document)


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    asyncio.run(run(request_text))


if __name__ == "__main__":
    main()
