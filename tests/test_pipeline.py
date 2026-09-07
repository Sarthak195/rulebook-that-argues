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
