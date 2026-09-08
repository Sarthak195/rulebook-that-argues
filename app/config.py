"""Runtime configuration, read once from the environment (.env is loaded by app.main)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORPUS_DIR = Path(os.getenv("CORPUS_DIR", ROOT / "corpus"))
INDEX_DIR = Path(os.getenv("INDEX_DIR", ROOT / "index"))


def _list(name: str, default: str) -> list[str]:
    return [m.strip() for m in os.getenv(name, default).split(",") if m.strip()]


def _keys(name: str) -> list[str]:
    """Every provider accepts several keys: X_API_KEYS (comma-separated), or numbered lines
    X_API_KEY1, X_API_KEY2, ... , as well as the single X_API_KEY. Each key is its own quota; the
    spread pool rotates across keys and models. Duplicates are dropped, order kept."""
    found = _list(f"{name}_API_KEYS", "")
    for n in range(1, 51):
        v = os.getenv(f"{name}_API_KEY{n}", "").strip()
        if v:
            found.append(v)
    one = os.getenv(f"{name}_API_KEY", "").strip()
    if one:
        found.append(one)
    return list(dict.fromkeys(found))


# ---- LLM providers ---------------------------------------------------------------------------
# Every provider speaks the OpenAI chat-completions dialect. A call walks PROVIDER_ORDER and,
# within each provider, its model list, skipping providers without a key and models that were
# recently seen dead or rate-limited (see app.llm). All defaults are free tiers:
#   OpenRouter  ":free" models; 50 requests/day on a free-tier key, 1,000/day once $10 credits exist
#   Groq        free tier, generous per-day limits, fast; key from https://console.groq.com/keys
#   Gemini      free tier via Google AI Studio; key from https://aistudio.google.com/apikey
PROVIDER_ORDER = _list("PROVIDER_ORDER", "codecraft,groq,gemini,openrouter")
# Spread mode (batch jobs, the evaluation tab): rotate across the live models of these providers
# instead of always taking the first, because every model has its own per-minute token bucket.
# Add openrouter here to use its models as well; on a free-tier key that is 50 requests a day.
SPREAD_PROVIDERS = _list("SPREAD_PROVIDERS", "groq,gemini")
# Whether batch calls may fall through to the other providers once the spread pool has been
# unavailable for SPREAD_MAX_WAIT. Off by default: the fallbacks' small daily quotas are for
# live questions, and a failed row in a batch is cheaper than a dead demo.
SPREAD_FALLBACK = os.getenv("SPREAD_FALLBACK", "0").strip() in {"1", "true", "yes"}

# CodeCraft API (https://codecraftapi.com): a paid, OpenAI-compatible gateway to many models.
# Keys look like cc_ followed by 48 characters.
CODECRAFT_API_KEY = os.getenv("CODECRAFT_API_KEY", "").strip()
CODECRAFT_API_KEYS = _keys("CODECRAFT")
CODECRAFT_URL = os.getenv("CODECRAFT_URL", "https://codecraftapi.com/v1/chat/completions").strip()
CODECRAFT_MODELS = _list("CODECRAFT_MODELS", "deepseek-v4-flash-0731,gpt-5.6-luna,gemini-3.7-flash")
# Seconds to wait for one response, per provider. CodeCraft queued 35-50 s per request during
# its recovery on 8 Sep; the default 60 s would have timed out real questions.
PROVIDER_TIMEOUTS = {"codecraft": float(os.getenv("CODECRAFT_TIMEOUT", "150")), "openrouter": 90.0, "groq": 60.0, "gemini": 60.0}

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_API_KEYS = _keys("OPENROUTER")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Probed 8 Sep 2026 (scripts/probe_models.py) after minimax-m3:free was withdrawn:
#   nvidia/nemotron-3-super-120b-a12b:free  4/4, JSON, 3-30 s      <- primary
#   poolside/laguna-s-2.1:free              4/4, 6-12 s
#   google/gemma-4-31b-it:free              good when not rate-limited upstream
#   inclusionai/ling-3.0-flash-sante:free   fast, occasionally malformed JSON (retried)
# The "openrouter/free" router is deliberately not used: it can hand a question to a
# safety-classifier model that never returns JSON.
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free").strip()
OPENROUTER_FALLBACKS = _list(
    "OPENROUTER_FALLBACKS",
    "poolside/laguna-s-2.1:free,google/gemma-4-31b-it:free,inclusionai/ling-3.0-flash-sante:free,"
    "dots-studio/dots-3-note-preview:free,google/gemma-4-26b-a4b-it:free",
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_API_KEYS = _keys("GROQ")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Probed 8 Sep 2026 on the free tier: all three 4/4 on the response-type probe;
# gpt-oss-120b answers in 1.4-2.0 s, gpt-oss-20b in 1-2 s, qwen3.8-27b in 1-7 s.
GROQ_MODELS = _list("GROQ_MODELS", "openai/gpt-oss-120b,openai/gpt-oss-20b,qwen/qwen3.8-27b")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_API_KEYS = _keys("GEMINI")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
# Probed 8 Sep 2026 on free AI Studio keys. New projects cannot use gemini-2.5-flash ("no longer
# available to new users"); gemini-3.5-flash-lite and gemini-flash-lite-latest score 4/4 at
# 1.5-3 s on every key, gemini-2.5-flash 4/4 at 3.6-5.6 s on an older project, gemini-3.6-flash
# 3/4 at 20-55 s, gemini-3.8-flash hits quota after two answers. Order: fast and universal first.
GEMINI_MODELS = _list("GEMINI_MODELS", "gemini-3.5-flash-lite,gemini-2.5-flash,gemini-flash-lite-latest")

# The audit judges ~50-200 clause pairs in one batch; it may pin a different OpenRouter model
# than the one that answers live questions. Empty means "same chain as everything else".
AUDIT_MODEL = os.getenv("AUDIT_MODEL", "").strip()

# ---- embeddings and retrieval -----------------------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
# bge models are trained with this instruction on the query side only.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

TOP_K = int(os.getenv("TOP_K", "6"))
# Second, narrower LLM call on every "answered": do the cited passages explicitly govern this
# situation, or a neighbouring one? Costs one extra call; set VERIFY_ANSWERS=0 to disable.
VERIFY_ANSWERS = os.getenv("VERIFY_ANSWERS", "1").strip() not in {"0", "false", "no"}
# Measured on this corpus with bge-small: off-topic questions ("capital of France") peak at ~0.44,
# the weakest genuinely-covered question scores ~0.55. Adjacent-but-unanswered questions score
# 0.55-0.75, so the gate cannot catch them; that is the LLM's job.
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.45"))

INSTITUTE = "Shivalik Institute of Technology, Indore"
