"""LLM client: OpenAI-compatible chat completions across a chain of free providers and models.

Free models come and go on OpenRouter without notice (minimax-m3:free was withdrawn overnight
during this project), and free-tier keys have small daily quotas (50 requests/day without
credits). So a call is made against a chain: for each provider in config.PROVIDER_ORDER that
has a key, each of its models in order. A model that answers "unavailable", 401/402/403/404 is
parked for DEAD_TTL seconds; one that fails after its retries (429, 5xx, empty body) is parked
briefly. The concrete model that answered is returned in usage["model"].
"""
from __future__ import annotations

import itertools
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
# parked models. Three in flight per provider, of which batch work (spread=True) may hold at
# most two, so a live question asked while the evaluation runs always has a slot of its own.
MAX_IN_FLIGHT = 3
MAX_BATCH_IN_FLIGHT = 2
_gates: dict[str, threading.Semaphore] = {}
_batch_gate = threading.Semaphore(MAX_BATCH_IN_FLIGHT)
_gates_lock = threading.Lock()


def _gate(provider: str) -> threading.Semaphore:
    with _gates_lock:
        if provider not in _gates:
            _gates[provider] = threading.Semaphore(MAX_IN_FLIGHT)
        return _gates[provider]


class _Gates:
    """Acquire several semaphores in order, release in reverse. Held only around one HTTP
    request, never around a backoff sleep: a sleeping thread must not block the others."""

    def __init__(self, *sems: threading.Semaphore):
        self.sems = sems

    def __enter__(self):
        for s in self.sems:
            s.acquire()
        return self

    def __exit__(self, *a):
        for s in reversed(self.sems):
            s.release()
        return False


MAX_RETRY_WAIT = 15.0      # per 429 backoff; longer than this, park the model and try the next one
RATE_LIMIT_ATTEMPTS = 3    # requests per model per call before giving up on it for LIMITED_TTL
SPREAD_MAX_WAIT = 120.0    # batch calls wait this long for their own pool before touching fallbacks


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


_rr = itertools.count()


def spread_chain(primary: str | None = None) -> list[Entry]:
    """Chain for batch work: the live models of SPREAD_PROVIDERS rotated round-robin so that
    consecutive calls land on different per-minute token buckets, then everything else as
    failover. Falls back to the plain chain when no spread provider is live."""
    chain = model_chain(primary)
    pool = [e for e in chain if e.provider in config.SPREAD_PROVIDERS]
    if len(pool) < 2:
        return chain
    k = next(_rr) % len(pool)
    rotated = pool[k:] + pool[:k]
    return rotated + [e for e in chain if e not in pool]


def chat(messages: list[dict], *, model: str | None = None, temperature: float = 0.0,
         max_tokens: int = 900, json_mode: bool = True, timeout: float = 60.0,
         spread: bool = False) -> tuple[str, dict]:
    """Return (content, usage). Tries the chain in order (rotated across providers' models when
    spread=True). Raises LLMError when all fail."""
    if not available():
        raise LLMError("no LLM provider key is set (CODECRAFT_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY or GEMINI_API_KEY)")
    errors: list[str] = []
    kw = dict(temperature=temperature, max_tokens=max_tokens, json_mode=json_mode, timeout=timeout)

    if spread:
        # Batch work stays inside its own pool: rotate over the live pool models; if every one
        # is parked, wait for the earliest to unpark (they unpark within seconds) instead of
        # spilling onto the fallback providers and their small daily quotas.
        deadline = time.time() + SPREAD_MAX_WAIT
        while True:
            now = time.time()
            all_pool = [e for e in full_chain(model) if e.provider in config.SPREAD_PROVIDERS]
            if not all_pool:
                break
            live = [e for e in all_pool if _dead.get(e.id, 0.0) <= now]
            if live:
                k = next(_rr) % len(live)
                for entry in live[k:] + live[:k]:
                    try:
                        return _try(messages, entry, spread=True, **kw)
                    except LLMError as e:
                        errors.append(f"{entry.id}: {e}")
            if time.time() >= deadline:
                break
            wake = min(_dead.get(e.id, 0.0) for e in all_pool)
            time.sleep(max(0.5, min(5.0, wake - time.time())))

    for entry in model_chain(model):
        if spread and entry.provider in config.SPREAD_PROVIDERS:
            continue  # tried above
        try:
            return _try(messages, entry, spread=spread, **kw)
        except LLMError as e:
            errors.append(f"{entry.id}: {e}")
    raise LLMError("every model in the chain failed -> " + " | ".join(errors)[:700])


