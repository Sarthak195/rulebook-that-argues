"""The evaluation as a server-side job.

The Evaluation tab used to drive the 47 questions from the browser, so a page refresh killed
the run and orphaned the in-flight requests. Now the server owns the run: one job at a time,
progress written to results/eval_live.json after every row, and any page (or a later reload,
or a second device) re-attaches by polling GET /eval. The last finished run is shown until the
next one starts, which also means the video can open the tab and find the results already there.
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from . import config
from .grading import EXPECTED, grade, jobs, summarise
from .pipeline import ask

STATE_PATH = config.ROOT / "results" / "eval_live.json"

_lock = threading.Lock()
_cancel = threading.Event()
_state: dict = {"status": "idle", "started_at": None, "finished_at": None, "done": 0, "total": 0,
                "workers": 0, "spread": False, "rows": [], "summary": None}


def state() -> dict:
    with _lock:
        s = dict(_state)
        s["rows"] = [dict(r) for r in _state["rows"]]
        return s


def _save_locked() -> None:
    try:
        STATE_PATH.parent.mkdir(exist_ok=True)
        STATE_PATH.write_text(json.dumps(_state, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def load_saved() -> None:
    """On startup, show the last run; a run that was in progress when the server stopped is
    marked interrupted rather than left looking alive."""
    if not STATE_PATH.exists():
        return
    try:
        saved = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if saved.get("status") == "running":
        saved["status"] = "interrupted"
        saved["finished_at"] = saved.get("finished_at") or time.time()
    with _lock:
        _state.update(saved)


def start(retriever, workers: int = 3, spread: bool = True) -> dict:
    with _lock:
        if _state["status"] == "running":
            return state()
        todo = jobs()
        _state.update(status="running", started_at=time.time(), finished_at=None, done=0, total=len(todo),
                      workers=workers, spread=spread, summary=None,
                      rows=[{"id": it["id"], "category": cat, "question": it["question"], "expected": EXPECTED[cat],
                             "status": "pending"} for cat, it in todo])
        _cancel.clear()
        _save_locked()
    threading.Thread(target=_run, args=(retriever, todo, workers, spread), name="eval-job", daemon=True).start()
    return state()


def cancel() -> dict:
    _cancel.set()
    return state()


def _run(retriever, todo: list[tuple[str, dict]], workers: int, spread: bool) -> None:
    def one(indexed):
        idx, (cat, item) = indexed
        t0 = time.time()
        if _cancel.is_set():
            row = {"status": "cancelled", "pass": False, "why": "cancelled"}
        else:
            try:
                resp = ask(item["question"], retriever, spread=spread)
                ok, why = grade(cat, item, resp)
                row = {"status": resp.status, "pass": ok, "why": why, "citations": resp.citations,
                       "conflict_sections": resp.conflict.sections if resp.conflict else [],
                       "answer": resp.answer, "model": resp.model, "notes": resp.validation_notes}
            except Exception as e:  # one failure must not stop the run
                row = {"status": "error", "pass": False, "why": f"{type(e).__name__}: {str(e)[:300]}", "citations": [],
                       "conflict_sections": [], "answer": "", "model": None, "notes": []}
        row["latency_ms"] = int((time.time() - t0) * 1000)
        with _lock:
            _state["rows"][idx].update(row)
            _state["done"] += 1
            _state["summary"] = summarise(_state["rows"])
            _save_locked()

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, enumerate(todo)))
    with _lock:
        _state["status"] = "cancelled" if _cancel.is_set() else "done"
        _state["finished_at"] = time.time()
        _state["summary"] = summarise(_state["rows"])
        _save_locked()
