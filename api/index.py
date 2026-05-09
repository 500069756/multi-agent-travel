"""Vercel serverless entry point — exposes the FastAPI app."""
import sys
from pathlib import Path

# Add project root so phase0..phase6, pipeline, common, web are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web.server import app  # noqa: E402,F401  (Vercel detects `app`)
