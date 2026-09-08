"""One tiny request per configured key of a provider: which keys still work?

    python scripts/keycheck.py gemini
    python scripts/keycheck.py groq

Prints the key's slot, a masked prefix, the HTTP status and the first line of any error.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app import config  # noqa: E402

PROVIDERS = {
    "gemini": (config.GEMINI_URL, config.GEMINI_API_KEYS, config.GEMINI_MODELS[0] if config.GEMINI_MODELS else "gemini-3.5-flash-lite"),
    "groq": (config.GROQ_URL, config.GROQ_API_KEYS, config.GROQ_MODELS[0] if config.GROQ_MODELS else ""),
    "openrouter": (config.OPENROUTER_URL, config.OPENROUTER_API_KEYS, config.OPENROUTER_MODEL),
    "codecraft": (config.CODECRAFT_URL, config.CODECRAFT_API_KEYS, config.CODECRAFT_MODELS[0] if config.CODECRAFT_MODELS else ""),
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    provider = sys.argv[1] if len(sys.argv) > 1 else "gemini"
    url, keys, model = PROVIDERS[provider]
    print(f"{provider}: {len(keys)} key(s), model {model}")
    alive = 0
    for i, k in enumerate(keys, 1):
        t0 = time.time()
        try:
            r = httpx.post(url, headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"}, timeout=40,
                           json={"model": model, "max_tokens": 20, "messages": [{"role": "user", "content": "Reply with the word ok"}]})
            text = " ".join(r.text.split())
            ok = r.status_code == 200 and '"content"' in text
            alive += ok
            print(f"  #{i:<2} {k[:6]}...{k[-4:]}  HTTP {r.status_code}  {int((time.time() - t0) * 1000):>5} ms  {'ok' if ok else text[:140]}")
        except Exception as e:
            print(f"  #{i:<2} {k[:6]}...{k[-4:]}  {type(e).__name__}: {str(e)[:100]}")
    print(f"{alive}/{len(keys)} keys answered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
