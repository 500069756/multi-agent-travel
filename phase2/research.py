import asyncio
import os
from typing import Optional

import groq
from tavily import TavilyClient

from common.llm import acall_groq_structured
from phase0.schema import TripRequest

from .schema import ResearchOutput


SYSTEM_PROMPT = """You are the Destination Research Agent in a travel-planning multi-agent system.

You will be provided with a structured TripRequest and real-world search results from Tavily.
Your job is to recommend points of interest across the listed cities based on this data.

Rules:
- Produce 8-15 POIs total, distributed across all cities.
- For each POI, set:
  - category: temple, food_street, neighborhood, museum, experience, viewpoint, market, park, etc.
  - tier: "must_do" for marquee items, "nice_to_have" for optional add-ons.
  - crowd_level: "low" / "medium" / "high".
  - description: one or two sentences on why it fits the traveler.
- Honor preferences: weight categories the traveler likes.
- Honor avoidances: if "crowds" is listed, prefer low/medium crowd POIs and call out off-peak alternatives.
- Mix categories — don't return only one type.
- Use the provided search results to ensure POIs are real, currently open, and match the traveler's interests.
- Provide a short notes string with general advice (best time to visit, reservation tips, etc.).
- Return the output as a JSON object matching the ResearchOutput schema.
Example structure:
{
  "pois": [
    {
      "name": "Louvre Museum",
      "city": "Paris",
      "category": "museum",
      "tier": "must_do",
      "crowd_level": "high",
      "description": "World's largest art museum, home to the Mona Lisa.",
      "estimated_cost_usd": 20.0
    }
  ],
  "notes": "Book museum tickets in advance."
}
"""


async def _search_city(tavily: TavilyClient, city: str, country: str, preferences: list[str]) -> str:
    """Fetch real-world data for a specific city."""
    query = f"best things to do in {city}, {country} for {', '.join(preferences)} avoiding crowds"
    # TavilyClient is sync, so we wrap it
    response = await asyncio.to_thread(
        tavily.search,
        query=query,
        search_depth="advanced",
        max_results=5
    )
    
    results_text = f"--- Search Results for {city} ---\n"
    for r in response.get("results", []):
        results_text += f"- {r['title']}: {r['content']} (Source: {r['url']})\n"
    return results_text


async def research_destinations(
    trip: TripRequest,
    client: groq.AsyncGroq,
    *,
    revision_context: Optional[str] = None,
) -> ResearchOutput:
    """Recommend POIs using real-world search data from Tavily."""
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    tavily = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

    search_data = ""
    if tavily:
        try:
            tasks = [
                _search_city(tavily, city, trip.destination, trip.preferences)
                for city in trip.cities
            ]
            results = await asyncio.gather(*tasks)
            search_data = "\n".join(results)
        except Exception as exc:
            # Tavily failed (invalid key, rate limit, network) — fall back to model knowledge
            print(f"[research] Tavily search failed: {type(exc).__name__}: {exc}. "
                  "Continuing with model-only knowledge.")
            search_data = ""
    
    user_content = f"TRIP REQUEST:\n{trip.model_dump_json()}\n\n"
    if search_data:
        user_content += f"REAL-WORLD RESEARCH DATA:\n{search_data}\n\n"
        
    if revision_context:
        user_content += (
            "\n\nRevision request from the Budget Agent — adjust the POI list to address this:\n"
            + revision_context
        )

    return await acall_groq_structured(
        client=client,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_content,
        response_model=ResearchOutput,
    )
