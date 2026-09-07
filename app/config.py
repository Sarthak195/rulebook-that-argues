"""Runtime configuration, read once from the environment (.env is loaded by app.main)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORPUS_DIR = Path(os.getenv("CORPUS_DIR", ROOT / "corpus"))
INDEX_DIR = Path(os.getenv("INDEX_DIR", ROOT / "index"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
# bge models are trained with this instruction on the query side only.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

TOP_K = int(os.getenv("TOP_K", "6"))
# Below this best-passage cosine similarity we do not even ask the LLM: the corpus is silent.
# Measured on this corpus with bge-small: off-topic questions ("capital of France") peak at ~0.44,
# the weakest genuinely-covered question scores ~0.55. Adjacent-but-unanswered questions score
# 0.55-0.75, so the gate cannot catch them; that is the LLM's job.
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.45"))

INSTITUTE = "Shivalik Institute of Technology, Indore"
