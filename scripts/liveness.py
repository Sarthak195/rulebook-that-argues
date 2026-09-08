"""Quick liveness sweep of every model a provider lists: one tiny JSON call each, in parallel.

    python scripts/liveness.py codecraft            # every model from GET /models
    python scripts/liveness.py codecraft --workers 8 --timeout 45

Prints ok/fail, latency, the model the gateway reports it served, and price per million tokens.
This is a 10-second-per-model smoke test, not a quality probe; use probe_models.py for that.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app import config  # noqa: E402

PROVIDERS = {
    "codecraft": (config.CODECRAFT_URL, config.CODECRAFT_API_KEYS[0] if config.CODECRAFT_API_KEYS else ""),
    "openrouter": (config.OPENROUTER_URL, config.OPENROUTER_API_KEYS[0] if config.OPENROUTER_API_KEYS else ""),
    "groq": (config.GROQ_URL, config.GROQ_API_KEYS[0] if config.GROQ_API_KEYS else ""),
    "gemini": (config.GEMINI_URL, config.GEMINI_API_KEYS[0] if config.GEMINI_API_KEYS else ""),
}
for _name, _p in config.EXTRA_PROVIDERS.items():
    PROVIDERS[_name] = (_p["url"], _p["keys"][0] if _p["keys"] else "")


def list_models(url: str, key: str) -> list[dict]:
    base = url.rsplit("/chat/completions", 1)[0]
    r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("data", data) if isinstance(data, dict) else data


def ping(url: str, key: str, model: str, timeout: float) -> dict:
    t0 = time.time()
    # 160 tokens, not 20: reasoning models spend tokens thinking before the reply and come back
    # empty on a tiny budget, which would misreport a working model as dead.
    payload = {"model": model, "max_tokens": 160, "temperature": 0,
               "messages": [{"role": "user", "content": 'Reply with exactly this JSON and nothing else: {"ok": true}'}]}
    try:
        r = httpx.post(url, json=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, timeout=timeout)
        ms = int((time.time() - t0) * 1000)
        if r.status_code != 200:
            return {"model": model, "ok": False, "ms": ms, "note": f"HTTP {r.status_code}: {r.text[:100]}"}
        d = r.json()
        content = (((d.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        ok = '"ok"' in content and "true" in content
        return {"model": model, "ok": ok, "ms": ms, "served": d.get("model"), "note": "" if ok else f"reply: {content[:60]!r}"}
    except Exception as e:
        return {"model": model, "ok": False, "ms": int((time.time() - t0) * 1000), "note": f"{type(e).__name__}: {str(e)[:80]}"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("provider", choices=sorted(PROVIDERS))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=45.0)
    ap.add_argument("--only", nargs="*", help="model ids to test instead of the full list")
    args = ap.parse_args()
    url, key = PROVIDERS[args.provider]
    if not key:
        print(f"no key configured for {args.provider}")
        return 2
    try:
        models = list_models(url, key)
    except Exception as e:  # a gateway in trouble may not even list; fall back to what we know
        print(f"could not list models ({type(e).__name__}: {str(e)[:80]}); using --only or the configured list")
        fallback = {"codecraft": config.CODECRAFT_MODELS, "openrouter": [config.OPENROUTER_MODEL] + config.OPENROUTER_FALLBACKS,
                    "groq": config.GROQ_MODELS, "gemini": config.GEMINI_MODELS}.get(args.provider) or config.EXTRA_PROVIDERS.get(args.provider, {}).get("models", [])
        models = [{"id": m} for m in (args.only or fallback)]
    price = {}
    for m in models:
        p = m.get("pricing") or {}
        try:
            price[m["id"]] = float(p.get("prompt", 0)) * 1e6
        except (TypeError, ValueError):
            price[m["id"]] = None
    ids = args.only or [m["id"] for m in models]
    print(f"{args.provider}: pinging {len(ids)} models with {args.workers} workers, {args.timeout:.0f}s timeout\n")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(lambda mid: ping(url, key, mid, args.timeout), ids))
    results.sort(key=lambda r: (not r["ok"], price.get(r["model"]) or 0, r["ms"]))
    print(f"{'model':32} {'ok':4} {'ms':>7} {'$/M in':>8}  note")
    for r in results:
        pr = price.get(r["model"])
        print(f"{r['model']:32} {'ok' if r['ok'] else 'FAIL':4} {r['ms']:>7} {('%.2f' % pr) if pr is not None else '?':>8}  {r.get('note', '')}")
    ok = sum(r["ok"] for r in results)
    print(f"\n{ok}/{len(results)} models answered")
    (ROOT / "results" / f"liveness_{args.provider}.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
