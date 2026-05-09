from typing import List

from phase0.schema import TripRequest
from phase4.schema import DraftItinerary

from .schema import CheckResult


def check_day_count(trip: TripRequest, itinerary: DraftItinerary) -> CheckResult:
    expected = trip.duration_days
    actual = len(itinerary.days)
    return CheckResult(
        name="day_count",
        severity="hard",
        passed=actual == expected,
        reason=(
            f"Itinerary has {actual} days, matching the {expected}-day request."
            if actual == expected
            else f"Itinerary has {actual} days but request asked for {expected}."
        ),
    )


def check_cities_covered(trip: TripRequest, itinerary: DraftItinerary) -> CheckResult:
    requested = {c.lower() for c in trip.cities}
    covered = {d.city.lower() for d in itinerary.days}
    missing = requested - covered
    if not missing:
        return CheckResult(
            name="cities_covered",
            severity="hard",
            passed=True,
            reason=f"All requested cities present: {', '.join(trip.cities)}.",
        )
    return CheckResult(
        name="cities_covered",
        severity="hard",
        passed=False,
        reason=f"Missing cities from itinerary: {', '.join(sorted(missing))}.",
    )


def check_budget(trip: TripRequest, itinerary: DraftItinerary) -> CheckResult:
    total = itinerary.total_estimated_cost_usd
    if total <= trip.budget_usd:
        return CheckResult(
            name="budget",
            severity="hard",
            passed=True,
            reason=f"Total ${total:,.0f} ≤ budget ${trip.budget_usd:,.0f}.",
        )
    over = total - trip.budget_usd
    return CheckResult(
        name="budget",
        severity="hard",
        passed=False,
        reason=f"Total ${total:,.0f} exceeds budget ${trip.budget_usd:,.0f} by ${over:,.0f}.",
    )


def check_day_cost_consistency(itinerary: DraftItinerary) -> CheckResult:
    day_sum = sum(d.estimated_cost_usd for d in itinerary.days)
    total = itinerary.total_estimated_cost_usd
    diff = abs(day_sum - total)
    tolerance = max(50.0, total * 0.05)
    if diff <= tolerance:
        return CheckResult(
            name="day_cost_consistency",
            severity="soft",
            passed=True,
            reason=f"Day costs sum to ${day_sum:,.0f}, within tolerance of total ${total:,.0f}.",
        )
    return CheckResult(
        name="day_cost_consistency",
        severity="soft",
        passed=False,
        reason=(
            f"Day costs sum to ${day_sum:,.0f} but itinerary total claims ${total:,.0f} "
            f"(off by ${diff:,.0f})."
        ),
    )


def run_deterministic_checks(
    trip: TripRequest, itinerary: DraftItinerary
) -> List[CheckResult]:
    return [
        check_day_count(trip, itinerary),
        check_cities_covered(trip, itinerary),
        check_budget(trip, itinerary),
        check_day_cost_consistency(itinerary),
    ]
