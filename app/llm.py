"""Thin OpenRouter client (OpenAI-compatible chat completions) plus a tolerant JSON extractor."""
from __future__ import annotations

import json
import re
import time

import httpx

from . import config


class LLMError(RuntimeError):
    pass


def available() -> bool:
    return bool(config.OPENROUTER_API_KEY)


def chat(messages: list[dict], *, model: str | None = None, temperature: float = 0.0,
         max_tokens: int = 900, json_mode: bool = True, timeout: float = 60.0) -> tuple[str, dict]:
    """Return (content, usage). Raises LLMError with a readable message on failure."""
    if not available():
        raise LLMError("OPENROUTER_API_KEY is not set")
    payload: dict = {
        "model": model or config.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/Sarthak195/rulebook-that-argues",
        "X-Title": "The Rulebook That Argues With Itself",
        "Content-Type": "application/json",
    }
    resp = _post_with_retries(payload, headers, timeout)
    if resp.status_code != 200 and json_mode and resp.status_code in (400, 404, 422):
        # Some models reject response_format; retry without it and rely on the prompt.
        payload.pop("response_format", None)
        resp = _post_with_retries(payload, headers, timeout)
    if resp.status_code != 200:
        raise LLMError(f"OpenRouter HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"unexpected OpenRouter response: {json.dumps(data)[:300]}") from e
    if not content and data.get("error"):
        raise LLMError(f"OpenRouter error: {data['error']}")
    usage = data.get("usage", {}) or {}
    usage["model"] = data.get("model")  # the concrete model, useful when routing through openrouter/free
    return content or "", usage


RETRY_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}


def _post_with_retries(payload: dict, headers: dict, timeout: float, attempts: int = 5) -> httpx.Response:
    """Free-tier models rate-limit aggressively; back off instead of failing the question."""
    delay = 2.0
    last: httpx.Response | None = None
    for attempt in range(attempts):
        try:
            resp = httpx.post(config.OPENROUTER_URL, json=payload, headers=headers, timeout=timeout)
        except httpx.HTTPError as e:
            if attempt == attempts - 1:
                raise LLMError(f"network error talking to OpenRouter: {e}") from e
            time.sleep(delay)
            delay = min(delay * 2, 20)
            continue
        if resp.status_code not in RETRY_STATUSES or attempt == attempts - 1:
            return resp
        last = resp
        retry_after = resp.headers.get("Retry-After")
        wait = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else delay
        time.sleep(min(wait, 30))
        delay = min(delay * 2, 20)
    assert last is not None
    return last


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def extract_json(text: str) -> dict:
    """Parse a JSON object out of a model reply, tolerating code fences and leading prose."""
    cleaned = _FENCE.sub("", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        return json.loads(cleaned[start:end + 1])
    raise LLMError(f"model did not return JSON: {text[:200]!r}")
