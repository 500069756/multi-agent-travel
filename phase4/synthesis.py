import json
from typing import Optional

import groq
from common.llm import acall_groq_structured

from phase0.schema import TripRequest
from phase2.schema import LogisticsPlan, ResearchOutput
from phase3.schema import BudgetBreakdown

from .schema import DraftItinerary


SYSTEM_PROMPT = """You are the Orchestrator Agent in synthesis mode.

You receive the original TripRequest, the Research Agent's POI list, the Logistics Agent's plan,
and the Budget Agent's reconciled breakdown. Produce a DraftItinerary that fuses them into a
coherent day-by-day plan.

Rules:
- The number of days must equal duration_days. Each day's city must match what city_allocations
  implies for that day, in the order the cities were listed.
- Inter-city travel days note the leg in transit_notes (e.g., "Morning Shinkansen Tokyo → Kyoto").
- Schedule every "must_do" POI somewhere across the trip. Add "nice_to_have" items where time allows
  without overcrowding.
- Group POIs by geographic proximity within a single day — do not bounce across town.
- For high-crowd POIs, recommend early-morning or late-afternoon timing in crowd_advisory if the
  traveler dislikes crowds.
- estimated_cost_usd per day should sum approximately to total_estimated_usd from the budget breakdown.
- title and summary should reflect the traveler's preferences (food, temples, etc.).
- highlights: 3-5 standout moments.
- practical_notes: 4-6 actionable tips (rail passes, reservation deadlines, payment methods,
  language tips, etc.).
- Use only POIs that appeared in the Research output. Do not invent venues.
- Return the output as a JSON object matching the DraftItinerary schema.
Example structure:
{
  "title": "Paris Art & Pastries",
  "summary": "A 3-day exploration of Parisian culture.",
  "days": [
    {"day_number": 1, "city": "Paris", "theme": "Art", "morning": ["Louvre"], "afternoon": ["Tuileries Garden"], "evening": ["Seine Cruise"], "estimated_cost_usd": 300.0}
  ],
  "total_estimated_cost_usd": 900.0,
  "highlights": ["Louvre"],
  "practical_notes": ["Metro pass."]
}
"""


def _build_user_message(
    trip: TripRequest,
    research: ResearchOutput,
    logistics: LogisticsPlan,
    budget: BudgetBreakdown,
) -> str:
    return json.dumps(
        {
            "trip_request": trip.model_dump(),
            "research": research.model_dump(),
            "logistics": logistics.model_dump(),
            "budget_breakdown": budget.model_dump(),
        },
        indent=2,
    )


async def synthesize(
    trip: TripRequest,
    research: ResearchOutput,
    logistics: LogisticsPlan,
    budget: BudgetBreakdown,
    *,
    client: Optional[groq.AsyncGroq] = None,
    revision_context: Optional[str] = None,
) -> DraftItinerary:
    """Merge research + logistics + budget into a day-by-day DraftItinerary."""
    client = client or groq.AsyncGroq()

    user_content = _build_user_message(trip, research, logistics, budget)
    if revision_context:
        user_content += (
            "\n\nRevision request from the Review Agent — address these issues "
            "in the new itinerary:\n" + revision_context
        )

    return await acall_groq_structured(
        client=client,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_content,
        response_model=DraftItinerary,
    )
