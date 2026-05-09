from typing import Optional

from phase0.schema import TripRequest
from phase2.schema import LogisticsPlan
from phase3.schema import BudgetBreakdown
from phase4.schema import DraftItinerary
from phase5.schema import ReviewResult


def _money(amount: float) -> str:
    return f"${amount:,.0f}"


def _bullets(items: list[str], indent: str = "") -> str:
    return "\n".join(f"{indent}- {item}" for item in items) if items else f"{indent}- _(none)_"


def format_header(trip: TripRequest, itinerary: DraftItinerary) -> str:
    cities = " + ".join(trip.cities)
    pieces = [
        f"# {itinerary.title}",
        "",
        f"**Destination:** {trip.destination} — {cities}",
        f"**Duration:** {trip.duration_days} days",
        f"**Budget:** {_money(trip.budget_usd)} (estimated spend "
        f"{_money(itinerary.total_estimated_cost_usd)})",
    ]
    if trip.travel_dates:
        pieces.append(f"**Dates:** {trip.travel_dates}")
    if trip.preferences:
        pieces.append(f"**Loves:** {', '.join(trip.preferences)}")
    if trip.avoidances:
        pieces.append(f"**Avoids:** {', '.join(trip.avoidances)}")
    return "\n".join(pieces)


def format_summary(itinerary: DraftItinerary) -> str:
    return f"## Overview\n\n{itinerary.summary}"


def format_days(itinerary: DraftItinerary) -> str:
    sections = ["## Day-by-Day Plan"]
    for day in itinerary.days:
        date = f" ({day.date})" if day.date else ""
        sections.append(
            f"\n### Day {day.day_number} — {day.city}{date} · _{day.theme}_"
        )
        if day.transit_notes:
            sections.append(f"\n**Transit:** {day.transit_notes}")
        if day.morning:
            sections.append(f"\n**Morning**\n{_bullets(day.morning)}")
        if day.afternoon:
            sections.append(f"\n**Afternoon**\n{_bullets(day.afternoon)}")
        if day.evening:
            sections.append(f"\n**Evening**\n{_bullets(day.evening)}")
        if day.crowd_advisory:
            sections.append(f"\n> 💡 {day.crowd_advisory}")
        sections.append(f"\n**Day spend:** {_money(day.estimated_cost_usd)}")
    return "\n".join(sections)


def format_lodging(logistics: LogisticsPlan) -> str:
    rows = ["| City | Nights | Stay area | Why |", "|---|---|---|---|"]
    for stay in logistics.city_allocations:
        rows.append(
            f"| {stay.city} | {stay.nights} | {stay.stay_area} | {stay.stay_area_rationale} |"
        )
    if logistics.flex_days:
        rows.append(f"| _flex_ | {logistics.flex_days} | — | Buffer / spontaneous exploration |")
    return "## Lodging\n\n" + "\n".join(rows)


def format_transport(logistics: LogisticsPlan) -> str:
    if not logistics.transport_legs:
        return "## Inter-city Transport\n\n_No inter-city legs._"
    rows = ["| From | To | Mode | Time | Cost |", "|---|---|---|---|---|"]
    for leg in logistics.transport_legs:
        rows.append(
            f"| {leg.from_city} | {leg.to_city} | {leg.mode} | "
            f"{leg.estimated_duration_hours:.1f}h | {_money(leg.estimated_cost_usd)} |"
        )
    parts = ["## Inter-city Transport", "", "\n".join(rows)]
    if logistics.notes:
        parts.append(f"\n_{logistics.notes}_")
    return "\n".join(parts)


def format_budget(budget: BudgetBreakdown) -> str:
    rows = ["| Category | Estimate |", "|---|---|"]
    for cat in budget.categories:
        rows.append(f"| {cat.name.title()} | {_money(cat.estimated_cost_usd)} |")
    rows.append(f"| **Total** | **{_money(budget.total_estimated_usd)}** |")
    rows.append(f"| Budget cap | {_money(budget.budget_usd)} |")

    status = "Within budget ✓" if budget.within_budget else (
        f"Over by {_money(budget.over_budget_by_usd)} ⚠"
    )
    rows.append(f"| Status | {status} |")

    parts = ["## Budget Breakdown", "", "\n".join(rows)]
    if budget.notes:
        parts.append(f"\n_{budget.notes}_")

    line_items = [
        f"- **{cat.name.title()}** ({_money(cat.estimated_cost_usd)})\n"
        + "\n".join(f"  - {line}" for line in cat.breakdown)
        for cat in budget.categories
        if cat.breakdown
    ]
    if line_items:
        parts.append("\n### Line items\n")
        parts.extend(line_items)

    return "\n".join(parts)


def format_highlights(itinerary: DraftItinerary) -> str:
    return "## Highlights\n\n" + _bullets(itinerary.highlights)


def format_practical_notes(itinerary: DraftItinerary) -> str:
    return "## Practical Notes\n\n" + _bullets(itinerary.practical_notes)


def format_review(review_result: Optional[ReviewResult]) -> str:
    if review_result is None:
        return ""
    icon = "✅" if review_result.overall == "PASS" else "❌"
    parts = [f"## Review — {icon} {review_result.overall}"]
    if review_result.failures:
        parts.append("\n**Issues raised:**\n" + _bullets(review_result.failures))
    if review_result.suggestions:
        parts.append("\n**Suggested next steps:**\n" + _bullets(review_result.suggestions))
    if not review_result.failures and not review_result.suggestions:
        parts.append("\nAll checks passed.")
    return "\n".join(parts)


def deliver(
    trip: TripRequest,
    itinerary: DraftItinerary,
    logistics: LogisticsPlan,
    budget: BudgetBreakdown,
    review_result: Optional[ReviewResult] = None,
) -> str:
    """Compose the final user-facing markdown document."""
    sections = [
        format_header(trip, itinerary),
        format_summary(itinerary),
        format_days(itinerary),
        format_lodging(logistics),
        format_transport(logistics),
        format_budget(budget),
        format_highlights(itinerary),
        format_practical_notes(itinerary),
    ]
    review_section = format_review(review_result)
    if review_section:
        sections.append(review_section)
    return "\n\n".join(sections) + "\n"
