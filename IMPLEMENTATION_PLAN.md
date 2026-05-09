# Implementation Plan: Refactoring to Groq & Tavily

This plan outlines the steps required to migrate the AI Travel Planner from Anthropic to Groq for LLM inference and integrate Tavily for real-time web search.

## Phase 1: Environment & Dependencies
- [x] Update `requirements.txt` to include `groq` and `tavily-python`.
- [x] Update `.env.example` with `GROQ_API_KEY` and `TAVILY_API_KEY`.
- [x] Update `common/env.py` to load new environment variables (Generic loader already supports this).

## Phase 2: LLM Client Refactoring
- [x] Replace `anthropic.AsyncAnthropic` with `groq.AsyncGroq` across all agents.
- [x] Update `client.messages.parse` (Anthropic pattern) to `client.chat.completions.create` (Groq/OpenAI pattern) via `common/llm.py`.
- [x] Implement a robust structured output parser for Groq (using Pydantic models with `response_format={"type": "json_object"}`).

## Phase 3: Search Integration (Tavily)
- [x] Initialize Tavily client in `phase2/research.py`.
- [x] Implement search logic in `research_destinations` to fetch real-world data before calling the LLM.
- [x] Feed search results into the LLM prompt for more accurate POI recommendations.

## Phase 4: Agent-Specific Updates
- [x] **Orchestrator Agent (Phase 1 & 4):** Update to use Groq for planning and synthesis.
- [x] **Research Agent (Phase 2A):** Integrate Tavily search and update to Groq.
- [x] **Logistics Agent (Phase 2B):** Update to Groq for planning logistics.
- [x] **Budget Agent (Phase 3):** Update to Groq for budget reconciliation.
- [x] **Review Agent (Phase 5):** Update to Groq for validation.

## Phase 5: Verification & Testing
- [x] Verify that structured outputs are correctly parsed from Groq (implemented in `common/llm.py` with schema enforcement and examples).
- [x] Test the full pipeline (`pipeline/main.py`) with new components (Successfully run end-to-end for Paris trip).
- [x] Ensure Tavily results are relevant and properly utilized (Confirmed in `phase2/research.py` results).
