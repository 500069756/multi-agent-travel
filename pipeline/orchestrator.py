from typing import Optional

import groq

from phase0 import intake
from phase2 import fan_out
from phase2.logistics import plan_logistics
from phase2.research import research_destinations
from phase3 import reconcile_budget
from phase4 import synthesize
from phase5 import review
from phase6 import deliver

from .schema import PipelineCycle, PipelineResult


def _failures_to_context(reasons: list[str]) -> str:
    return "\n- " + "\n- ".join(reasons) if reasons else ""


async def run_pipeline(
    request_text: str,
    *,
    max_review_cycles: int = 2,
    client: Optional[groq.AsyncGroq] = None,
) -> PipelineResult:
    """Drive all 6 phases. On review FAIL, route to the targeted phase up to max_review_cycles."""
    client = client or groq.AsyncGroq()

    # Phase 0 (sync, uses its own client if not passed, but we'll let it use default for now or pass a sync client if needed)
    # Actually, intake expects a sync client.
    sync_client = groq.Groq()
    trip = intake(request_text, client=sync_client)

    # Phase 2 — initial fan-out
    research, logistics = await fan_out(trip, client)

    # Phase 3 — initial budget reconciliation (may itself loop research/logistics up to 2x)
    budget_result = await reconcile_budget(trip, research, logistics, client=client)
    research = budget_result.final_research
    logistics = budget_result.final_logistics
    budget = budget_result.final_breakdown

    cycles: list[PipelineCycle] = []
    itinerary = None
    review_result = None

    for cycle in range(max_review_cycles + 1):
        # Phase 4 — synthesis (with revision context on retries)
        revision_context = None
        if cycles and cycles[-1].review.failures:
            revision_context = _failures_to_context(cycles[-1].review.failures)

        itinerary = await synthesize(
            trip,
            research,
            logistics,
            budget,
            client=client,
            revision_context=revision_context if cycles and cycles[-1].revision_target == "synthesis" else None,
        )

        # Phase 5 — review
        review_result = await review(trip, itinerary, client=client)

        target = review_result.revision_target
        cycles.append(
            PipelineCycle(
                cycle=cycle,
                itinerary=itinerary,
                review=review_result,
                revision_target=target if review_result.overall == "FAIL" else None,
            )
        )

        if review_result.overall == "PASS":
            break
        if cycle >= max_review_cycles:
            break

        # Route the revision to the upstream phase the review pointed at
        revision_text = _failures_to_context(review_result.failures)

        if target == "research":
            research = await research_destinations(
                trip, client, revision_context=revision_text
            )
            # Re-reconcile budget — costs may have shifted with new POI mix
            budget_result = await reconcile_budget(
                trip, research, logistics, client=client
            )
            research = budget_result.final_research
            logistics = budget_result.final_logistics
            budget = budget_result.final_breakdown

        elif target == "logistics":
            logistics = await plan_logistics(
                trip, client, revision_context=revision_text
            )
            budget_result = await reconcile_budget(
                trip, research, logistics, client=client
            )
            research = budget_result.final_research
            logistics = budget_result.final_logistics
            budget = budget_result.final_breakdown

        # target == "synthesis" or None: loop back and re-synthesize with revision_context

    document = deliver(trip, itinerary, logistics, budget, review_result)

    return PipelineResult(
        trip=trip,
        final_research=research,
        final_logistics=logistics,
        final_budget=budget,
        final_itinerary=itinerary,
        final_review=review_result,
        cycles=cycles,
        converged=review_result.overall == "PASS",
        document=document,
    )
