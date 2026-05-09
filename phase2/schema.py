from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


Tier = Literal["must_do", "nice_to_have"]
CrowdLevel = Literal["low", "medium", "high"]
TransportMode = Literal["shinkansen", "train", "flight", "bus", "car", "ferry"]


def _normalize_enum(v: Any) -> Any:
    """Coerce LLM-emitted enum strings into the canonical underscore_lower form.

    Handles drift like 'Nice-to-Have', 'must do', 'NICE_TO_HAVE', 'Shinkansen ' → 'nice_to_have' / 'must_do' / 'shinkansen'.
    Non-strings pass through unchanged so Pydantic can raise its normal type error.
    """
    if isinstance(v, str):
        return v.strip().lower().replace("-", "_").replace(" ", "_")
    return v


class CandidatePOI(BaseModel):
    name: str
    city: str
    category: str = Field(
        description="Type of POI: temple, food_street, neighborhood, museum, experience, viewpoint, etc."
    )
    tier: Tier
    crowd_level: CrowdLevel
    description: str = Field(description="One or two sentences on why it fits the traveler.")
    estimated_cost_usd: Optional[float] = Field(
        default=None, description="Rough per-person cost; null if free or highly variable."
    )

    _normalize_tier = field_validator("tier", mode="before")(lambda cls, v: _normalize_enum(v))
    _normalize_crowd = field_validator("crowd_level", mode="before")(lambda cls, v: _normalize_enum(v))


class ResearchOutput(BaseModel):
    pois: List[CandidatePOI] = Field(description="8-15 POIs across all cities, ranked by fit.")
    notes: str = Field(description="General travel tips relevant to the request.")


class CityStay(BaseModel):
    city: str
    nights: int = Field(ge=0)
    stay_area: str = Field(description="Recommended neighborhood name.")
    stay_area_rationale: str


class InterCityLeg(BaseModel):
    from_city: str
    to_city: str
    mode: TransportMode
    estimated_duration_hours: float = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)

    _normalize_mode = field_validator("mode", mode="before")(lambda cls, v: _normalize_enum(v))


class LogisticsPlan(BaseModel):
    city_allocations: List[CityStay]
    transport_legs: List[InterCityLeg]
    flex_days: int = Field(ge=0, description="Unallocated days for buffer/exploration.")
    notes: str
