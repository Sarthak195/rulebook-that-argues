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
    assert codes == {"AR", "EE", "HH", "FS", "SF", "LM", "SG"}
    assert len(chunks) > 150
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


def test_bucket_headers_route_around_a_drained_model(monkeypatch):
    import time

    from app import config, llm

    assert llm.parse_duration("48.352s") == 48.352
    assert llm.parse_duration("1m30.5s") == 90.5
    assert abs(llm.parse_duration("2h29m45.6s") - 8985.6) < 1e-6
    assert llm.parse_duration("1ms") == 0.001 and llm.parse_duration(None) is None and llm.parse_duration("soon") is None

    monkeypatch.setattr(config, "PROVIDER_ORDER", ["groq"])
    monkeypatch.setattr(config, "GROQ_API_KEY", "g")
    monkeypatch.setattr(config, "GROQ_MODELS", ["a", "b"])
    monkeypatch.setattr(llm, "_dead", {})
    monkeypatch.setattr(llm, "_bucket", {})
    a, b = llm.full_chain()
    assert llm.has_headroom(a)  # unknown means yes

    class Resp:
        headers = {"x-ratelimit-remaining-tokens": "900", "x-ratelimit-reset-tokens": "40s"}

    llm._remember_quota(a, Resp())
    assert not llm.has_headroom(a) and llm.has_headroom(b)
    llm._bucket[a.id]["reset_at"] = time.time() - 1  # refilled
    assert llm.has_headroom(a)

    # A live question tries the sibling with headroom first when the preferred model is drained.
    llm._remember_quota(a, Resp())
    calls: list[str] = []

    def fake_once(messages, entry, **kw):
        calls.append(entry.model)
        return '{"ok": true}', {"model": entry.id}

    monkeypatch.setattr(llm, "_chat_once", fake_once)
    llm.chat([{"role": "user", "content": "hi"}])
    assert calls == ["b"]


def test_daily_cap_parks_the_model_for_the_stated_wait(monkeypatch):
    import time

    from app import config, llm

    class Resp:
        status_code = 429
        headers = {"retry-after": "584", "x-ratelimit-remaining-tokens": "8000", "x-ratelimit-reset-tokens": "1ms"}
        text = ('{"error":{"message":"Rate limit reached for model `openai/gpt-oss-120b` ... on tokens per day (TPD): '
                'Limit 200000, Used 199868, Requested 1483. Please try again in 9m43.632s."}}')

    assert llm.stated_wait(Resp()) == 584.0
    monkeypatch.setattr(config, "PROVIDER_ORDER", ["groq"])
    monkeypatch.setattr(config, "GROQ_API_KEY", "g")
    monkeypatch.setattr(config, "GROQ_MODELS", ["a", "b"])
    monkeypatch.setattr(llm, "_dead", {})
    monkeypatch.setattr(llm, "_bucket", {})
    a, b = llm.full_chain()
    posted: list[str] = []

    def fake_post(url, json=None, headers=None, timeout=None):
        posted.append(json["model"])
        if json["model"] == "a":
            return Resp()
        class Ok:
            status_code = 200
            headers = {}
            text = '{"choices":[{"message":{"content":"{\\"ok\\":true}"}}],"model":"b"}'
            def json(self):
                import json as _j
                return _j.loads(self.text)
        return Ok()

    monkeypatch.setattr(llm.httpx, "post", fake_post)
    content, usage = llm.chat([{"role": "user", "content": "hi"}])
    assert usage["model"] == "groq/b" and posted == ["a", "b"]     # exactly one request at the capped model
    assert llm._dead["groq/a"] > time.time() + 500                 # parked for the stated wait, not 20 s
    assert not llm.has_headroom(a)
    llm.chat([{"role": "user", "content": "again"}])
    assert posted == ["a", "b", "b"]                               # parked model not touched again

    assert llm.extract_json("<think>\nreasoning {with braces}\n</think>\n{\"status\": \"answered\"}") == {"status": "answered"}


