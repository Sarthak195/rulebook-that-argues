"""Grading rules for the labelled test set, shared by scripts/evaluate.py and the in-app job.

  answerable   status == answered  AND at least one expected section is cited
  conflict     status == conflict  AND every expected section is named in the conflict
  not_covered  status == not_covered
"""
from __future__ import annotations

import json

from . import config
from .schemas import AskResponse

TESTS_PATH = config.ROOT / "tests" / "questions.json"
EXPECTED = {"answerable": "answered", "conflict": "conflict", "not_covered": "not_covered"}
STATUSES = ["answered", "not_covered", "conflict"]


def load_tests() -> dict:
    return json.loads(TESTS_PATH.read_text(encoding="utf-8"))


def jobs() -> list[tuple[str, dict]]:
    tests = load_tests()
    return [(cat, item) for cat in EXPECTED for item in tests.get(cat, [])]


def grade(category: str, item: dict, resp: AskResponse) -> tuple[bool, str]:
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


def summarise(rows: list[dict]) -> dict:
    """Per-category pass counts and the confusion matrix over graded rows."""
    graded = [r for r in rows if r.get("status") not in (None, "pending", "cancelled")]
    per_cat: dict[str, dict] = {}
    for r in rows:
        per_cat.setdefault(r["category"], {"passed": 0, "total": 0})
    for r in graded:
        per_cat[r["category"]]["total"] += 1
        per_cat[r["category"]]["passed"] += 1 if r.get("pass") else 0
    matrix = {e: {s: 0 for s in STATUSES + ["error"]} for e in STATUSES}
    for r in graded:
        got = r["status"] if r["status"] in STATUSES else "error"
        matrix[r["expected"]][got] += 1
    return {"passed": sum(1 for r in graded if r.get("pass")), "graded": len(graded), "total": len(rows),
            "per_category": per_cat, "matrix": matrix}
