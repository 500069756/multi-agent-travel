from typing import List, Optional

from pydantic import BaseModel, Field

from phase0.schema import TripRequest
from phase2.schema import LogisticsPlan, ResearchOutput
from phase3.schema import BudgetBreakdown
from phase4.schema import DraftItinerary
from phase5.schema import ReviewResult


class PipelineCycle(BaseModel):
    cycle: int = Field(description="0 = first synthesis+review; >0 = revision rounds.")
    itinerary: DraftItinerary
    review: ReviewResult
    revision_target: Optional[str] = Field(
        default=None,
        description="Where this cycle's revision was routed (null on the final cycle if PASS).",
    )


class PipelineResult(BaseModel):
    trip: TripRequest
    final_research: ResearchOutput
    final_logistics: LogisticsPlan
    final_budget: BudgetBreakdown
    final_itinerary: DraftItinerary
    final_review: ReviewResult
    cycles: List[PipelineCycle]
    converged: bool = Field(description="True if the final review passed within the cycle cap.")
    document: str = Field(description="The Phase 6 markdown delivery.")
