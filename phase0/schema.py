from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class TripRequest(BaseModel):
    destination: str = Field(description="Country or region (e.g., 'Japan')")
    cities: List[str] = Field(description="Cities to visit, in order")
    duration_days: int = Field(description="Total trip length in days", gt=0)
    budget_usd: float = Field(description="Total budget in US dollars", ge=0)
    preferences: List[str] = Field(
        default_factory=list,
        description="Things the traveler enjoys (e.g., 'food', 'temples')",
    )
    avoidances: List[str] = Field(
        default_factory=list,
        description="Things to avoid (e.g., 'crowds')",
    )
    travel_dates: Optional[str] = Field(
        default=None,
        description="Travel dates if specified (e.g., 'April 2026'), else null",
    )

    @field_validator("cities", "preferences", "avoidances", mode="before")
    @classmethod
    def _null_to_empty_list(cls, v: Any) -> List[str]:
        return [] if v is None else v
