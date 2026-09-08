"""Runtime configuration, read once from the environment (.env is loaded by app.main)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORPUS_DIR = Path(os.getenv("CORPUS_DIR", ROOT / "corpus"))
INDEX_DIR = Path(os.getenv("INDEX_DIR", ROOT / "index"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
# Free models only by default. Measured on the test set: minimax/minimax-m3:free answers in ~2 s
# with reliable JSON. The "openrouter/free" router is deliberately not used: it can hand a
# question to a safety-classifier model that never returns JSON.
# Probed 8 Sep 2026 (scripts/probe_models.py) after minimax-m3:free was withdrawn:
#   nvidia/nemotron-3-super-120b-a12b:free  4/4, JSON, 3-30 s      <- primary
#   poolside/laguna-s-2.1:free              4/4, 6-12 s
#   google/gemma-4-31b-it:free              good when not rate-limited upstream
#   inclusionai/ling-3.0-flash-sante:free   fast, occasionally malformed JSON (retried)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free").strip()
# Tried in order when the primary is withdrawn, rate-limited or overloaded. Free models appear
# and disappear on OpenRouter without notice; keep several here. Comma-separated in the env.
OPENROUTER_FALLBACKS = [m.strip() for m in os.getenv(
    "OPENROUTER_FALLBACKS",
    "poolside/laguna-s-2.1:free,google/gemma-4-31b-it:free,inclusionai/ling-3.0-flash-sante:free,"
    "dots-studio/dots-3-note-preview:free,google/gemma-4-26b-a4b-it:free",
).split(",") if m.strip()]
# The audit judges ~100-200 clause pairs in one batch; it may use a different (cheaper or
# stronger) model than the one that answers live questions.
AUDIT_MODEL = os.getenv("AUDIT_MODEL", "").strip() or OPENROUTER_MODEL
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
# bge models are trained with this instruction on the query side only.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

TOP_K = int(os.getenv("TOP_K", "6"))
# Second, narrower LLM call on every "answered": do the cited passages explicitly govern this
# situation, or a neighbouring one? Costs one extra call; set VERIFY_ANSWERS=0 to disable.
VERIFY_ANSWERS = os.getenv("VERIFY_ANSWERS", "1").strip() not in {"0", "false", "no"}
# Below this best-passage cosine similarity we do not even ask the LLM: the corpus is silent.
# Measured on this corpus with bge-small: off-topic questions ("capital of France") peak at ~0.44,
# the weakest genuinely-covered question scores ~0.55. Adjacent-but-unanswered questions score
# 0.55-0.75, so the gate cannot catch them; that is the LLM's job.
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.45"))

INSTITUTE = "Shivalik Institute of Technology, Indore"
