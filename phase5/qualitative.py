import json
from typing import List

import groq
from common.llm import acall_groq_structured

from phase0.schema import TripRequest
from phase4.schema import DraftItinerary

from .schema import CheckResult, QualitativeReview


SYSTEM_PROMPT = """You are the Review Agent in a travel-planning multi-agent system.

You receive the original TripRequest and the DraftItinerary. Run four qualitative checks and
return one assessment (passed + reason) for each.

Checks (return all four):

1. preferences_honored — Do POIs and activities clearly reflect the traveler's stated preferences?
   If preferences include "food", expect food-focused activities and notable meals.
   If "temples", expect temple visits. Pass if the trip clearly leans into them; fail with specifics
   if they are missing or underrepresented.

2. avoidances_honored — Are stated avoidances respected? If "crowds" is listed, look for
   crowd_advisory entries on busy days, off-peak timing suggestions, or lesser-known alternatives.
   Pass if there is clear effort; fail if the issue is ignored.

3. travel_times_realistic — Are inter-city movements accounted for in transit_notes on the right
   days? Is each daily plan achievable given the geography (POIs grouped sensibly, no impossible
   bouncing across the city)? Fail with specifics if a day looks unrealistic.

4. pacing_reasonable — Are days well-paced (not crammed, not too sparse)? Are POIs grouped
   geographically within each day? Pass if pacing feels comfortable and tied to the traveler's
   energy level for the trip length.

For each check, the reason string must be specific and reference concrete days, cities, or POIs from
the itinerary — not generic statements.

- Return the output as a JSON object matching the QualitativeReview schema.
Example structure:
{
  "preferences_honored": {"passed": true, "reason": "Included art museums and bakeries."},
  "avoidances_honored": {"passed": true, "reason": "Morning timing for popular spots."},
  "travel_times_realistic": {"passed": true, "reason": "POIs grouped by arrondissement."},
  "pacing_reasonable": {"passed": true, "reason": "3 activities per day is manageable."}
}
"""


# Map QualitativeReview field name -> (CheckResult name, severity)
_FIELD_MAP = {
    "preferences_honored": ("preferences_honored", "hard"),
    "avoidances_honored": ("avoidances_honored", "hard"),
    "travel_times_realistic": ("travel_times_realistic", "hard"),
    "pacing_reasonable": ("pacing_reasonable", "soft"),
}


async def run_qualitative_checks(
    trip: TripRequest,
    itinerary: DraftItinerary,
    client: groq.AsyncGroq,
) -> List[CheckResult]:
    user_message = json.dumps(
        {
            "trip_request": trip.model_dump(),
            "draft_itinerary": itinerary.model_dump(),
        },
        indent=2,
    )

    review: QualitativeReview = await acall_groq_structured(
        client=client,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_message,
        response_model=QualitativeReview,
    )

    results: List[CheckResult] = []
    for field_name, (check_name, severity) in _FIELD_MAP.items():
        assessment = getattr(review, field_name)
        results.append(
            CheckResult(
                name=check_name,
                severity=severity,
                passed=assessment.passed,
                reason=assessment.reason,
            )
        )
    return results
