from typing import Optional

import groq

from phase0.schema import TripRequest
from phase4.schema import DraftItinerary

from .deterministic import run_deterministic_checks
from .qualitative import run_qualitative_checks
from .schema import CheckResult, ReviewResult, RevisionTarget


# Routing rules: failed check name → which earlier phase to re-run.
# First match wins, in priority order.
_ROUTING: list[tuple[str, RevisionTarget, str]] = [
    ("budget", "research", "Budget exceeded — drop expensive POIs or downgrade stay tier."),
    ("day_count", "synthesis", "Re-run synthesis ensuring duration_days is honored."),
    ("cities_covered", "synthesis", "Re-run synthesis ensuring every requested city is visited."),
    ("preferences_honored", "research", "Re-run research with stronger preference emphasis."),
    ("avoidances_honored", "research", "Re-run research filtering harder for avoidances."),
    ("travel_times_realistic", "synthesis", "Re-run synthesis with tighter geographic grouping."),
]


def _route_revision(failed_names: set[str]) -> tuple[Optional[RevisionTarget], list[str]]:
    """Pick the highest-priority failed check and emit its revision target + suggestion."""
    suggestions: list[str] = []
    target: Optional[RevisionTarget] = None
    for name, route_target, suggestion in _ROUTING:
        if name in failed_names:
            if target is None:
                target = route_target
            suggestions.append(suggestion)
    return target, suggestions


async def review(
    trip: TripRequest,
    itinerary: DraftItinerary,
    *,
    client: Optional[groq.AsyncGroq] = None,
) -> ReviewResult:
    """Validate the DraftItinerary. Hybrid: deterministic hard checks + LLM qualitative checks."""
    deterministic_results = run_deterministic_checks(trip, itinerary)

    client = client or groq.AsyncGroq()
    qualitative_results = await run_qualitative_checks(trip, itinerary, client)

    all_checks: list[CheckResult] = deterministic_results + qualitative_results

    hard_failures = [c for c in all_checks if not c.passed and c.severity == "hard"]
    overall = "FAIL" if hard_failures else "PASS"

    failures = [c.reason for c in all_checks if not c.passed]
    failed_names = {c.name for c in all_checks if not c.passed and c.severity == "hard"}
    revision_target, suggestions = (
        _route_revision(failed_names) if failed_names else (None, [])
    )

    return ReviewResult(
        overall=overall,
        checks=all_checks,
        failures=failures,
        suggestions=suggestions,
        revision_target=revision_target,
    )
