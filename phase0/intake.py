import groq
from common.llm import call_groq_structured

from .schema import TripRequest


SYSTEM_PROMPT = """You are the intake stage of a travel-planning multi-agent system.

Your job: read a short natural-language travel request and extract its constraints \
into a structured TripRequest object.

Rules:
- destination is the country or region (e.g., "Japan", "Italy").
- cities lists every city the traveler wants to visit, preserving the order they mention them.
- duration_days is the total trip length. If a range is given, use the upper bound.
- budget_usd is in US dollars. Convert other currencies if obvious. If not specified, estimate a reasonable mid-range budget for the duration (e.g., $200-$300 per day).
- preferences are things the traveler likes (food, temples, museums, hiking, nightlife, etc.).
- avoidances are things they want to avoid (crowds, expensive restaurants, long flights, etc.).
- travel_dates: only fill if explicitly mentioned, else null.
- Do not invent fields the user did not provide.
- Return the output as a JSON object matching the TripRequest schema.
Example structure:
{
  "destination": "France",
  "cities": ["Paris"],
  "duration_days": 3,
  "budget_usd": 900.0,
  "preferences": ["art", "croissants"],
  "avoidances": ["crowds"],
  "travel_dates": null
}
"""


def intake(request_text: str, *, client: groq.Groq | None = None) -> TripRequest:
    """Parse a natural-language travel request into a structured TripRequest."""
    client = client or groq.Groq()

    return call_groq_structured(
        client=client,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=request_text,
        response_model=TripRequest,
    )
