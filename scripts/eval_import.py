"""Load a finished batch run (scripts/evaluate.py output) into the Evaluation tab's state.

    python scripts/eval_import.py results/runs/run9.json
    python scripts/eval_import.py results/runs/run9.json --out /opt/rulebook/results/eval_live.json

Why this exists: the free tiers that answer questions cannot always afford a 65-call run on
demand (Groq caps each model at 200k tokens a day; OpenRouter at 50 requests a day on a free
key). The batch run went through exactly the same pipeline; showing it in the tab, labelled
"imported" with its source file and time, is honest and lets the tab still be useful when the
day's quota is gone. Starting a live run replaces it.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.grading import EXPECTED, summarise  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="a results/runs/*.json written by scripts/evaluate.py")
    ap.add_argument("--out", default=str(ROOT / "results" / "eval_live.json"))
    args = ap.parse_args()
    src = Path(args.source)
    results = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    for r in results:
        rows.append({
            "id": r["id"], "category": r["category"], "question": r["question"], "expected": EXPECTED[r["category"]],
            "status": r["status"], "pass": bool(r["pass"]), "why": r["why"], "citations": r.get("citations", []),
            "conflict_sections": r.get("conflict_sections", []), "answer": r.get("answer", ""),
            "model": r.get("model"), "notes": r.get("notes", []), "latency_ms": r.get("latency_ms", 0),
        })
    mtime = src.stat().st_mtime
    state = {
        "status": "imported", "started_at": mtime, "finished_at": mtime, "done": len(rows), "total": len(rows),
        "workers": 0, "spread": False, "rows": rows, "summary": summarise(rows),
        "source": f"{src.as_posix()} (batch run via scripts/evaluate.py, {time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime))})",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    s = state["summary"]
    print(f"imported {len(rows)} rows from {src}: {s['passed']}/{s['graded']} passed -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
