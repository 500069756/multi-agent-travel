from phase0.schema import TripRequest

from .schema import HardConstraints, MasterPlan, SoftPreferences, Task


def plan(trip: TripRequest) -> MasterPlan:
    """Orchestrator: split TripRequest into hard/soft constraints and emit the task graph.

    The graph for this problem shape is fixed:
        research ─┐
                  ├─► budget ─► synthesis ─► review
        logistics ┘
    """
    hard = HardConstraints(
        destination=trip.destination,
        cities=trip.cities,
        duration_days=trip.duration_days,
        budget_usd=trip.budget_usd,
    )
    soft = SoftPreferences(
        likes=trip.preferences,
        dislikes=trip.avoidances,
        travel_dates=trip.travel_dates,
    )

    tasks = [
        Task(
            id="research",
            agent="DestinationResearchAgent",
            description="Recommend POIs filtered by preferences and avoidances.",
            depends_on=[],
            parallel_group="fan_out",
            inputs=["hard_constraints", "soft_preferences"],
            outputs=["research"],
        ),
        Task(
            id="logistics",
            agent="LogisticsAgent",
            description="Allocate nights per city, pick stay areas, plan inter-city transport.",
            depends_on=[],
            parallel_group="fan_out",
            inputs=["hard_constraints", "soft_preferences"],
            outputs=["logistics"],
        ),
        Task(
            id="budget",
            agent="BudgetAgent",
            description="Reconcile cost estimates against budget; request revisions if over.",
            depends_on=["research", "logistics"],
            inputs=["hard_constraints", "research", "logistics"],
            outputs=["budget"],
        ),
        Task(
            id="synthesis",
            agent="OrchestratorAgent",
            description="Merge research + logistics + budget into a day-by-day itinerary.",
            depends_on=["budget"],
            inputs=["hard_constraints", "soft_preferences", "research", "logistics", "budget"],
            outputs=["draft_itinerary"],
        ),
        Task(
            id="review",
            agent="ReviewAgent",
            description="Validate the draft itinerary against all constraints; PASS or FAIL.",
            depends_on=["synthesis"],
            inputs=["hard_constraints", "soft_preferences", "draft_itinerary", "budget"],
            outputs=["review_result"],
        ),
    ]

    blackboard_seed = {
        "hard_constraints": hard.model_dump(),
        "soft_preferences": soft.model_dump(),
    }

    rationale = (
        f"Standard 5-stage plan for a {hard.duration_days}-day {hard.destination} trip "
        f"across {len(hard.cities)} cities ({', '.join(hard.cities)}) within "
        f"${hard.budget_usd:,.0f}. Research and logistics are independent so they fan out; "
        f"budget reconciles their outputs; synthesis weaves the itinerary; review gates delivery."
    )

    return MasterPlan(
        hard_constraints=hard,
        soft_preferences=soft,
        tasks=tasks,
        blackboard_seed=blackboard_seed,
        rationale=rationale,
    )
