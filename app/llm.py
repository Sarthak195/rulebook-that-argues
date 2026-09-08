"""Thin OpenRouter client (OpenAI-compatible chat completions) plus a tolerant JSON extractor."""
from __future__ import annotations

import json
import re
import time

import httpx

from . import config


class LLMError(RuntimeError):
    pass


class ModelUnavailable(LLMError):
    """The model is gone, not free any more, or refuses this key: no point retrying it soon."""


def available() -> bool:
    return bool(config.OPENROUTER_API_KEY)


# Free models come and go on OpenRouter without notice (minimax-m3:free was withdrawn overnight
# during this project). So a call is made against a chain of models: the configured one first,
# then the fallbacks. A model that answers "unavailable" is parked for DEAD_TTL seconds; one that
# merely failed after retries is parked briefly. The concrete model used is returned in usage.
_dead: dict[str, float] = {}
DEAD_TTL = 600.0
SICK_TTL = 90.0


def full_chain(primary: str | None = None) -> list[str]:
    first = primary or config.OPENROUTER_MODEL
    return [first] + [m for m in config.OPENROUTER_FALLBACKS if m != first]


def model_chain(primary: str | None = None) -> list[str]:
    """The chain minus models parked as dead or sick; if everything is parked, try everything."""
    chain = full_chain(primary)
    now = time.time()
    live = [m for m in chain if _dead.get(m, 0.0) <= now]
    return live or chain


def park(model: str | None, ttl: float = SICK_TTL) -> None:
    """Skip a model for a while, e.g. after it returned unparseable JSON."""
    if model:
        _dead[model] = time.time() + ttl


def model_status() -> dict:
    now = time.time()
    return {m: ("parked" if _dead.get(m, 0.0) > now else "live") for m in full_chain()}


def chat(messages: list[dict], *, model: str | None = None, temperature: float = 0.0,
         max_tokens: int = 900, json_mode: bool = True, timeout: float = 60.0) -> tuple[str, dict]:
    """Return (content, usage). Tries the model chain in order. Raises LLMError when all fail."""
    if not available():
        raise LLMError("OPENROUTER_API_KEY is not set")
    errors: list[str] = []
    for m in model_chain(model):
        try:
            return _chat_once(messages, m, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode, timeout=timeout)
        except ModelUnavailable as e:
            _dead[m] = time.time() + DEAD_TTL
            errors.append(f"{m}: {e}")
        except LLMError as e:
            _dead[m] = time.time() + SICK_TTL
            errors.append(f"{m}: {e}")
    raise LLMError("every model in the chain failed -> " + " | ".join(errors)[:600])


UNAVAILABLE_HINTS = ("unavailable", "not found", "no endpoints", "not a valid model", "does not exist",
                     "insufficient credits", "key limit", "payment required")


def _chat_once(messages: list[dict], model: str, *, temperature: float, max_tokens: int,
               json_mode: bool, timeout: float) -> tuple[str, dict]:
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "seed": 7,  # honoured by some providers; harmless elsewhere
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/Sarthak195/rulebook-that-argues",
        "X-Title": "The Rulebook That Argues With Itself",
        "Content-Type": "application/json",
    }
    last_err = "no attempts made"
    for attempt in range(3):
        resp = _post_with_retries(payload, headers, timeout)
        if resp.status_code != 200 and json_mode and resp.status_code in (400, 422):
            # Some models reject response_format; retry without it and rely on the prompt.
            payload.pop("response_format", None)
            json_mode = False
            resp = _post_with_retries(payload, headers, timeout)
        if resp.status_code != 200:
            body = resp.text[:300]
            if resp.status_code in (402, 403, 404) or any(h in body.lower() for h in UNAVAILABLE_HINTS):
                raise ModelUnavailable(f"HTTP {resp.status_code}: {body}")
            raise LLMError(f"OpenRouter HTTP {resp.status_code}: {body}")
        try:
            data = resp.json()
        except ValueError:
            data = {"error": {"message": f"non-JSON body: {resp.text[:120]}"}}
        choices = data.get("choices") or []
        content = ((choices[0].get("message") or {}).get("content") if choices else None) or ""
        if content.strip():
            usage = data.get("usage", {}) or {}
            usage["model"] = data.get("model")  # the concrete model, useful when routing through openrouter/free
            return content, usage
        # Free-tier providers sometimes return HTTP 200 with {"error": {...}} or an empty
        # completion ("Provider returned error"). Treat both as transient.
        err_text = json.dumps(data.get("error") or "empty completion")[:300]
        if any(h in err_text.lower() for h in UNAVAILABLE_HINTS):
            raise ModelUnavailable(err_text)
        last_err = f"OpenRouter error: {err_text}"
        time.sleep(2.0 * (attempt + 1))
    raise LLMError(last_err)


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
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError as e:
            raise LLMError(f"model returned malformed JSON ({e.msg} at {e.pos}): {text[:200]!r}") from e
    raise LLMError(f"model did not return JSON: {text[:200]!r}")
