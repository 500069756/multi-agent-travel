from typing import List, Optional

from pydantic import BaseModel, Field


class DayBlock(BaseModel):
    day_number: int = Field(ge=1)
    city: str = Field(description="Primary city for this day.")
    date: Optional[str] = Field(default=None, description="Calendar date if travel_dates were provided.")
    theme: str = Field(description="One-line theme, e.g., 'Temples in eastern Kyoto'.")
    morning: List[str] = Field(default_factory=list, description="Activities/POIs in order.")
    afternoon: List[str] = Field(default_factory=list)
    evening: List[str] = Field(default_factory=list)
    transit_notes: str = Field(
        default="",
        description="Inter-city movement that day, e.g., 'Morning Shinkansen Tokyo → Kyoto'.",
    )
    estimated_cost_usd: float = Field(ge=0)
    crowd_advisory: Optional[str] = Field(
        default=None,
        description="Off-peak timing tips for crowded POIs scheduled this day.",
    )


class DraftItinerary(BaseModel):
    title: str
    summary: str = Field(description="2-4 sentence narrative overview reflecting the trip's character.")
    days: List[DayBlock]
    highlights: List[str] = Field(description="3-5 standout moments from the trip.")
    practical_notes: List[str] = Field(
        description="Actionable tips: rail passes, reservations, payment methods, etc."
    )
    total_estimated_cost_usd: float = Field(ge=0)
