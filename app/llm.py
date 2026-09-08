"""LLM client: OpenAI-compatible chat completions across a chain of free providers and models.

Free models come and go on OpenRouter without notice (minimax-m3:free was withdrawn overnight
during this project), and free-tier keys have small daily quotas (50 requests/day without
credits). So a call is made against a chain: for each provider in config.PROVIDER_ORDER that
has a key, each of its models in order. A model that answers "unavailable", 401/402/403/404 is
parked for DEAD_TTL seconds; one that fails after its retries (429, 5xx, empty body) is parked
briefly. The concrete model that answered is returned in usage["model"].
"""
from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass

import httpx

from . import config


class LLMError(RuntimeError):
    pass


class ModelUnavailable(LLMError):
    """The model is gone, not free any more, or refuses this key: no point retrying it soon."""


@dataclass(frozen=True)
class Entry:
    provider: str
    model: str
    url: str
    key: str
    seed: bool  # whether the endpoint accepts a "seed" parameter

    @property
    def id(self) -> str:
        return self.model if self.provider == "openrouter" else f"{self.provider}/{self.model}"


def providers() -> dict[str, dict]:
    """Read from config on every call so tests and scripts can override values at runtime."""
    return {
        "codecraft": {"url": config.CODECRAFT_URL, "key": config.CODECRAFT_API_KEY, "seed": False, "models": config.CODECRAFT_MODELS},
        "openrouter": {"url": config.OPENROUTER_URL, "key": config.OPENROUTER_API_KEY, "seed": True,
                       "models": [config.OPENROUTER_MODEL] + [m for m in config.OPENROUTER_FALLBACKS if m != config.OPENROUTER_MODEL]},
        "groq": {"url": config.GROQ_URL, "key": config.GROQ_API_KEY, "seed": True, "models": config.GROQ_MODELS},
        "gemini": {"url": config.GEMINI_URL, "key": config.GEMINI_API_KEY, "seed": False, "models": config.GEMINI_MODELS},
    }


def available() -> bool:
    return any(p["key"] for p in providers().values())


_dead: dict[str, float] = {}
_quota: dict[str, dict] = {}
DEAD_TTL = 600.0     # withdrawn / unauthorised: do not bother it for ten minutes
SICK_TTL = 90.0      # failed after retries (5xx, empty bodies)
LIMITED_TTL = 20.0   # 429 after retries: per-minute limits clear quickly, try again soon

# Free tiers limit requests per minute per provider. A burst of parallel questions (the
# evaluation tab, a batch script) must queue here rather than turn into 429s, retries and
# parked models. Two in flight per provider is enough to keep a demo snappy.
MAX_IN_FLIGHT = int(config.__dict__.get("MAX_IN_FLIGHT", 2))
_gates: dict[str, threading.Semaphore] = {}
_gates_lock = threading.Lock()


def _gate(provider: str) -> threading.Semaphore:
    with _gates_lock:
        if provider not in _gates:
            _gates[provider] = threading.Semaphore(MAX_IN_FLIGHT)
        return _gates[provider]


def full_chain(primary: str | None = None) -> list[Entry]:
    """Every configured (provider, model) in order. `primary`, if given, is an OpenRouter model
    id to try before the rest of that provider's list (used by the audit's AUDIT_MODEL)."""
    out: list[Entry] = []
    table = providers()
    for name in config.PROVIDER_ORDER:
        p = table.get(name)
        if not p or not p["key"]:
            continue
        models = list(p["models"])
        if primary and name == "openrouter":
            models = [primary] + [m for m in models if m != primary]
        out.extend(Entry(name, m, p["url"], p["key"], p["seed"]) for m in models)
    return out


def model_chain(primary: str | None = None) -> list[Entry]:
    """The chain minus entries parked as dead or sick; if everything is parked, try everything."""
    chain = full_chain(primary)
    now = time.time()
    live = [e for e in chain if _dead.get(e.id, 0.0) <= now]
    return live or chain


def park(model_id: str | None, ttl: float = SICK_TTL) -> None:
    """Skip a model for a while, e.g. after it returned unparseable JSON."""
    if model_id:
        _dead[model_id] = time.time() + ttl


def model_status() -> dict:
    now = time.time()
    return {e.id: ("parked" if _dead.get(e.id, 0.0) > now else "live") for e in full_chain()}


def quota_status() -> dict:
    """Last rate-limit headers seen per provider (OpenRouter: x-ratelimit-limit/remaining/reset)."""
    return dict(_quota)


