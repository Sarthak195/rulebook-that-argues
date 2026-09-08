"""The agent loop with a scripted model: search, open, conflicts, finish; and the fallback."""
from __future__ import annotations

import json

import numpy as np
import pytest

from app import agent, llm
from app.chunking import Chunk
from app.retriever import Retriever


@pytest.fixture
def retriever(monkeypatch):
    docs = [
        Chunk(id="AR §4.3", doc_code="AR", doc_title="Academic Regulations", section="4.3", title="Condonation", parent_title="Attendance",
              text="condoned on medical grounds only if attendance is not less than 65 per cent", source="a.md", format="markdown"),
        Chunk(id="LM §2.2", doc_code="LM", doc_title="Leave Policy", section="2.2", title="Condonation on medical grounds", parent_title="Medical Leave",
              text="condoned provided overall attendance is not less than 55 per cent", source="l.md", format="markdown"),
        Chunk(id="EE §3.3", doc_code="EE", doc_title="Exam Regulations", section="3.3", title="Missed Mid-term Tests", parent_title="Absence",
              text="a student who misses a mid-term test on medical grounds shall be given a re-test within two weeks", source="e.md", format="markdown"),
    ]
    r = Retriever(docs, np.eye(3, dtype=np.float32))
    monkeypatch.setattr(r, "embed_query", lambda q: np.array([1.0, 0.9, 0.2], dtype=np.float32) if "attendance" in q else np.array([0.1, 0.1, 1.0], dtype=np.float32))
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(agent, "load_audit", lambda: {"conflicts": [{"a_id": "AR §4.3", "b_id": "LM §2.2", "topic": "condonation floor",
                                                                         "confidence": 0.97, "explanation": "65 vs 55"}]})
    monkeypatch.setattr(agent, "known_conflicts", lambda: {})
    return r


def scripted(replies):
    it = iter(replies)

    def chat(messages, **kw):
        return json.dumps(next(it)), {"model": "test/model"}
    return chat


def test_agent_searches_opens_checks_conflicts_and_finishes(monkeypatch, retriever):
    monkeypatch.setattr(llm, "chat", scripted([
        {"thought": "look up condonation", "action": "search", "input": {"query": "attendance shortage condonation medical"}},
        {"thought": "and the mid-term rule", "action": "search", "input": {"query": "missed mid-term test medical re-test"}},
        {"thought": "check disputes", "action": "conflicts", "input": {}},
        {"thought": "done", "action": "finish", "input": {"status": "conflict", "answer": "Condonation is disputed: AR §4.3 says 65, LM §2.2 says 55. The mid-term can be re-taken (EE §3.3).",
                                                             "citations": ["AR §4.3", "LM §2.2", "EE §3.3"], "conflict": {"sections": ["AR §4.3", "LM §2.2"], "explanation": "65 vs 55"}}},
    ]))
    resp = agent.run_agent("58% attendance after hospital and a missed mid-term: options?", retriever)
    assert resp.status == "conflict" and not resp.fell_back
    assert [s.action for s in resp.steps] == ["search", "search", "conflicts", "finish"]
    assert "1 known contradictions" in resp.steps[2].observation
    assert resp.conflict.sections == ["AR §4.3", "LM §2.2"] and "EE §3.3" in resp.citations
    assert {p.id for p in resp.passages} == {"AR §4.3", "LM §2.2", "EE §3.3"}
    assert all(p.cited for p in resp.passages)


def test_agent_cannot_cite_what_it_did_not_see(monkeypatch, retriever):
    monkeypatch.setattr(llm, "chat", scripted([
        {"thought": "guess", "action": "finish", "input": {"status": "answered", "answer": "You can re-take it.", "citations": ["EE §3.3"]}},
    ]))
    resp = agent.run_agent("Can I retake a missed mid-term?", retriever)
    assert resp.status == "not_covered" and resp.citations == []
    assert any("did not" in n or "without citing" in n for n in resp.validation_notes)


def test_agent_falls_back_to_one_shot_when_it_runs_out_of_steps(monkeypatch, retriever):
    from app import config, pipeline
    from app.schemas import AskResponse

    monkeypatch.setattr(llm, "chat", scripted([{"thought": "search", "action": "search", "input": {"query": "attendance"}}] * agent.MAX_STEPS))
    monkeypatch.setattr(agent, "ask", lambda q, r: AskResponse(question=q, status="answered", answer="one-shot", citations=["EE §3.3"],
                                                                   passages=[], top_similarity=0.9, llm_used=True, mode="llm", model="m", latency_ms=1))
    resp = agent.run_agent("attendance?", retriever)
    assert resp.fell_back and resp.answer == "one-shot" and len(resp.steps) == agent.MAX_STEPS
