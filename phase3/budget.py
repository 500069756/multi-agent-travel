import asyncio
import json
from typing import Optional, Tuple

import groq
from common.llm import acall_groq_structured

from phase0.schema import TripRequest
from phase2.logistics import plan_logistics
from phase2.research import research_destinations
from phase2.schema import LogisticsPlan, ResearchOutput

from .schema import (
    BudgetEvaluation,
    BudgetIteration,
    BudgetResult,
    RevisionRequest,
)


SYSTEM_PROMPT = """You are the Budget Agent in a travel-planning multi-agent system.

You receive a TripRequest, the Research Agent's POI list, and the Logistics Agent's plan.
Estimate total trip cost split across four categories: stay, transport, food, activities.

Rules:
- stay: realistic per-night hotel rates for each city's stay_area × nights. Mid-range default unless
  the budget_usd / duration_days ratio implies budget or luxury tier.
- transport: sum the inter-city transport_legs costs and add a daily allowance for intra-city transit
  (subway, taxi, local trains).
- food: per-day per-person estimate for each city. If preferences include "food", lean mid-range to
  good restaurants; otherwise budget tier.
- activities: include all "must_do" POI costs and a representative subset of "nice_to_have" items.
- total_estimated_usd = sum of category estimates.
- over_budget_by_usd = total_estimated_usd - budget_usd  (negative or zero means within budget).
- within_budget = (over_budget_by_usd <= 0).
- breakdown lists for each category should explain the estimate (e.g., "4 nights @ $180 = $720").

If over budget, populate revisions:
- target_agent = "research" if savings should come from the activity mix (drop expensive POIs,
  swap for free/cheap alternatives).
- target_agent = "logistics" if savings should come from cheaper stay areas or transport modes.
- target_savings_usd should sum across revisions to roughly cover over_budget_by_usd.
- instruction must be specific and actionable (cite the city, the swap, and why).

If within budget, return revisions = [].
- Return the output as a JSON object matching the BudgetEvaluation schema.
Example structure:
{
  "breakdown": {
    "categories": [
      {"name": "stay", "estimated_cost_usd": 600.0, "breakdown": ["3 nights @ $200"]},
      {"name": "transport", "estimated_cost_usd": 150.0, "breakdown": ["Metro + train"]},
      {"name": "food", "estimated_cost_usd": 300.0, "breakdown": ["$100/day"]},
      {"name": "activities", "estimated_cost_usd": 100.0, "breakdown": ["Museums"]}
    ],
    "total_estimated_usd": 1150.0,
    "budget_usd": 1200.0,
    "over_budget_by_usd": -50.0,
    "within_budget": true,
    "notes": "Stay: 3 nights @ $200. Transport: local trains."
  },
  "revisions": []
}
"""


def _build_user_message(
    trip: TripRequest,
    research: ResearchOutput,
    logistics: LogisticsPlan,
) -> str:
    return json.dumps(
        {
            "trip_request": trip.model_dump(),
            "research": research.model_dump(),
            "logistics": logistics.model_dump(),
        },
        indent=2,
    )


async def evaluate_budget(
    trip: TripRequest,
    research: ResearchOutput,
    logistics: LogisticsPlan,
    client: groq.AsyncGroq,
) -> BudgetEvaluation:
    """Single Budget Agent pass: estimate costs and emit revision requests if over budget."""
    return await acall_groq_structured(
        client=client,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_build_user_message(trip, research, logistics),
        response_model=BudgetEvaluation,
    )


def _split_revisions(revisions: list[RevisionRequest]) -> Tuple[Optional[str], Optional[str]]:
    """Group revision instructions by target agent and join them into single prompts."""
    research_lines = [r.instruction for r in revisions if r.target_agent == "research"]
    logistics_lines = [r.instruction for r in revisions if r.target_agent == "logistics"]
    research_ctx = "\n- " + "\n- ".join(research_lines) if research_lines else None
    logistics_ctx = "\n- " + "\n- ".join(logistics_lines) if logistics_lines else None
    return research_ctx, logistics_ctx


async def _rerun_scoped(
    trip: TripRequest,
    revisions: list[RevisionRequest],
    research: ResearchOutput,
    logistics: LogisticsPlan,
    client: groq.AsyncGroq,
) -> Tuple[ResearchOutput, LogisticsPlan]:
    """Re-run only the agents named in the revision targets, in parallel when both are needed."""
    research_ctx, logistics_ctx = _split_revisions(revisions)

    if research_ctx and logistics_ctx:
        return await asyncio.gather(
            research_destinations(trip, client, revision_context=research_ctx),
            plan_logistics(trip, client, revision_context=logistics_ctx),
        )
    if research_ctx:
        new_research = await research_destinations(trip, client, revision_context=research_ctx)
        return new_research, logistics
    if logistics_ctx:
        new_logistics = await plan_logistics(trip, client, revision_context=logistics_ctx)
        return research, new_logistics
    return research, logistics


async def reconcile_budget(
    trip: TripRequest,
    research: ResearchOutput,
    logistics: LogisticsPlan,
    *,
    max_revisions: int = 2,
    client: Optional[groq.AsyncGroq] = None,
) -> BudgetResult:
    """Reconcile cost estimates against budget. If over, re-run scoped agents up to max_revisions."""
    client = client or groq.AsyncGroq()

    history: list[BudgetIteration] = []
    iterations_used = 0

    for revision_round in range(max_revisions + 1):
        evaluation = await evaluate_budget(trip, research, logistics, client)
        history.append(
            BudgetIteration(
                iteration=revision_round,
                breakdown=evaluation.breakdown,
                revisions_emitted=evaluation.revisions,
            )
        )

        if evaluation.breakdown.within_budget:
            return BudgetResult(
                final_breakdown=evaluation.breakdown,
                final_research=research,
                final_logistics=logistics,
                history=history,
                iterations_used=iterations_used,
                converged=True,
            )

        if revision_round >= max_revisions:
            return BudgetResult(
                final_breakdown=evaluation.breakdown,
                final_research=research,
                final_logistics=logistics,
                history=history,
                iterations_used=iterations_used,
                converged=False,
            )

        research, logistics = await _rerun_scoped(
            trip, evaluation.revisions, research, logistics, client
        )
        iterations_used += 1

    raise RuntimeError("unreachable")
