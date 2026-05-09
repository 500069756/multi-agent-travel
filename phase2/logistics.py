from typing import Optional

import groq
from common.llm import acall_groq_structured

from phase0.schema import TripRequest

from .schema import LogisticsPlan


SYSTEM_PROMPT = """You are the Logistics Agent in a travel-planning multi-agent system.

Given a structured TripRequest (JSON), produce a LogisticsPlan that covers night allocation,
stay-area recommendations, and inter-city transport.

Rules:
- Total nights across city_allocations + flex_days must equal duration_days.
- For each city, recommend a specific neighborhood (stay_area) and a one-sentence rationale in the `stay_area_rationale` field.
- transport_legs: Provide inter-city connections in order.
  - mode: Must be EXACTLY one of: "shinkansen", "train", "flight", "bus", "car", "ferry". (All lowercase).
  - Use EXACT field names: `estimated_duration_hours` and `estimated_cost_usd`. Do NOT shorten them.
- Return the output as a JSON object matching the LogisticsPlan schema exactly.

Example structure:
{
  "city_allocations": [
    {
      "city": "Tokyo",
      "nights": 2,
      "stay_area": "Shinjuku",
      "stay_area_rationale": "Major transport hub with many shops."
    },
    {
      "city": "Kyoto",
      "nights": 1,
      "stay_area": "Gion",
      "stay_area_rationale": "Historic district close to temples."
    }
  ],
  "transport_legs": [
    {
      "from_city": "Tokyo",
      "to_city": "Kyoto",
      "mode": "shinkansen",
      "estimated_duration_hours": 2.5,
      "estimated_cost_usd": 130.0
    }
  ],
  "flex_days": 0,
  "notes": "Purchase a JR Pass if visiting multiple cities."
}
"""


async def plan_logistics(
    trip: TripRequest,
    client: groq.AsyncGroq,
    *,
    revision_context: Optional[str] = None,
) -> LogisticsPlan:
    """Allocate nights, pick stay areas, and plan inter-city transport."""
    user_content = trip.model_dump_json()
    if revision_context:
        user_content += (
            "\n\nRevision request from the Budget Agent — adjust stay/transport to address this:\n"
            + revision_context
        )

    return await acall_groq_structured(
        client=client,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_content,
        response_model=LogisticsPlan,
    )
