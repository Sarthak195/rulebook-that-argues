"""Audit the whole corpus for contradictions and write results/conflict_audit.{json,md}.

    python scripts/audit.py                    # default: cosine >= 0.72, up to 120 pairs
    python scripts/audit.py --threshold 0.68 --max-pairs 200
    python scripts/audit.py --cross-document-only
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app.audit import run_audit, write_markdown  # noqa: E402
from app.retriever import load_index  # noqa: E402

PLANTED = {frozenset({"AR §4.3", "LM §2.2"}), frozenset({"FS §4.1", "SF §6.2"}), frozenset({"AR §11.2", "SF §3.1"})}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.72)
    ap.add_argument("--max-pairs", type=int, default=120)
    ap.add_argument("--cross-document-only", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    r = load_index()
    report = run_audit(r, threshold=args.threshold, max_pairs=args.max_pairs,
                       cross_document_only=args.cross_document_only, workers=args.workers)
    write_markdown(report, ROOT / "results" / "conflict_audit.md")

    found = {frozenset({c["a_id"], c["b_id"]}) for c in report["conflicts"]}
    hits = PLANTED & found
    extras = found - PLANTED
    print(f"\nplanted contradictions found: {len(hits)}/3")
    for p in PLANTED - found:
        print(f"  MISSED: {' vs '.join(sorted(p))}")
    print(f"other pairs flagged: {len(extras)} (review these by hand; some may be real)")
    for p in extras:
        print(f"  {' vs '.join(sorted(p))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
