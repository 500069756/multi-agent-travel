"""Phase 3 demo — Phase 0 intake, Phase 2 fan-out, then Phase 3 budget reconciliation."""
from common import load_environment

load_environment()

import asyncio
import sys

import groq

from phase0 import intake
from phase2 import fan_out
from phase3 import reconcile_budget


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


async def run(request_text: str) -> None:
    print(f"Input: {request_text}\n")

    # intake is sync
    trip = intake(request_text)
    print("=== TripRequest (Phase 0) ===")
    print(trip.model_dump_json(indent=2))
    print()

    client = groq.AsyncGroq()
    research, logistics = await fan_out(trip, client)
    print("=== Phase 2 fan-out complete ===")
    print(f"Research POIs: {len(research.pois)}")
    print(f"City allocations: {len(logistics.city_allocations)}")
    print(f"Transport legs: {len(logistics.transport_legs)}\n")

    result = await reconcile_budget(trip, research, logistics, client=client)

    print("=== BudgetResult (Phase 3) ===")
    print(f"Converged: {result.converged}")
    print(f"Revision rounds used: {result.iterations_used}")
    print(f"Final estimate: ${result.final_breakdown.total_estimated_usd:,.0f} "
          f"vs budget ${result.final_breakdown.budget_usd:,.0f}")
    print()

    print("--- Iteration history ---")
    for it in result.history:
        revisions_summary = (
            f"{len(it.revisions_emitted)} revision(s)"
            if it.revisions_emitted
            else "within budget"
        )
        print(f"  iter {it.iteration}: ${it.breakdown.total_estimated_usd:,.0f} "
              f"(over by ${it.breakdown.over_budget_by_usd:,.0f}) — {revisions_summary}")
    print()

    print("--- Final breakdown ---")
    print(result.final_breakdown.model_dump_json(indent=2))


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    asyncio.run(run(request_text))


if __name__ == "__main__":
    main()
