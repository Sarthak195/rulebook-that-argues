"""Thin OpenRouter client (OpenAI-compatible chat completions) plus a tolerant JSON extractor."""
from __future__ import annotations

import json
import re

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
    try:
        resp = httpx.post(config.OPENROUTER_URL, json=payload, headers=headers, timeout=timeout)
    except httpx.HTTPError as e:
        raise LLMError(f"network error talking to OpenRouter: {e}") from e
    if resp.status_code != 200:
        # Some models reject response_format; retry once without it.
        if json_mode and resp.status_code in (400, 404, 422):
            payload.pop("response_format", None)
            resp = httpx.post(config.OPENROUTER_URL, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            raise LLMError(f"OpenRouter HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"unexpected OpenRouter response: {json.dumps(data)[:300]}") from e
    return content or "", data.get("usage", {})


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
