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


class RateLimited(LLMError):
    """A 429 whose wait is not worth sitting through (a daily cap, or a long refill). Carries the
    provider's stated wait so the caller can park the model for exactly that long."""

    def __init__(self, message: str, wait: float):
        super().__init__(message)
        self.wait = wait


_TRY_AGAIN_RE = re.compile(r"(?:try again|retry) in ([0-9hms.]+)", re.IGNORECASE)  # Groq and Gemini wordings
DAILY_HINTS = ("per day", "per-day", "tpd", "rpd", "daily")
MAX_PARK = 900.0  # never park longer than fifteen minutes on a single message


def stated_wait(resp) -> float | None:
    """Seconds the provider asks us to wait, from Retry-After or a 'try again in 9m43.6s' body."""
    ra = resp.headers.get("retry-after")
    if ra and ra.replace(".", "", 1).isdigit():
        return float(ra)
    m = _TRY_AGAIN_RE.search(resp.text or "")
    return parse_duration(m.group(1)) if m else None


@dataclass(frozen=True)
class Entry:
    provider: str
    model: str
    url: str
    key: str
    seed: bool      # whether the endpoint accepts a "seed" parameter
    slot: int = 0   # which of the provider's keys; each key is its own quota
    nkeys: int = 1

    @property
    def account(self) -> str:
        """Provider plus key slot: the unit that rate limits apply to."""
        return self.provider if self.nkeys == 1 else f"{self.provider}#{self.slot + 1}"

    @property
    def id(self) -> str:
        if self.provider == "openrouter" and self.nkeys == 1:
            return self.model
        return f"{self.account}/{self.model}"


def _keys_for(provider: str) -> list[str]:
    """Prefer the *_API_KEYS list; fall back to the single *_API_KEY (tests set the latter)."""
    many = getattr(config, f"{provider.upper()}_API_KEYS", None) or []
    one = getattr(config, f"{provider.upper()}_API_KEY", "") or ""
    keys = [k for k in many if k] or ([one] if one else [])
    return keys


def providers() -> dict[str, dict]:
    """Read from config on every call so tests and scripts can override values at runtime."""
    return {
        "codecraft": {"url": config.CODECRAFT_URL, "keys": _keys_for("codecraft"), "seed": False, "models": config.CODECRAFT_MODELS},
        "openrouter": {"url": config.OPENROUTER_URL, "keys": _keys_for("openrouter"), "seed": True,
                       "models": [config.OPENROUTER_MODEL] + [m for m in config.OPENROUTER_FALLBACKS if m != config.OPENROUTER_MODEL]},
        "groq": {"url": config.GROQ_URL, "keys": _keys_for("groq"), "seed": True, "models": config.GROQ_MODELS},
        "gemini": {"url": config.GEMINI_URL, "keys": _keys_for("gemini"), "seed": False, "models": config.GEMINI_MODELS},
    }


def available() -> bool:
    return any(p["keys"] for p in providers().values())


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
_gates_lock = threading.Lock()


def spread_slots() -> int:
    """Distinct quota slots (provider#key) among the spread providers."""
    seen = set()
    for name in config.PROVIDER_ORDER:
        if name in config.SPREAD_PROVIDERS:
            for i, _ in enumerate(providers().get(name, {}).get("keys", [])):
                seen.add((name, i))
    return len(seen)


def batch_concurrency() -> int:
    """How many batch calls may be in flight at once: two per quota slot, capped at eight, and
    never more than leaves a slot free for live questions on a single-key setup."""
    return max(MAX_BATCH_IN_FLIGHT, min(8, 2 * spread_slots()))


_batch_gate = threading.Semaphore(batch_concurrency())


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
        if not p or not p["keys"]:
            continue
        models = list(p["models"])
        if primary and name == "openrouter":
            models = [primary] + [m for m in models if m != primary]
        keys = p["keys"]
        # Model-major order: the preferred model on every key comes before any fallback model,
        # so a second key extends quota without lowering quality.
        out.extend(Entry(name, m, p["url"], k, p["seed"], slot=i, nkeys=len(keys))
                   for m in models for i, k in enumerate(keys))
    return out


def model_chain(primary: str | None = None) -> list[Entry]:
    """The chain minus entries parked as dead or sick; if everything is parked, try everything."""
    chain = full_chain(primary)
    now = time.time()
    live = [e for e in chain if _dead.get(e.id, 0.0) <= now]
    return live or chain


def park(model_id: str | None, ttl: float = SICK_TTL, model_wide: bool = False) -> None:
    """Skip a model for a while, e.g. after it returned unparseable JSON. JSON discipline is a
    property of the model, not of the key, so model_wide parks the same model on every key."""
    if not model_id:
        return
    until = time.time() + ttl
    _dead[model_id] = until
    if model_wide:
        model = model_id.split("/", 1)[-1] if "/" in model_id else model_id
        for e in full_chain():
            if e.model == model or e.id.endswith("/" + model):
                _dead[e.id] = until


def model_status() -> dict:
    now = time.time()
    return {e.id: ("parked" if _dead.get(e.id, 0.0) > now else "live") for e in full_chain()}


