from common import load_environment

load_environment()

import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from groq import RateLimitError
from pydantic import BaseModel, Field

from pipeline import run_pipeline


WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(title="AI Travel Planner")


class PlanRequest(BaseModel):
    request: str = Field(min_length=1)


class CycleSummary(BaseModel):
    cycle: int
    overall: str
    revision_target: Optional[str]
    failures: List[str]


class PlanResponse(BaseModel):
    document: str
    cycles: List[CycleSummary]
    converged: bool
    final_overall: str
    total_estimated_cost_usd: float
    budget_usd: float


@app.get("/api/health")
async def health() -> dict:
    has_groq = bool(os.environ.get("GROQ_API_KEY"))
    has_tavily = bool(os.environ.get("TAVILY_API_KEY"))
    return {
        "ok": True,
        "groq_key_configured": has_groq,
        "tavily_key_configured": has_tavily
    }


@app.post("/api/plan", response_model=PlanResponse)
async def plan(req: PlanRequest) -> PlanResponse:
    try:
        result = await run_pipeline(req.request)
    except RateLimitError as exc:
        # Surface Groq's quota errors as 429 so the frontend can show a useful message
        msg = str(exc)
        is_daily = "tokens per day" in msg.lower() or "tpd" in msg.lower()
        prefix = "Daily token quota exhausted on Groq free tier." if is_daily else "Rate limited by Groq."
        raise HTTPException(status_code=429, detail=f"{prefix} {msg}")
    except Exception as exc:  # surface other pipeline errors to the client
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

    return PlanResponse(
        document=result.document,
        cycles=[
            CycleSummary(
                cycle=c.cycle,
                overall=c.review.overall,
                revision_target=c.revision_target,
                failures=c.review.failures,
            )
            for c in result.cycles
        ],
        converged=result.converged,
        final_overall=result.final_review.overall,
        total_estimated_cost_usd=result.final_itinerary.total_estimated_cost_usd,
        budget_usd=result.trip.budget_usd,
    )


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
