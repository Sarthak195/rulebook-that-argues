from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["answered", "not_covered", "conflict"]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int | None = Field(None, ge=1, le=12)
    # Batch callers (the evaluation tab) set this to rotate across providers' live models so
    # consecutive calls hit different per-minute token buckets. Single questions leave it off.
    spread: bool = False


class Passage(BaseModel):
    id: str                 # "AR §4.3"
    doc_code: str
    doc_title: str
    section: str
    title: str
    parent_title: str
    source: str
    format: str
    score: float            # dense cosine similarity
    bm25: float
    text: str
    cited: bool = False     # the answer relied on this passage
    closest: bool = False   # for not_covered: nearest passage that still does not answer


class ConflictInfo(BaseModel):
    sections: list[str]
    explanation: str


class Authority(BaseModel):
    id: str
    title: str
    text: str


class AskResponse(BaseModel):
    question: str
    status: Status
    answer: str
    citations: list[str]
    passages: list[Passage]
    conflict: ConflictInfo | None = None
    resolution_authority: Authority | None = None
    top_similarity: float
    llm_used: bool
    mode: str               # "llm" | "retrieval-gate" | "offline-fallback"
    model: str | None
    latency_ms: int
    validation_notes: list[str] = []
