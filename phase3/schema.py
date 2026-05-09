from typing import Any, List, Literal

from pydantic import BaseModel, Field, field_validator

from phase2.schema import LogisticsPlan, ResearchOutput


RevisionTarget = Literal["research", "logistics"]


def _normalize_enum(v: Any) -> Any:
    """Coerce LLM-emitted enum strings into the canonical underscore_lower form."""
    if isinstance(v, str):
        return v.strip().lower().replace("-", "_").replace(" ", "_")
    return v


class BudgetCategory(BaseModel):
    name: Literal["stay", "transport", "food", "activities"]
    estimated_cost_usd: float = Field(ge=0)
    breakdown: List[str] = Field(
        default_factory=list,
        description="Human-readable line items contributing to the estimate.",
    )

    _normalize_name = field_validator("name", mode="before")(lambda cls, v: _normalize_enum(v))


class BudgetBreakdown(BaseModel):
    categories: List[BudgetCategory]
    total_estimated_usd: float = Field(ge=0)
    budget_usd: float = Field(ge=0)
    over_budget_by_usd: float = Field(
        description="Positive if over budget, negative or zero if within."
    )
    within_budget: bool
    notes: str


class RevisionRequest(BaseModel):
    target_agent: RevisionTarget = Field(
        description="research = cheaper activities/POIs; logistics = cheaper stay/transport."
    )
    target_savings_usd: float = Field(
        ge=0, description="Approximate dollars to cut via this revision."
    )
    instruction: str = Field(description="Specific actionable guidance for the agent.")

    _normalize_target = field_validator("target_agent", mode="before")(lambda cls, v: _normalize_enum(v))


class BudgetEvaluation(BaseModel):
    """Single Budget Agent output. Empty revisions = within budget."""

    breakdown: BudgetBreakdown
    revisions: List[RevisionRequest] = Field(default_factory=list)


class BudgetIteration(BaseModel):
    iteration: int
    breakdown: BudgetBreakdown
    revisions_emitted: List[RevisionRequest]


class BudgetResult(BaseModel):
    final_breakdown: BudgetBreakdown
    final_research: ResearchOutput
    final_logistics: LogisticsPlan
    history: List[BudgetIteration]
    iterations_used: int = Field(
        description="Number of revision rounds applied (0 if first pass was within budget)."
    )
    converged: bool = Field(description="True if the final plan is within budget.")