def _try(messages: list[dict], entry: Entry, *, spread: bool, **kw) -> tuple[str, dict]:
    """One model: call it, and on failure park it (or its whole provider) before re-raising."""
    gate = _Gates(_batch_gate, _gate(entry.provider)) if spread else _Gates(_gate(entry.provider))
    try:
        return _chat_once(messages, entry, gate=gate, **kw)
    except ModelUnavailable:
        _dead[entry.id] = time.time() + DEAD_TTL
        raise
    except LLMError as e:
        msg = str(e)
        if "429" in msg:
            _dead[entry.id] = time.time() + LIMITED_TTL
        elif msg.startswith("HTTP 5") or "network error" in msg:
            # A 5xx or a dead socket is the gateway, not the model: park every model of this
            # provider so the next call does not pay the same price three times.
            for other in full_chain():
                if other.provider == entry.provider:
                    _dead[other.id] = time.time() + SICK_TTL
        else:
            _dead[entry.id] = time.time() + SICK_TTL
        raise


UNAVAILABLE_HINTS = ("unavailable", "not found", "no endpoints", "not a valid model", "does not exist",
                     "insufficient credits", "key limit", "payment required", "invalid api key",
                     "api key not valid", "unauthorized", "only available on")
RETRY_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}


def _chat_once(messages: list[dict], entry: Entry, *, temperature: float, max_tokens: int,
               json_mode: bool, timeout: float, gate=None) -> tuple[str, dict]:
    gate = gate if gate is not None else _Gates()
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
        resp = _post_with_retries(entry, payload, headers, timeout, gate)
        if resp.status_code != 200 and json_mode and resp.status_code in (400, 422):
            # Some models reject response_format; retry without it and rely on the prompt.
            payload.pop("response_format", None)
            json_mode = False
            resp = _post_with_retries(entry, payload, headers, timeout, gate)
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


def _post_with_retries(entry: Entry, payload: dict, headers: dict, timeout: float, gate,
                       attempts: int = RATE_LIMIT_ATTEMPTS) -> httpx.Response:
    """Free tiers rate-limit aggressively; back off a little instead of failing the question,
    but only a little: a 429 gets at most `attempts` requests with waits capped at
    MAX_RETRY_WAIT, after which the caller parks this model and moves to the next. A daily
    quota (OpenRouter's free-models-per-day) and a gateway that is down (5xx) are not worth
    waiting for at all. The gate is held only while a request is in flight."""
    delay = 2.0
    last: httpx.Response | None = None
    server_errors = 0
    for attempt in range(attempts):
        try:
            with gate:
                resp = httpx.post(entry.url, json=payload, headers=headers, timeout=timeout)
        except httpx.HTTPError as e:
            if attempt >= 1:
                raise LLMError(f"network error talking to {entry.provider}: {e}") from e
            time.sleep(delay)
            continue
        _remember_quota(entry, resp)
        if resp.status_code == 429 and "per-day" in resp.text:
            return resp
        if resp.status_code >= 500:
            server_errors += 1
            if server_errors >= 2:
                return resp
            time.sleep(delay)
            continue
        if resp.status_code not in RETRY_STATUSES or attempt == attempts - 1:
            return resp
        last = resp
        retry_after = resp.headers.get("Retry-After")
        wait = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else delay
        time.sleep(min(wait, MAX_RETRY_WAIT))
        delay = min(delay * 2, MAX_RETRY_WAIT)
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
