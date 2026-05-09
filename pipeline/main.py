"""End-to-end pipeline runner — Phase 0 through Phase 6 with bounded review-revision loop."""
from common import load_environment

load_environment()

import asyncio
import sys
import io

# Ensure UTF-8 output for emojis in Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path

from pipeline import run_pipeline


SAMPLE = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "trip_plan.md"


async def run(request_text: str) -> None:
    print(f"Input: {request_text}\n")

    result = await run_pipeline(request_text)

    print("=== Cycle history ===")
    for cyc in result.cycles:
        target = f" → revise {cyc.revision_target}" if cyc.revision_target else ""
        print(f"  cycle {cyc.cycle}: review = {cyc.review.overall}{target}")
        for f in cyc.review.failures:
            print(f"      - {f}")
    print()

    print(f"Converged: {result.converged}")
    print(f"Final review: {result.final_review.overall}")
    print(f"Final cost: ${result.final_itinerary.total_estimated_cost_usd:,.0f} "
          f"vs budget ${result.trip.budget_usd:,.0f}\n")

    OUTPUT_FILE.write_text(result.document, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE.name} ({len(result.document):,} chars)")
    print("=" * 72)
    print(result.document)


def main() -> None:
    request_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else SAMPLE
    asyncio.run(run(request_text))


if __name__ == "__main__":
    main()