def test_multiple_keys_become_separate_quota_slots(monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "PROVIDER_ORDER", ["gemini"])
    monkeypatch.setattr(config, "GEMINI_API_KEYS", ["k1", "k2"])
    monkeypatch.setattr(config, "GEMINI_MODELS", ["flash", "latest"])
    monkeypatch.setattr(llm, "_dead", {})
    chain = llm.full_chain()
    assert [e.id for e in chain] == ["gemini#1/flash", "gemini#2/flash", "gemini#1/latest", "gemini#2/latest"]
    assert [e.key for e in chain] == ["k1", "k2", "k1", "k2"]
    assert chain[0].account == "gemini#1" and chain[1].account == "gemini#2"
    # Parking one key's model leaves the other key's copy live.
    llm.park("gemini#1/flash", 60)
    assert [e.id for e in llm.model_chain()][0] == "gemini#2/flash"
    # A single key keeps the old ids.
    monkeypatch.setattr(config, "GEMINI_API_KEYS", ["only"])
    assert [e.id for e in llm.full_chain()] == ["gemini/flash", "gemini/latest"]


def test_extra_openai_compatible_provider_joins_the_chain(monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "EXTRA_PROVIDERS", {"cerebras": {"url": "https://api.cerebras.ai/v1/chat/completions",
                                                                  "keys": ["csk-1"], "models": ["gpt-oss-120b"], "seed": True, "timeout": 45.0}})
    monkeypatch.setattr(config, "PROVIDER_ORDER", ["cerebras", "gemini"])
    monkeypatch.setattr(config, "GEMINI_API_KEYS", ["g"])
    monkeypatch.setattr(config, "GEMINI_MODELS", ["flash"])
    monkeypatch.setattr(llm, "_dead", {})
    chain = llm.full_chain()
    assert [e.id for e in chain] == ["cerebras/gpt-oss-120b", "gemini/flash"]
    assert chain[0].url.startswith("https://api.cerebras.ai") and chain[0].seed is True
    assert llm.provider_timeout("cerebras") == 45.0 and llm.provider_timeout("gemini") == 60.0


def test_mistral_style_headers_feed_the_bucket(monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "PROVIDER_ORDER", ["mistral"])
    monkeypatch.setattr(config, "EXTRA_PROVIDERS", {"mistral": {"url": "https://api.mistral.ai/v1/chat/completions",
                                                                 "keys": ["m"], "models": ["ministral-8b-2512", "ministral-14b-2512"], "seed": False, "timeout": 60}})
    monkeypatch.setattr(llm, "_bucket", {})
    small, big = llm.full_chain()

    class Resp:
        headers = {"x-ratelimit-limit-req-minute": "30", "x-ratelimit-remaining-req-minute": "0",
                   "x-ratelimit-limit-tokens-minute": "937500", "x-ratelimit-remaining-tokens-minute": "900000"}

    llm._remember_quota(big, Resp())
    assert not llm.has_headroom(big)      # no requests left this minute, whatever the tokens say
    assert llm.has_headroom(small)        # unknown means yes

    class Resp2:
        headers = {"x-ratelimit-remaining-req-minute": "150", "x-ratelimit-remaining-tokens-minute": "600000"}

    llm._remember_quota(small, Resp2())
    assert llm.has_headroom(small)


def test_chain_spans_providers_in_order_and_skips_missing_keys(monkeypatch):
    from app import config, llm

    monkeypatch.setattr(config, "PROVIDER_ORDER", ["groq", "gemini", "openrouter"])
    monkeypatch.setattr(config, "GROQ_API_KEY", "g")
    monkeypatch.setattr(config, "GROQ_API_KEYS", [])
    monkeypatch.setattr(config, "GROQ_MODELS", ["llama-3.3-70b-versatile"])
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")  # no key: skipped entirely
    monkeypatch.setattr(config, "GEMINI_API_KEYS", [])
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "o")
    monkeypatch.setattr(config, "OPENROUTER_API_KEYS", [])
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
