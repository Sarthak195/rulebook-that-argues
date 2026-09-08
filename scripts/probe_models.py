"""Try candidate models on one question of each response type.

    python scripts/probe_models.py google/gemma-4-31b-it:free nvidia/nemotron-3-super-120b-a12b:free
    python scripts/probe_models.py codecraft:deepseek-v4-flash-0731 groq:llama-3.3-70b-versatile

A bare id is an OpenRouter model; "provider:model" selects another configured provider
(codecraft, groq, gemini). Prints status, citations, latency and which model served the call.
Use it to pick a model before running the full evaluation; models differ a lot in JSON discipline.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app import config  # noqa: E402
from app.pipeline import ask  # noqa: E402
from app.retriever import load_index  # noqa: E402

PROBES = [
    ("conflict", "What CGPA do I need to maintain to keep my merit scholarship?"),
    ("not_covered", "What happens if I miss the end-semester exam because of a family wedding?"),
    ("answered", "What time do the hostel gates close at night?"),
    ("not_covered", "Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid?"),
]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    models = sys.argv[1:] or [config.OPENROUTER_MODEL]
    r = load_index(log=lambda *a: None)
    r.embed_query("warm up")
    config.OPENROUTER_FALLBACKS = []  # probe each model on its own; no failover while measuring
    for spec in models:
        provider, _, m = spec.partition(":") if ":" in spec and not spec.endswith(":free") else ("openrouter", "", spec)
        config.PROVIDER_ORDER = [provider]
        if provider == "openrouter":
            config.OPENROUTER_MODEL = m
        elif provider == "codecraft":
            config.CODECRAFT_MODELS = [m]
        elif provider == "groq":
            config.GROQ_MODELS = [m]
        elif provider == "gemini":
            config.GEMINI_MODELS = [m]
        elif provider in config.EXTRA_PROVIDERS:
            config.EXTRA_PROVIDERS[provider]["models"] = [m]
        else:
            print(f"\n=== {spec}: unknown provider {provider!r} (configure it via EXTRA_PROVIDERS)")
            continue
        print(f"\n=== {spec}", flush=True)
        score = 0
        for expected, q in PROBES:
            t0 = time.time()
            try:
                resp = ask(q, r)
                ok = resp.status == expected
                score += ok
                print(f"  {'ok ' if ok else 'BAD'} {expected:<12} -> {resp.status:<12} {resp.citations} "
                      f"{int((time.time() - t0) * 1000)} ms {('notes: ' + '; '.join(resp.validation_notes)) if resp.validation_notes else ''}")
            except Exception as e:
                print(f"  ERR {expected:<12} -> {type(e).__name__}: {str(e)[:160]}")
        print(f"  score {score}/{len(PROBES)}")


if __name__ == "__main__":
    main()
