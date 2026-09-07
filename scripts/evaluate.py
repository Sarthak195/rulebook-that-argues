"""Run the labelled test set through the pipeline and grade it.

    python scripts/evaluate.py                 # all 47 questions
    python scripts/evaluate.py --category not_covered
    python scripts/evaluate.py --workers 4

Grading rules (deliberately strict):
  answerable   status == answered  AND at least one expected section is cited
  conflict     status == conflict  AND every expected section is named in the conflict
  not_covered  status == not_covered

Writes results/eval_report.md (human) and results/eval_results.json (machine).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app import config  # noqa: E402
from app.pipeline import ask  # noqa: E402
from app.retriever import load_index  # noqa: E402

STATUSES = ["answered", "not_covered", "conflict"]
EXPECTED = {"answerable": "answered", "conflict": "conflict", "not_covered": "not_covered"}


def grade(category: str, item: dict, resp) -> tuple[bool, str]:
    exp = EXPECTED[category]
    if resp.status != exp:
        return False, f"status {resp.status} != {exp}"
    if category == "answerable":
        hit = [s for s in item["expected_sections"] if s in resp.citations]
        return (True, f"cited {hit}") if hit else (False, f"cited {resp.citations}, expected one of {item['expected_sections']}")
    if category == "conflict":
        named = resp.conflict.sections if resp.conflict else []
        missing = [s for s in item["expected_sections"] if s not in named]
        return (True, f"named {named}") if not missing else (False, f"named {named}, missing {missing}")
    return True, "silent, as expected"


def run_one(retriever, category: str, item: dict) -> dict:
    t0 = time.time()
    try:
        resp = ask(item["question"], retriever)
        ok, why = grade(category, item, resp)
        retrieved = [p.id for p in resp.passages]
        expected = item.get("expected_sections", [])
        return {
            "id": item["id"], "category": category, "question": item["question"],
            "expected_status": EXPECTED[category], "status": resp.status, "pass": ok, "why": why,
            "citations": resp.citations, "conflict_sections": resp.conflict.sections if resp.conflict else [],
            "retrieved": retrieved, "top_similarity": resp.top_similarity,
            "retrieval_recall": (all(s in retrieved for s in expected) if expected else None),
            "answer": resp.answer, "mode": resp.mode, "notes": resp.validation_notes,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:  # keep going; one failure must not hide the rest
        return {"id": item["id"], "category": category, "question": item["question"],
                "expected_status": EXPECTED[category], "status": "error", "pass": False, "why": f"{type(e).__name__}: {e}",
                "citations": [], "conflict_sections": [], "retrieved": [], "top_similarity": 0.0,
                "retrieval_recall": None, "answer": "", "mode": "error", "notes": [], "latency_ms": int((time.time() - t0) * 1000)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", choices=list(EXPECTED), default=None)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="results/eval_report.md", help="markdown report path; JSON goes next to it")
    args = ap.parse_args()

    tests = json.loads((ROOT / "tests" / "questions.json").read_text(encoding="utf-8"))
    jobs = [(cat, item) for cat in EXPECTED if not args.category or cat == args.category for item in tests[cat]]
    if args.limit:
        jobs = jobs[: args.limit]

    retriever = load_index()
    retriever.embed_query("warm up")
    print(f"model: {config.OPENROUTER_MODEL} | embeddings: {config.EMBEDDING_MODEL} | top_k={config.TOP_K} "
          f"| gate={config.MIN_SIMILARITY} | {len(jobs)} questions\n")

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for res in ex.map(lambda j: run_one(retriever, *j), jobs):
            results.append(res)
            mark = "PASS" if res["pass"] else "FAIL"
            print(f"{mark} {res['id']}  {res['expected_status']:>11} -> {res['status']:<11} {res['why']}")

    # ---- summary -------------------------------------------------------------
    by_cat = {cat: [r for r in results if r["category"] == cat] for cat in EXPECTED}
    lines = ["# Evaluation report", "",
             f"Model `{config.OPENROUTER_MODEL}` via OpenRouter, embeddings `{config.EMBEDDING_MODEL}`, "
             f"top_k={config.TOP_K}, similarity gate={config.MIN_SIMILARITY}.", "",
             "| Category | Passed | Total | Accuracy |", "|---|---|---|---|"]
    total_pass = 0
    for cat, rs in by_cat.items():
        if not rs:
            continue
        p = sum(r["pass"] for r in rs)
        total_pass += p
        lines.append(f"| {cat} | {p} | {len(rs)} | {p / len(rs):.0%} |")
    lines.append(f"| **all** | **{total_pass}** | **{len(results)}** | **{total_pass / max(len(results), 1):.0%}** |")

    lines += ["", "## Confusion matrix (rows: expected, columns: predicted)", "",
              "| expected \\ predicted | answered | not_covered | conflict | error |", "|---|---|---|---|---|"]
    for exp in STATUSES:
        row = [r for r in results if r["expected_status"] == exp]
        if not row:
            continue
        counts = [sum(r["status"] == s for r in row) for s in STATUSES + ["error"]]
        lines.append(f"| {exp} | " + " | ".join(str(c) for c in counts) + " |")

    rec = [r for r in results if r["retrieval_recall"] is not None]
    if rec:
        lines += ["", f"Retrieval recall (every expected section inside the top-{config.TOP_K} passages): "
                      f"{sum(r['retrieval_recall'] for r in rec)}/{len(rec)}"]
    lat = sorted(r["latency_ms"] for r in results)
    lines += [f"Median latency {lat[len(lat) // 2]} ms, p90 {lat[int(len(lat) * 0.9) - 1]} ms.", "",
              "## Per question", "", "| id | expected | got | pass | detail |", "|---|---|---|---|---|"]
    for r in results:
        detail = r["why"].replace("|", "/")
        lines.append(f"| {r['id']} | {r['expected_status']} | {r['status']} | {'yes' if r['pass'] else 'NO'} | {detail} |")
    lines += ["", "## Failures in detail", ""]
    fails = [r for r in results if not r["pass"]]
    if not fails:
        lines.append("None.")
    for r in fails:
        lines += [f"### {r['id']}: {r['question']}", "", f"- expected `{r['expected_status']}`, got `{r['status']}` ({r['why']})",
                  f"- retrieved: {', '.join(r['retrieved'])}", f"- answer: {r['answer']}", ""]

    out_md = ROOT / args.out
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json = out_md.with_name(out_md.stem.replace("report", "results") + ".json") if "report" in out_md.stem else out_md.with_suffix(".json")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n" + "\n".join(lines[4: 4 + len(by_cat) + 3]))
    print(f"\nwrote {out_md.relative_to(ROOT)} and {out_json.relative_to(ROOT)}")
    return 0 if total_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
