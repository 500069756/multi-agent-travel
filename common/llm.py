import asyncio
import json
import os
import re
import time
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError
from groq import AsyncGroq, Groq, RateLimitError

T = TypeVar("T", bound=BaseModel)

# Each Groq model has its OWN daily TPD bucket.
# Override with GROQ_MODEL in .env to swap when one bucket is exhausted.
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_MAX_TOKENS = 4096   # cap output to slow daily TPD burn rate
MAX_RETRIES = 3
MAX_WAIT_SECONDS = 90       # don't block longer than this on a single retry


_RETRY_AFTER_M_S = re.compile(r"try again in (\d+)m([\d.]+)s")
_RETRY_AFTER_S = re.compile(r"try again in ([\d.]+)s")


def _retry_after_seconds(exc: Exception) -> float:
    """Parse Groq's 'try again in Xm Y.YYYs' / 'try again in Y.YYs' from the error message."""
    msg = str(exc)
    m = _RETRY_AFTER_M_S.search(msg)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = _RETRY_AFTER_S.search(msg)
    if m:
        return float(m.group(1))
    return 5.0


def _is_daily_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "tokens per day" in msg or "tpd" in msg or "requests per day" in msg


def _build_messages(system_prompt: str, user_prompt: str) -> list[dict]:
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    return messages


def _maybe_append_schema(
    messages: list[dict],
    system_prompt: str,
    user_prompt: str,
    response_model: Type[T] | None,
) -> None:
    if not response_model:
        return
    if "json" in system_prompt.lower() or "json" in user_prompt.lower():
        return
    schema_json = json.dumps(response_model.model_json_schema(), indent=2)
    messages[-1]["content"] = (
        user_prompt
        + f"\n\nReturn ONLY a JSON object matching this schema. No preamble or markdown:\n{schema_json}"
    )


def call_groq_structured(
    client: Groq,
    model: str = DEFAULT_MODEL,
    system_prompt: str = "",
    user_prompt: str = "",
    response_model: Type[T] = None,
    max_tokens: int | None = DEFAULT_MAX_TOKENS,
    **kwargs: Any,
) -> T:
    """Call Groq synchronously with retry-on-rate-limit and a token cap."""
    messages = _build_messages(system_prompt, user_prompt)
    _maybe_append_schema(messages, system_prompt, user_prompt, response_model)

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"} if response_model else None,
                max_tokens=max_tokens,
                **kwargs,
            )
            content = response.choices[0].message.content
            if response_model:
                try:
                    return response_model.model_validate_json(content)
                except ValidationError as e:
                    last_exc = e
                    if attempt + 1 == MAX_RETRIES:
                        break
                    print(f"[llm] validation error, retrying {attempt + 2}/{MAX_RETRIES}")
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": f"Your last response failed validation:\n{e}\nPlease fix the JSON and return a valid object. Do not use null for lists, use []."})
                    continue
            return content
        except RateLimitError as e:
            last_exc = e
            if _is_daily_limit(e):
                # Daily quota — retrying within a request can't help; surface immediately.
                raise
            if attempt + 1 == MAX_RETRIES:
                break
            wait = min(_retry_after_seconds(e) + 0.5, MAX_WAIT_SECONDS)
            print(f"[llm] rate limit hit, waiting {wait:.1f}s before retry {attempt + 2}/{MAX_RETRIES}")
            time.sleep(wait)
    assert last_exc is not None
    raise last_exc


async def acall_groq_structured(
    client: AsyncGroq,
    model: str = DEFAULT_MODEL,
    system_prompt: str = "",
    user_prompt: str = "",
    response_model: Type[T] = None,
    max_tokens: int | None = DEFAULT_MAX_TOKENS,
    **kwargs: Any,
) -> T:
    """Async version of call_groq_structured."""
    messages = _build_messages(system_prompt, user_prompt)
    _maybe_append_schema(messages, system_prompt, user_prompt, response_model)

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"} if response_model else None,
                max_tokens=max_tokens,
                **kwargs,
            )
            content = response.choices[0].message.content
            if response_model:
                try:
                    return response_model.model_validate_json(content)
                except ValidationError as e:
                    last_exc = e
                    if attempt + 1 == MAX_RETRIES:
                        break
                    print(f"[llm] validation error, retrying {attempt + 2}/{MAX_RETRIES}")
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": f"Your last response failed validation:\n{e}\nPlease fix the JSON and return a valid object. Do not use null for lists, use []."})
                    continue
            return content
        except RateLimitError as e:
            last_exc = e
            if _is_daily_limit(e):
                raise
            if attempt + 1 == MAX_RETRIES:
                break
            wait = min(_retry_after_seconds(e) + 0.5, MAX_WAIT_SECONDS)
            print(f"[llm] rate limit hit, waiting {wait:.1f}s before retry {attempt + 2}/{MAX_RETRIES}")
            await asyncio.sleep(wait)
    assert last_exc is not None
    raise last_exc
