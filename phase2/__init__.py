import asyncio
from typing import Tuple

import groq

from phase0.schema import TripRequest

from .logistics import plan_logistics
from .research import research_destinations
from .schema import (
    CandidatePOI,
    CityStay,
    InterCityLeg,
    LogisticsPlan,
    ResearchOutput,
)


async def fan_out(
    trip: TripRequest,
    client: groq.AsyncGroq | None = None,
) -> Tuple[ResearchOutput, LogisticsPlan]:
    """Run the research and logistics agents in parallel against the same TripRequest."""
    client = client or groq.AsyncGroq()
    research, logistics = await asyncio.gather(
        research_destinations(trip, client),
        plan_logistics(trip, client),
    )
    return research, logistics


__all__ = [
    "CandidatePOI",
    "CityStay",
    "InterCityLeg",
    "LogisticsPlan",
    "ResearchOutput",
    "fan_out",
    "plan_logistics",
    "research_destinations",
]
