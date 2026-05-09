from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Severity = Literal["hard", "soft"]
RevisionTarget = Literal["research", "logistics", "synthesis"]


class CheckResult(BaseModel):
    name: str
    passed: bool
    severity: Severity = Field(
        description="'hard' = must pass for overall PASS; 'soft' = quality concern only."
    )
    reason: str


class QualitativeAssessment(BaseModel):
    """Single qualitative judgement from the Review Agent. Name/severity are added in code."""

    passed: bool
    reason: str


class QualitativeReview(BaseModel):
    """Structured output from the Review Agent's LLM call."""

    preferences_honored: QualitativeAssessment
    avoidances_honored: QualitativeAssessment
    travel_times_realistic: QualitativeAssessment
    pacing_reasonable: QualitativeAssessment


class ReviewResult(BaseModel):
    overall: Literal["PASS", "FAIL"]
    checks: List[CheckResult]
    failures: List[str] = Field(
        default_factory=list,
        description="Reasons from any failed checks, hard or soft.",
    )
    suggestions: List[str] = Field(default_factory=list)
    revision_target: Optional[RevisionTarget] = Field(
        default=None,
        description="Which earlier phase to re-run on FAIL, or null on PASS.",
    )
