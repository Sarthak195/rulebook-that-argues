"""Whole-corpus contradiction audit.

The /ask endpoint finds a conflict only when somebody asks the right question. This module
does the thing the brief says nobody does: it reads every section against every other section
at once. Candidate pairs are picked by embedding similarity (contradictions are, by definition,
about the same topic, so they sit close together), then an LLM judges each pair. Results are
cached to results/conflict_audit.json and served by GET /audit.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import config, llm
from .retriever import Retriever

AUDIT_PATH = config.ROOT / "results" / "conflict_audit.json"

JUDGE_PROMPT = """You are auditing a university rulebook for internal contradictions. You will be shown two clauses from different parts of the rulebook.

Decide whether the two clauses give INCOMPATIBLE rules for the SAME situation. A contradiction means: different numbers, percentages, thresholds, deadlines or amounts for the same thing; or one clause permits what the other prohibits; or one imposes a condition the other says does not apply.

The following are NOT contradictions: clauses that agree or restate each other; clauses about different situations, different fee components, different categories of people, or different aspects of one topic; a general rule alongside a more specific procedure; a clause that lets an authority relax, waive or interpret a rule; a cross-reference to another document; clauses that merely use different wording for the same rule.

Reply with one JSON object only:
{"conflict": true or false,
 "topic": "short noun phrase naming what the rule is about",
 "explanation": "one or two sentences quoting the incompatible parts, or saying why they are compatible",
 "confidence": number between 0 and 1}"""


def candidate_pairs(r: Retriever, threshold: float, max_pairs: int, cross_document_only: bool) -> list[tuple[int, int, float]]:
    sims = r.emb @ r.emb.T
    n = len(r.chunks)
    pairs: list[tuple[int, int, float]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if cross_document_only and r.chunks[i].doc_code == r.chunks[j].doc_code:
                continue
            s = float(sims[i, j])
            if s >= threshold:
                pairs.append((i, j, s))
    pairs.sort(key=lambda p: -p[2])
    return pairs[:max_pairs]


def judge_pair(r: Retriever, i: int, j: int, s: float) -> dict:
    a, b = r.chunks[i], r.chunks[j]
    user = (f"Clause 1 [{a.id}] {a.doc_title} > {a.parent_title} > {a.title}\n{a.text}\n\n"
            f"Clause 2 [{b.id}] {b.doc_title} > {b.parent_title} > {b.title}\n{b.text}")
    content, _ = llm.chat([{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": user}], max_tokens=400)
    data = llm.extract_json(content)
    return {
        "a_id": a.id, "b_id": b.id, "similarity": round(s, 4),
        "conflict": bool(data.get("conflict")), "topic": str(data.get("topic", "")).strip(),
        "explanation": str(data.get("explanation", "")).strip(),
        "confidence": float(data.get("confidence", 0) or 0),
    }


def run_audit(r: Retriever, *, threshold: float = 0.72, max_pairs: int = 120, cross_document_only: bool = False,
              workers: int = 4, log=print) -> dict:
    if not llm.available():
        raise llm.LLMError("OPENROUTER_API_KEY is not set; the audit needs the LLM judge")
    t0 = time.time()
    pairs = candidate_pairs(r, threshold, max_pairs, cross_document_only)
    log(f"{len(pairs)} candidate pairs at cosine >= {threshold} (cross-document only: {cross_document_only})")
    verdicts: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for k, v in enumerate(ex.map(lambda p: judge_pair(r, *p), pairs), 1):
            verdicts.append(v)
            if v["conflict"]:
                log(f"  CONFLICT {v['a_id']} vs {v['b_id']} ({v['similarity']:.2f}): {v['topic']}")
            if k % 20 == 0:
                log(f"  judged {k}/{len(pairs)}")
    by_id = r.by_id
    conflicts = []
    for v in sorted((v for v in verdicts if v["conflict"]), key=lambda v: -v["confidence"]):
        a, b = by_id[v["a_id"]], by_id[v["b_id"]]
        conflicts.append({
            **v,
            "a": {"id": a.id, "doc_title": a.doc_title, "path": a.label, "format": a.format, "text": a.text},
            "b": {"id": b.id, "doc_title": b.doc_title, "path": b.label, "format": b.format, "text": b.text},
        })
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": config.OPENROUTER_MODEL, "embedding_model": config.EMBEDDING_MODEL,
        "threshold": threshold, "cross_document_only": cross_document_only,
        "sections": len(r.chunks), "pairs_checked": len(pairs), "seconds": round(time.time() - t0, 1),
        "conflicts": conflicts,
        "cleared": [v for v in verdicts if not v["conflict"]],
    }
    AUDIT_PATH.parent.mkdir(exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"{len(conflicts)} conflicts found in {report['seconds']}s -> {AUDIT_PATH}")
    return report


def load_audit() -> dict | None:
    if AUDIT_PATH.exists():
        return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    return None


def write_markdown(report: dict, path: Path) -> None:
    lines = ["# Conflict audit", "",
             f"Generated {report['generated_at']} with `{report['model']}`; {report['sections']} sections, "
             f"{report['pairs_checked']} candidate pairs at cosine >= {report['threshold']}, "
             f"{len(report['conflicts'])} contradictions found in {report['seconds']}s.", ""]
    for k, c in enumerate(report["conflicts"], 1):
        lines += [f"## {k}. {c['topic']}  ({c['a_id']} vs {c['b_id']}, similarity {c['similarity']:.2f}, confidence {c['confidence']:.2f})", "",
                  f"**{c['a']['id']}** {c['a']['doc_title']} > {c['a']['path']} ({c['a']['format']})", "", f"> {c['a']['text']}", "",
                  f"**{c['b']['id']}** {c['b']['doc_title']} > {c['b']['path']} ({c['b']['format']})", "", f"> {c['b']['text']}", "",
                  f"{c['explanation']}", ""]
    lines += ["## Pairs checked and cleared", "", "| A | B | similarity | reason |", "|---|---|---|---|"]
    for v in report["cleared"]:
        lines.append(f"| {v['a_id']} | {v['b_id']} | {v['similarity']:.2f} | {v['explanation'].replace('|', '/')} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
