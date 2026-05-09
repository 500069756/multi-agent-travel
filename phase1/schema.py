from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HardConstraints(BaseModel):
    """Constraints that MUST be honored. Violating any of these = plan rejected."""

    destination: str
    cities: List[str]
    duration_days: int = Field(gt=0)
    budget_usd: float = Field(ge=0)


class SoftPreferences(BaseModel):
    """Preferences to optimize toward / away from. Trade-offs allowed."""

    likes: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    travel_dates: Optional[str] = None


class Task(BaseModel):
    id: str = Field(description="Stable task identifier referenced by depends_on.")
    agent: str = Field(description="Which agent executes this task.")
    description: str
    depends_on: List[str] = Field(
        default_factory=list,
        description="Task ids that must complete before this one runs.",
    )
    parallel_group: Optional[str] = Field(
        default=None,
        description="Tasks with the same parallel_group can run concurrently.",
    )
    inputs: List[str] = Field(
        default_factory=list,
        description="Blackboard keys this task reads.",
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Blackboard keys this task writes.",
    )


class MasterPlan(BaseModel):
    hard_constraints: HardConstraints
    soft_preferences: SoftPreferences
    tasks: List[Task]
    blackboard_seed: Dict[str, Any] = Field(
        description="Initial shared state every agent reads from."
    )
    rationale: str

    def execution_order(self) -> List[List[str]]:
        """Return tasks grouped into waves that can run together (topological)."""
        remaining = {t.id: set(t.depends_on) for t in self.tasks}
        order: List[List[str]] = []
        while remaining:
            ready = [tid for tid, deps in remaining.items() if not deps]
            if not ready:
                raise ValueError("Cyclic dependency in task graph")
            order.append(sorted(ready))
            for tid in ready:
                del remaining[tid]
            for deps in remaining.values():
                deps.difference_update(ready)
        return order
