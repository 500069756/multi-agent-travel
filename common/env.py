from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    """Load environment variables from .env, falling back to .env.example.

    Real keys belong in .env (gitignored). .env.example is the committed template
    and is loaded only as a fallback so a key dropped there still works.
    Existing process environment variables are never overridden.
    """
    load_dotenv(ROOT / ".env", override=False)
    load_dotenv(ROOT / ".env.example", override=False)