def chat(messages: list[dict], *, model: str | None = None, temperature: float = 0.0,
         max_tokens: int = 900, json_mode: bool = True, timeout: float = 60.0) -> tuple[str, dict]:
    """Return (content, usage). Tries the chain in order. Raises LLMError when all fail."""
    if not available():
        raise LLMError("no LLM provider key is set (CODECRAFT_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY or GEMINI_API_KEY)")
    errors: list[str] = []
    for entry in model_chain(model):
        try:
            with _gate(entry.provider):
                return _chat_once(messages, entry, temperature=temperature, max_tokens=max_tokens,
                                  json_mode=json_mode, timeout=timeout)
        except ModelUnavailable as e:
            _dead[entry.id] = time.time() + DEAD_TTL
            errors.append(f"{entry.id}: {e}")
        except LLMError as e:
            limited = "429" in str(e)
            _dead[entry.id] = time.time() + (LIMITED_TTL if limited else SICK_TTL)
            errors.append(f"{entry.id}: {e}")
    raise LLMError("every model in the chain failed -> " + " | ".join(errors)[:700])


UNAVAILABLE_HINTS = ("unavailable", "not found", "no endpoints", "not a valid model", "does not exist",
                     "insufficient credits", "key limit", "payment required", "invalid api key",
                     "api key not valid", "unauthorized", "only available on")
RETRY_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}


def _chat_once(messages: list[dict], entry: Entry, *, temperature: float, max_tokens: int,
               json_mode: bool, timeout: float) -> tuple[str, dict]:
    payload: dict = {"model": entry.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if entry.seed:
        payload["seed"] = 7  # honoured by some providers; harmless elsewhere
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {entry.key}",
        "HTTP-Referer": "https://github.com/Sarthak195/rulebook-that-argues",
        "X-Title": "The Rulebook That Argues With Itself",
        "Content-Type": "application/json",
    }
    last_err = "no attempts made"
    for attempt in range(3):
        resp = _post_with_retries(entry, payload, headers, timeout)
        if resp.status_code != 200 and json_mode and resp.status_code in (400, 422):
            # Some models reject response_format; retry without it and rely on the prompt.
            payload.pop("response_format", None)
            json_mode = False
            resp = _post_with_retries(entry, payload, headers, timeout)
        if resp.status_code != 200:
            body = resp.text[:300]
            if resp.status_code in (401, 402, 403, 404) or any(h in body.lower() for h in UNAVAILABLE_HINTS):
                raise ModelUnavailable(f"HTTP {resp.status_code}: {body}")
            raise LLMError(f"HTTP {resp.status_code}: {body}")
        try:
            data = resp.json()
        except ValueError:
            data = {"error": {"message": f"non-JSON body: {resp.text[:120]}"}}
        choices = data.get("choices") or []
        content = ((choices[0].get("message") or {}).get("content") if choices else None) or ""
        if content.strip():
            usage = data.get("usage", {}) or {}
            usage["model"] = entry.id
            usage["served_by"] = data.get("model")
            return content, usage
        # Free-tier providers sometimes return HTTP 200 with {"error": {...}} or an empty
        # completion ("Provider returned error"). Treat both as transient.
        err_text = json.dumps(data.get("error") or "empty completion")[:300]
        if any(h in err_text.lower() for h in UNAVAILABLE_HINTS):
            raise ModelUnavailable(err_text)
        last_err = f"provider error: {err_text}"
        time.sleep(2.0 * (attempt + 1))
    raise LLMError(last_err)


def _remember_quota(entry: Entry, resp: httpx.Response) -> None:
    rl = {k.lower(): v for k, v in resp.headers.items() if k.lower().startswith("x-ratelimit")}
    if rl:
        rl["seen_at"] = int(time.time())
        rl["model"] = entry.id
        _quota[entry.provider] = rl


def _post_with_retries(entry: Entry, payload: dict, headers: dict, timeout: float, attempts: int = 5) -> httpx.Response:
    """Free tiers rate-limit aggressively; back off instead of failing the question. A daily
    quota (OpenRouter's free-models-per-day) is not worth waiting for: give up at once."""
    delay = 2.0
    last: httpx.Response | None = None
    for attempt in range(attempts):
        try:
            resp = httpx.post(entry.url, json=payload, headers=headers, timeout=timeout)
        except httpx.HTTPError as e:
            if attempt == attempts - 1:
                raise LLMError(f"network error talking to {entry.provider}: {e}") from e
            time.sleep(delay)
            delay = min(delay * 2, 20)
            continue
        _remember_quota(entry, resp)
        if resp.status_code == 429 and "per-day" in resp.text:
            return resp
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