def quota_status() -> dict:
    """Last rate-limit headers seen per provider, plus per-model token buckets where known."""
    now = time.time()
    out = dict(_quota)
    out["buckets"] = {mid: {"remaining_tokens": b["remaining"], "refills_in_s": max(0, round(b["reset_at"] - now, 1))}
                      for mid, b in _bucket.items()}
    return out


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

    global _interactive_pending
    if spread:
        # Batch work stays inside its own pool: rotate over the live pool models that still have
        # a call's worth of tokens in their minute bucket; if none has, wait for the earliest
        # refill (seconds) instead of firing at a drained model and sleeping on the 429, and
        # never spill onto the fallback providers and their small daily quotas. A live question
        # waiting anywhere pauses batch work.
        deadline = time.time() + SPREAD_MAX_WAIT
        while True:
            _batch_yield_to_interactive(deadline)
            now = time.time()
            all_pool = [e for e in full_chain(model) if e.provider in config.SPREAD_PROVIDERS]
            if not all_pool:
                break
            live = [e for e in all_pool if _dead.get(e.id, 0.0) <= now]
            ready = [e for e in live if has_headroom(e)]
            if ready:
                k = next(_rr) % len(ready)
                for entry in ready[k:] + ready[:k]:
                    try:
                        return _try(messages, entry, spread=True, **kw)
                    except LLMError as e:
                        errors.append(f"{entry.id}: {e}")
            if time.time() >= deadline:
                break
            # If every pool model is parked until well past the deadline (a daily cap), waiting
            # is pointless: fall through to the failover chain now.
            if not live and min(_dead.get(e.id, 0.0) for e in all_pool) > deadline:
                break
            _wait_for_headroom(live or all_pool, deadline)
        if not config.SPREAD_FALLBACK:
            raise LLMError("spread pool unavailable for %ds and SPREAD_FALLBACK is off -> " % SPREAD_MAX_WAIT
                           + " | ".join(errors)[:600])

    with _pending_lock:
        _interactive_pending += 0 if spread else 1
    try:
        chain = [e for e in model_chain(model) if not (spread and e.provider in config.SPREAD_PROVIDERS)]
        # A live question prefers the configured order, but a model whose bucket is known to be
        # drained is tried after its siblings with headroom: a two-second answer from the
        # second model beats a fifteen-second wait for the first.
        ordered = [e for e in chain if has_headroom(e)] + [e for e in chain if not has_headroom(e)]
        for entry in ordered:
            try:
                return _try(messages, entry, spread=spread, **kw)
            except LLMError as e:
                errors.append(f"{entry.id}: {e}")
    finally:
        with _pending_lock:
            _interactive_pending -= 0 if spread else 1
    if not errors:
        raise LLMError("no model to call: check PROVIDER_ORDER and the provider keys "
                       f"(configured: {[e.id for e in full_chain(model)] or 'nothing'})")
    raise LLMError("every model in the chain failed -> " + " | ".join(errors)[:700])


def _try(messages: list[dict], entry: Entry, *, spread: bool, **kw) -> tuple[str, dict]:
    """One model: call it, and on failure park it (or its whole provider) before re-raising."""
    gate = _Gates(_batch_gate, _gate(entry.account)) if spread else _Gates(_gate(entry.account))
    try:
        return _chat_once(messages, entry, gate=gate, spread=spread, **kw)
    except ModelUnavailable:
        _dead[entry.id] = time.time() + DEAD_TTL
        raise
    except RateLimited as e:
        # Park for exactly what the provider asked (capped), and mark the bucket empty until then
        # so routing skips this model without another request.
        until = time.time() + max(LIMITED_TTL, min(e.wait, MAX_PARK))
        _dead[entry.id] = until
        _bucket[entry.id] = {"remaining": 0, "reset_at": until}
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
               json_mode: bool, timeout: float, gate=None, spread: bool = False) -> tuple[str, dict]:
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
        resp = _post_with_retries(entry, payload, headers, timeout, gate, spread=spread)
        if resp.status_code != 200 and json_mode and resp.status_code in (400, 422):
            # Some models reject response_format; retry without it and rely on the prompt.
            payload.pop("response_format", None)
            json_mode = False
            resp = _post_with_retries(entry, payload, headers, timeout, gate, spread=spread)
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


_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")


def parse_duration(text: str | None) -> float | None:
    """Groq's reset headers look like '48.352s', '1m30.5s', '2h29m45.6s', '1ms'. Seconds out."""
    if not text:
        return None
    total, matched = 0.0, False
    for num, unit in _DURATION_RE.findall(text):
        matched = True
        total += float(num) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[unit]
    return total if matched else None


# Per-model token buckets as last reported by the provider (Groq sends remaining tokens and
# the time until the bucket refills on every response). Used to route around a drained model
# instead of firing at it and sleeping on the 429.
_bucket: dict[str, dict] = {}
TOKENS_PER_CALL = 2600   # a question with six passages is ~2,000-2,500 tokens in and out
_interactive_pending = 0
_pending_lock = threading.Lock()

