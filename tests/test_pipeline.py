"""Unit tests that need no API key: chunking, id normalisation, and the validator's downgrades.

    python -m pytest -q
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.chunking import load_corpus
from app.pipeline import normalise_ids

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def chunks():
    return load_corpus(ROOT / "corpus")


def test_corpus_parses_every_document(chunks):
    codes = {c.doc_code for c in chunks}
    assert codes == {"AR", "EE", "HH", "FS", "SF", "LM"}
    assert len(chunks) > 120
    assert sum(len(c.text.split()) for c in chunks) >= 6000


def test_pdf_and_tables_are_parsed(chunks):
    formats = {c.format for c in chunks}
    assert {"markdown", "pdf", "table"} <= formats
    by_id = {c.id: c for c in chunks}
    assert by_id["SF §6.2"].format == "pdf"
    assert by_id["FS §4.1"].format == "table" and "| 100 per cent |" in by_id["FS §4.1"].text


def test_planted_contradictions_exist_as_separate_sections(chunks):
    by_id = {c.id: c for c in chunks}
    assert "65 per cent" in by_id["AR §4.3"].text and "55 per cent" in by_id["LM §2.2"].text
    assert "100 per cent" in by_id["FS §4.1"].text and "ten per cent" in by_id["SF §6.2"].text
    assert "7.5" in by_id["AR §11.2"].text and "8.0" in by_id["SF §3.1"].text


def test_section_ids_are_unique(chunks):
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))


def test_normalise_ids_accepts_sloppy_model_output():
    valid = {"AR §4.3", "LM §2.2", "FS §4.1"}
    assert normalise_ids(["AR §4.3"], valid) == ["AR §4.3"]
    assert normalise_ids(["AR 4.3", "[LM §2.2]", "LM§2.2"], valid) == ["AR §4.3", "LM §2.2"]
    assert normalise_ids("AR §4.3 and FS §4.1", valid) == ["AR §4.3", "FS §4.1"]
    assert normalise_ids(["ZZ §9.9", "AR §99.1", 42, None], valid) == []


@pytest.fixture(autouse=True)
def _no_second_pass(monkeypatch):
    """Unit tests stub one chat reply; switch the attribution check off unless a test enables it."""
    from app import config

    monkeypatch.setattr(config, "VERIFY_ANSWERS", False)


def test_attribution_check_downgrades_answer_from_neighbouring_rule(monkeypatch):
    import numpy as np

    from app import config, llm, pipeline
    from app.chunking import Chunk
    from app.retriever import Retriever

    docs = [Chunk(id="EE §3.1", doc_code="EE", doc_title="T", section="3.1", title="t", parent_title="p",
                  text="absence from an examination because of illness", source="x.md", format="markdown")]
    r = Retriever(docs, np.eye(1, dtype=np.float32))
    monkeypatch.setattr(r, "embed_query", lambda q: np.array([1.0], dtype=np.float32))
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(pipeline, "known_conflicts", lambda: {})
    monkeypatch.setattr(config, "VERIFY_ANSWERS", True)
    replies = iter(['{"status":"answered","answer":"Submit a certificate within 5 days.","citations":["EE §3.1"]}',
                    '{"explicit": false, "reason": "the rule is about illness, the question is about a wedding"}'])
    monkeypatch.setattr(llm, "chat", lambda *a, **k: (next(replies), {}))
    resp = pipeline.ask("What if I miss the exam for a wedding?", r)
    assert resp.status == "not_covered" and resp.citations == [] and resp.passages[0].closest
    assert any("attribution check" in n for n in resp.validation_notes)

    replies = iter(['{"status":"answered","answer":"Submit a certificate within 5 days.","citations":["EE §3.1"]}',
                    '{"explicit": true, "reason": "illness is the situation asked about"}'])
    monkeypatch.setattr(llm, "chat", lambda *a, **k: (next(replies), {}))
    assert pipeline.ask("What if I miss the exam because I am ill?", r).status == "answered"


def test_model_chain_fails_over_when_a_free_model_is_withdrawn(monkeypatch):
    """First model answers 'unavailable for free' (as minimax-m3:free did overnight); the call
    must succeed on the next model and the dead one must be parked for later calls."""
    from app import config, llm

    monkeypatch.setattr(config, "PROVIDER_ORDER", ["openrouter"])
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(config, "OPENROUTER_MODEL", "dead/model:free")
    monkeypatch.setattr(config, "OPENROUTER_FALLBACKS", ["alive/model:free"])
    monkeypatch.setattr(llm, "_dead", {})
    calls: list[str] = []

    def fake_once(messages, entry, **kw):
        calls.append(entry.model)
        if entry.model == "dead/model:free":
            raise llm.ModelUnavailable("HTTP 404: This model is unavailable for free")
        return '{"ok": true}', {"model": entry.id}

    monkeypatch.setattr(llm, "_chat_once", fake_once)
    content, usage = llm.chat([{"role": "user", "content": "hi"}])
    assert content == '{"ok": true}' and usage["model"] == "alive/model:free"
    assert calls == ["dead/model:free", "alive/model:free"]
    assert llm.model_status()["dead/model:free"] == "parked"

    llm.chat([{"role": "user", "content": "again"}])
    assert calls[-1] == "alive/model:free" and calls.count("dead/model:free") == 1  # parked, not retried

    monkeypatch.setattr(llm, "_chat_once", lambda *a, **k: (_ for _ in ()).throw(llm.LLMError("429 after retries")))
    with pytest.raises(llm.LLMError, match="every model in the chain failed"):
        llm.chat([{"role": "user", "content": "x"}])


def test_spread_rotates_across_spread_provider_models_then_fails_over(monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "PROVIDER_ORDER", ["groq", "openrouter"])
    monkeypatch.setattr(config, "SPREAD_PROVIDERS", ["groq"])
    monkeypatch.setattr(config, "GROQ_API_KEY", "g")
    monkeypatch.setattr(config, "GROQ_MODELS", ["a", "b", "c"])
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "o")
    monkeypatch.setattr(config, "OPENROUTER_MODEL", "x/y:free")
    monkeypatch.setattr(config, "OPENROUTER_FALLBACKS", [])
    monkeypatch.setattr(llm, "_dead", {})
    import itertools
    monkeypatch.setattr(llm, "_rr", itertools.count())
    heads = [[e.id for e in llm.spread_chain()][0] for _ in range(4)]
    assert heads == ["groq/a", "groq/b", "groq/c", "groq/a"]           # round-robin over the pool
    assert [e.id for e in llm.spread_chain()][-1] == "x/y:free"       # non-pool entries stay as failover
    assert [e.id for e in llm.model_chain()][0] == "groq/a"           # plain chain is unaffected


def test_eval_job_runs_in_background_grades_and_persists(monkeypatch, tmp_path):
    """The server-side evaluation: rows fill in as a thread pool works, the summary is kept
    up to date, the state survives on disk, and a run interrupted by a restart is marked so."""
    import json
    import time

    from app import evaljob
    from app.schemas import AskResponse

    monkeypatch.setattr(evaljob, "STATE_PATH", tmp_path / "eval_live.json")
    monkeypatch.setattr(evaljob, "_state", {"status": "idle", "started_at": None, "finished_at": None, "done": 0,
                                            "total": 0, "workers": 0, "spread": False, "rows": [], "summary": None})
    monkeypatch.setattr(evaljob, "jobs", lambda: [
        ("answerable", {"id": "A1", "question": "q1", "expected_sections": ["AR §1.1"]}),
        ("not_covered", {"id": "N1", "question": "q2"}),
        ("conflict", {"id": "C1", "question": "q3", "expected_sections": ["AR §1.1", "AR §2.1"]}),
    ])

    def fake_ask(question, retriever, top_k=None, spread=False):
        status = {"q1": "answered", "q2": "answered", "q3": "conflict"}[question]  # q2 is a deliberate miss
        return AskResponse(question=question, status=status, answer="a", citations=["AR §1.1"], passages=[],
                           conflict=None if status != "conflict" else {"sections": ["AR §1.1", "AR §2.1"], "explanation": "e"},
                           top_similarity=0.9, llm_used=True, mode="llm", model="m", latency_ms=1)

    monkeypatch.setattr(evaljob, "ask", fake_ask)
    s = evaljob.start(retriever=None, workers=2, spread=True)
    assert s["status"] == "running" and s["total"] == 3
    for _ in range(100):
        if evaljob.state()["status"] == "done":
            break
        time.sleep(0.02)
    s = evaljob.state()
    assert s["status"] == "done" and s["done"] == 3
    assert s["summary"]["passed"] == 2 and s["summary"]["matrix"]["not_covered"]["answered"] == 1
    assert {r["id"]: r["pass"] for r in s["rows"]} == {"A1": True, "N1": False, "C1": True}

    saved = json.loads((tmp_path / "eval_live.json").read_text(encoding="utf-8"))
    assert saved["status"] == "done"
    saved["status"] = "running"
    (tmp_path / "eval_live.json").write_text(json.dumps(saved), encoding="utf-8")
    evaljob.load_saved()
    assert evaljob.state()["status"] == "interrupted"


def test_chain_spans_providers_in_order_and_skips_missing_keys(monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "PROVIDER_ORDER", ["groq", "gemini", "openrouter"])
    monkeypatch.setattr(config, "GROQ_API_KEY", "g")
    monkeypatch.setattr(config, "GROQ_MODELS", ["llama-3.3-70b-versatile"])
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")  # no key: skipped entirely
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "o")
    monkeypatch.setattr(config, "OPENROUTER_MODEL", "x/y:free")
    monkeypatch.setattr(config, "OPENROUTER_FALLBACKS", [])
    monkeypatch.setattr(llm, "_dead", {})
    ids = [e.id for e in llm.full_chain()]
    assert ids == ["groq/llama-3.3-70b-versatile", "x/y:free"]
    assert [e.seed for e in llm.full_chain()] == [True, True]
    # An explicit OpenRouter model (the audit's AUDIT_MODEL) goes first within that provider only.
    assert [e.id for e in llm.full_chain("a/b:free")] == ["groq/llama-3.3-70b-versatile", "a/b:free", "x/y:free"]


def test_validator_downgrades_unbacked_claims(monkeypatch):
    """An 'answered' with no valid citation, or a 'conflict' with one section, must not survive."""
    import numpy as np

    from app import llm, pipeline
    from app.chunking import Chunk
    from app.retriever import Retriever

    docs = [Chunk(id=f"AR §{i}.1", doc_code="AR", doc_title="T", section=f"{i}.1", title="t", parent_title="p",
                  text=f"clause {i} about attendance and fees", source="x.md", format="markdown") for i in range(3)]
    r = Retriever(docs, np.eye(3, dtype=np.float32))
    monkeypatch.setattr(r, "embed_query", lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32))
    monkeypatch.setattr(llm, "available", lambda: True)

    monkeypatch.setattr(llm, "chat", lambda *a, **k: ('{"status":"answered","answer":"x","citations":["ZZ §1.1"]}', {}))
    resp = pipeline.ask("q", r)
    assert resp.status == "not_covered" and resp.validation_notes

    monkeypatch.setattr(llm, "chat", lambda *a, **k: ('{"status":"conflict","answer":"x","citations":["AR §0.1"],'
                                                      '"conflict":{"sections":["AR §0.1"],"explanation":"e"}}', {}))
    resp = pipeline.ask("q", r)
    assert resp.status == "answered" and resp.conflict is None


def test_answer_whose_own_words_say_silent_is_downgraded(monkeypatch):
    import numpy as np

    from app import llm, pipeline
    from app.chunking import Chunk
    from app.retriever import Retriever

    docs = [Chunk(id="EE §3.3", doc_code="EE", doc_title="T", section="3.3", title="t", parent_title="p",
                  text="re-test on medical grounds", source="x.md", format="markdown")]
    r = Retriever(docs, np.eye(1, dtype=np.float32))
    monkeypatch.setattr(r, "embed_query", lambda q: np.array([1.0], dtype=np.float32))
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(pipeline, "known_conflicts", lambda: {})
    monkeypatch.setattr(llm, "chat", lambda *a, **k: (
        '{"status":"answered","answer":"The rulebook does not contain a specific clause about falling ill during an '
        'exam. The closest rule is the re-test for a missed mid-term.","citations":["EE §3.3"]}', {}))
    resp = pipeline.ask("What if I fall ill during the exam?", r)
    assert resp.status == "not_covered" and resp.citations == []
    assert resp.passages[0].closest

    # A real answer that merely mentions a detail is not downgraded.
    monkeypatch.setattr(llm, "chat", lambda *a, **k: (
        '{"status":"answered","answer":"Yes, you get a re-test within two weeks. The rule does not mention weekends.",'
        '"citations":["EE §3.3"]}', {}))
    assert pipeline.ask("Do I get a re-test?", r).status == "answered"


def test_audit_escalates_answer_that_leans_on_a_known_disagreement(monkeypatch):
    """Model says 'answered' citing AR §0.1; the audit knows AR §0.1 and AR §1.1 disagree and
    AR §1.1 was also retrieved, so the response must become a conflict naming both."""
    import numpy as np

    from app import llm, pipeline
    from app.chunking import Chunk
    from app.retriever import Retriever

    docs = [Chunk(id=f"AR §{i}.1", doc_code="AR", doc_title="T", section=f"{i}.1", title="t", parent_title="p",
                  text=f"clause {i}", source="x.md", format="markdown") for i in range(3)]
    r = Retriever(docs, np.eye(3, dtype=np.float32))
    monkeypatch.setattr(r, "embed_query", lambda q: np.array([1.0, 0.9, 0.0], dtype=np.float32))
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(llm, "chat", lambda *a, **k: ('{"status":"answered","answer":"65 per cent","citations":["AR §0.1"]}', {}))
    monkeypatch.setattr(pipeline, "known_conflicts", lambda: {
        frozenset({"AR §0.1", "AR §1.1"}): {"a_id": "AR §0.1", "b_id": "AR §1.1", "explanation": "65 vs 55", "confidence": 0.97}})
    resp = pipeline.ask("q", r)
    assert resp.status == "conflict"
    assert resp.conflict and resp.conflict.sections == ["AR §0.1", "AR §1.1"]
    assert "65 vs 55" in resp.answer and any("escalated" in n for n in resp.validation_notes)

    # Not escalated when the answer does not use a disputed value: the cited section may hold
    # several rules and the question may be about the undisputed one.
    monkeypatch.setattr(llm, "chat", lambda *a, **k: ('{"status":"answered","answer":"CGPA 7.0 for merit-cum-means","citations":["AR §0.1"]}', {}))
    assert pipeline.ask("q", r).status == "answered"

    # Not escalated when the other side was not retrieved.
    monkeypatch.setattr(r, "embed_query", lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32))
    r2 = Retriever(docs[:1] + docs[2:], np.eye(3, dtype=np.float32)[[0, 2]])
    monkeypatch.setattr(r2, "embed_query", lambda q: np.array([1.0, 0.0, 0.0], dtype=np.float32))
    resp = pipeline.ask("q", r2)
    assert resp.status == "answered"
