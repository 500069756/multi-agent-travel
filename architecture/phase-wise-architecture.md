# Phase-Wise Architecture — AI Travel Planner

## Phase 0 — Input & Intake
**Actor:** User → Orchestrator
- User submits natural-language request (e.g., *"5-day Japan, Tokyo + Kyoto, $3k, food + temples, no crowds"*).
- Orchestrator normalizes input into a structured **TripRequest** object.

**Output schema:**
```
{
  destination, cities[], duration_days,
  budget_usd, preferences[], avoidances[],
  travel_dates (optional)
}
```

---

## Phase 1 — Constraint Extraction & Planning
**Actor:** Orchestrator Agent
- Parses TripRequest → extracts hard constraints (budget, days, cities) vs soft preferences (food, temples, no crowds).
- Builds a **Task Graph**: which agents to call, in what order, with what dependencies.
- Decides parallel vs sequential execution.

**Output:** `MasterPlan` = ordered task list + shared context blackboard.

---

## Phase 2 — Parallel Research & Logistics (Fan-out)
Two agents run **in parallel** since they're independent:

### 2A — Destination Research Agent
- Queries web/travel guides using **Tavily Search API** for neighborhoods, temples, food streets.
- Filters by preference (food + temples) and avoidance (crowds → off-peak / lesser-known spots).
- Tags each item: `must-do | nice-to-have`, `crowd_level`, `category`.

### 2B — Logistics Agent
- Allocates nights per city (e.g., 2 Tokyo / 2 Kyoto / 1 flex).
- Picks stay areas, estimates inter-city transport (Shinkansen).
- Builds rough day sequence to minimize backtracking.

**Output:** `CandidatePOIs[]` + `LogisticsPlan`.

---

## Phase 3 — Budget Reconciliation
**Actor:** Budget Agent (runs after 2A + 2B complete)
- Pulls cost estimates: stay, transport, food, activities.
- Checks total vs $3,000 cap.
- If over budget → emits **revision requests** back to Logistics (cheaper hotel area) or Research (lower-cost activities).

**Loop condition:** if revisions needed, re-trigger Phase 2 (scoped) → Phase 3. Max 2 iterations to avoid infinite loops.

**Output:** `BudgetBreakdown` + adjusted plan.

---

## Phase 4 — Itinerary Synthesis
**Actor:** Orchestrator Agent
- Merges Research + Logistics + Budget outputs into a **day-by-day itinerary**.
- Slots POIs into days respecting geography, opening hours, crowd-avoidance.
- Produces narrative summary + structured day blocks.

**Output:** `DraftItinerary`.

---

## Phase 5 — Review & Validation
**Actor:** Review Agent
- Runs a checklist against `DraftItinerary`:
  - Fits 5 days?
  - Both cities present?
  - ≤ $3,000?
  - Food + temples represented?
  - Crowd-avoidance honored?
  - Travel times realistic?
- Returns `PASS` or `FAIL + reasons[]`.

**On FAIL:** Orchestrator routes back to the relevant agent (Phase 2 or 3). Cap at 2 review cycles.

---

## Phase 6 — Delivery
**Actor:** Orchestrator → User
- Formats validated itinerary into user-facing output: day-by-day plan, lodging suggestions, budget table, transport notes.

---

## Cross-Cutting Components

| Component | Purpose |
|---|---|
| **Groq (LLM)** | Primary inference engine for all agents (Llama 3 / Mixtral) |
| **Tavily (Search)** | Real-time web search and research tool for the Destination Research Agent |
| **Shared Blackboard / State Store** | All agents read/write structured context here (avoids re-passing data) |
| **Tool Registry** | Web search (Tavily), maps, currency FX, hotel data — exposed to agents that need them |
| **Message Bus** | Orchestrator ↔ agents communication (typed messages) |
| **Iteration Guard** | Caps Budget and Review loops to prevent infinite revision cycles |
| **Logging / Trace** | Records each agent's input/output for debugging and explainability |

---

## Data Flow Diagram (textual)

```
User
 │
 ▼
[Orchestrator] ──► extract constraints ──► MasterPlan
 │
 ├──► [Research Agent] ─┐
 │                      ├──► Blackboard
 └──► [Logistics Agent]─┘
                        │
                        ▼
                 [Budget Agent] ──► (revise loop if over budget)
                        │
                        ▼
                 [Orchestrator] ──► DraftItinerary
                        │
                        ▼
                  [Review Agent] ──► (revise loop if FAIL)
                        │
                        ▼
                     User
```