# Last 300 provider requests, newest last: what was called, what came back, how long it took.
# GET /llmlog serves it. This is how "why is it slow" gets answered with facts.
_events: list[dict] = []
_events_lock = threading.Lock()


def _log_event(entry: Entry, *, status, ms: int, note: str = "", spread: bool = False) -> None:
    with _events_lock:
        _events.append({"t": round(time.time(), 1), "model": entry.id, "status": status, "ms": ms,
                        "spread": spread, "note": " ".join(note.split())[:400]})
        del _events[:-300]


def recent_events(n: int = 100) -> list[dict]:
    with _events_lock:
        return list(_events[-n:])


def _remember_quota(entry: Entry, resp: httpx.Response) -> None:
    rl = {k.lower(): v for k, v in resp.headers.items() if k.lower().startswith("x-ratelimit")}
    if not rl:
        return
    rl["seen_at"] = int(time.time())
    rl["model"] = entry.id
    _quota[entry.account] = rl
    rem = rl.get("x-ratelimit-remaining-tokens")
    reset = parse_duration(rl.get("x-ratelimit-reset-tokens"))
    if rem is not None and reset is not None:
        try:
            _bucket[entry.id] = {"remaining": int(float(rem)), "reset_at": time.time() + reset}
        except ValueError:
            pass


def has_headroom(entry: Entry, need: int = TOKENS_PER_CALL) -> bool:
    """False only when the provider told us this model's minute bucket is too low for one call
    and has not refilled yet. Unknown means yes."""
    b = _bucket.get(entry.id)
    if not b or b["reset_at"] <= time.time():
        return True
    return b["remaining"] >= need


def _wait_for_headroom(entries: list[Entry], deadline: float) -> None:
    """Sleep until some entry's bucket refills (or the deadline), in short steps."""
    resets = [b["reset_at"] for e in entries if (b := _bucket.get(e.id)) and b["reset_at"] > time.time()]
    wake = min(resets) if resets else time.time() + 1.0
    time.sleep(max(0.3, min(5.0, min(wake, deadline) - time.time())))


def _batch_yield_to_interactive(deadline: float) -> None:
    """Batch work pauses while a live question is waiting for a model."""
    while _interactive_pending > 0 and time.time() < deadline:
        time.sleep(0.3)


def _post_with_retries(entry: Entry, payload: dict, headers: dict, timeout: float, gate,
                       attempts: int = RATE_LIMIT_ATTEMPTS, spread: bool = False) -> httpx.Response:
    """Free tiers rate-limit aggressively; back off a little instead of failing the question,
    but only a little: a 429 gets at most `attempts` requests with waits capped at
    MAX_RETRY_WAIT, after which the caller parks this model and moves to the next. A daily
    quota (OpenRouter's free-models-per-day) and a gateway that is down (5xx) are not worth
    waiting for at all. The gate is held only while a request is in flight."""
    delay = 2.0
    last: httpx.Response | None = None
    server_errors = 0
    for attempt in range(attempts):
        t_wait = time.time()
        try:
            with gate:
                waited = int((time.time() - t_wait) * 1000)
                t0 = time.time()
                resp = httpx.post(entry.url, json=payload, headers=headers, timeout=timeout)
        except httpx.HTTPError as e:
            _log_event(entry, status="network", ms=int((time.time() - t_wait) * 1000), note=str(e), spread=spread)
            if attempt >= 1:
                raise LLMError(f"network error talking to {entry.provider}: {e}") from e
            time.sleep(delay)
            continue
        _log_event(entry, status=resp.status_code, ms=int((time.time() - t0) * 1000), spread=spread,
                   note=(f"waited {waited} ms for a slot; " if waited > 200 else "") +
                        (f"retry-after={resp.headers.get('retry-after')}; " if resp.status_code == 429 else "") +
                        (resp.text[:300] if resp.status_code != 200 else ""))
        _remember_quota(entry, resp)
        if resp.status_code == 429:
            wait = stated_wait(resp)
            body = (resp.text or "").lower()
            if any(h in body for h in DAILY_HINTS) or (wait is not None and wait > MAX_RETRY_WAIT):
                # A daily cap, or a refill minutes away: do not sit here and do not re-fire.
                raise RateLimited(f"HTTP 429: {resp.text[:300]}", wait if wait is not None else LIMITED_TTL)
        if resp.status_code >= 500:
            server_errors += 1
            if server_errors >= 2:
                return resp
            time.sleep(delay)
            continue
        if resp.status_code not in RETRY_STATUSES or attempt == attempts - 1:
            return resp
        last = resp
        wait = stated_wait(resp) if resp.status_code == 429 else None
        time.sleep(min(wait if wait is not None else delay, MAX_RETRY_WAIT))
        delay = min(delay * 2, MAX_RETRY_WAIT)
    assert last is not None
    return last


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_THINK = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> dict:
    """Parse a JSON object out of a model reply, tolerating code fences, a leading <think>
    block (Qwen 3.6 puts its reasoning in the content) and leading prose."""
    cleaned = _FENCE.sub("", _THINK.sub("", text.strip()).strip())
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
