"""The /ask pipeline: retrieve -> similarity gate -> LLM classification -> validation -> authority.

Three outcomes, and the system has to pick correctly:
  answered     at least one passage explicitly addresses the situation asked about
  not_covered  the corpus is silent, including when it covers an adjacent situation
  conflict     two passages give incompatible rules for the situation asked about

The LLM only ever sees the retrieved passages, must return JSON, and its citations are checked
against the passages it was given. An "answered" with no valid citation is downgraded; a
"conflict" naming fewer than two real sections is downgraded. The model cannot invent a source.
"""
from __future__ import annotations

import re
import time

from . import config, llm
from .audit import known_conflicts
from .retriever import Hit, Retriever
from .schemas import AskResponse, Authority, ConflictInfo, Passage

SYSTEM_PROMPT = f"""You are the regulations desk of {config.INSTITUTE}. You answer questions ONLY from the passages supplied in the user message. You never use outside knowledge and you never guess.

Decide which ONE of three outcomes applies, then reply with a single JSON object and nothing else.

1. "answered" - at least one passage explicitly addresses the specific situation asked about. Give a direct answer in plain language, quoting or closely paraphrasing the operative words of the clause, and list every passage you relied on in "citations".

2. "not_covered" - no passage addresses the specific situation asked about. This includes the common case where passages cover a RELATED or SIMILAR situation but not this one. Examples: a rule about absence due to illness does not answer a question about absence for a wedding; a rule about tuition-fee dues does not answer a question about hostel-fee dues; a rule about supplementary exams for failed courses does not answer a question about improving a passed grade. Do not extrapolate, generalise, reason by analogy, or infer that silence means permission or prohibition. In "answer", state plainly that the rulebook does not address the question, then in one sentence say what the closest passage does cover. Put that passage in "closest_sections". "citations" must be empty.

3. "conflict" - two or more passages give incompatible rules for the same situation asked about: different numbers, thresholds, percentages, deadlines, amounts, or opposite permissions. In "answer", quote both clauses with their section ids and explain the disagreement. Do NOT pick a winner, average them, or say one probably overrides the other. Put the disagreeing section ids in "conflict.sections" and in "citations". Note carefully what is NOT a conflict: a clause that lets an authority relax, waive, or interpret a rule; passages that agree; passages that address different aspects of the question; a general rule plus a specific procedure. Flag a conflict only when the disagreement is about the very thing the user asked.

Rules:
- Cite section ids exactly as they appear in square brackets, for example "AR §4.3". Never invent a section id.
- Keep "answer" to 2-5 sentences. Speak to the student directly.
- If the question is unrelated to the rulebook entirely, use "not_covered".

Reply with exactly this JSON shape:
{{"status": "answered" | "not_covered" | "conflict",
  "answer": "string",
  "citations": ["section id", ...],
  "closest_sections": ["section id", ...],
  "conflict": {{"sections": ["section id", "section id"], "explanation": "string"}} | null}}"""

AUTHORITY_QUERY = "inconsistency between these regulations and another policy, interpretation, decision shall be final"

SECTION_ID_RE = re.compile(r"\b([A-Z]{2,4})\s*§?\s*(\d+(?:\.\d+)?)\b")


def normalise_ids(raw, valid: set[str]) -> list[str]:
    """Map model output like 'AR 4.3' or ['AR §4.3'] onto known ids, deduplicated, order kept."""
    out: list[str] = []
    items = raw if isinstance(raw, list) else [raw]
    for item in items:
        if not isinstance(item, str):
            continue
        for code, sec in SECTION_ID_RE.findall(item):
            cid = f"{code} §{sec}"
            if cid in valid and cid not in out:
                out.append(cid)
    return out


def hit_to_passage(h: Hit) -> Passage:
    c = h.chunk
    return Passage(id=c.id, doc_code=c.doc_code, doc_title=c.doc_title, section=c.section, title=c.title,
                   parent_title=c.parent_title, source=c.source, format=c.format,
                   score=round(h.score, 4), bm25=round(h.bm25, 3), text=c.text)


def passage_block(hits: list[Hit]) -> str:
    parts = []
    for h in hits:
        c = h.chunk
        parts.append(f"[{c.id}] {c.doc_title} > {c.parent_title} > {c.title} (similarity {h.score:.2f})\n{c.text}")
    return "\n\n".join(parts)


def ask(question: str, retriever: Retriever, top_k: int | None = None) -> AskResponse:
    t0 = time.time()
    question = question.strip()
    hits = retriever.search(question, k=top_k or config.TOP_K)
    passages = [hit_to_passage(h) for h in hits]
    top_sim = max((h.score for h in hits), default=0.0)
    notes: list[str] = []

    def done(**kw) -> AskResponse:
        return AskResponse(question=question, passages=passages, top_similarity=round(top_sim, 4),
                           latency_ms=int((time.time() - t0) * 1000), validation_notes=notes, **kw)

    # 1. Similarity gate: nothing in the corpus is even near this question.
    if not hits or top_sim < config.MIN_SIMILARITY:
        return done(status="not_covered", citations=[], llm_used=False, mode="retrieval-gate", model=None,
                    answer="The rulebook does not address this. Nothing in the corpus is close enough to the "
                           f"question to be worth quoting (best similarity {top_sim:.2f}).")

    # 2. Offline fallback: keep the UI usable without a key, and say so loudly.
    if not llm.available():
        best = passages[0]
        best.cited = True
        return done(status="answered", citations=[best.id], llm_used=False, mode="offline-fallback", model=None,
                    answer=f"[Offline mode: OPENROUTER_API_KEY is not set, so this is the closest passage, not a "
                           f"verified answer] {best.id} {best.title}: {best.text}")

    # 3. Ask the model to classify and answer from the passages only.
    user_msg = f"Question: {question}\n\nPassages, ordered by retrieval rank:\n\n{passage_block(hits)}"
    content, _usage = llm.chat([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}])
    data = llm.extract_json(content)

    valid = {p.id for p in passages}
    status = str(data.get("status", "")).strip().lower().replace("-", "_")
    answer = str(data.get("answer", "")).strip()
    citations = normalise_ids(data.get("citations", []), valid)
    closest = normalise_ids(data.get("closest_sections", []), valid)
    raw_conflict = data.get("conflict") if isinstance(data.get("conflict"), dict) else None
    conflict: ConflictInfo | None = None

    # 4. Validate. The model does not get to assert what it cannot back with a passage it was given.
    if status not in {"answered", "not_covered", "conflict"}:
        notes.append(f"model returned unknown status {status!r}; treated as not_covered")
        status = "not_covered"
    if status == "conflict":
        sections = normalise_ids((raw_conflict or {}).get("sections", []), valid)
        if len(sections) < 2:
            notes.append("conflict claimed with fewer than two valid sections; downgraded")
            status = "answered" if citations else "not_covered"
        else:
            conflict = ConflictInfo(sections=sections, explanation=str((raw_conflict or {}).get("explanation", "")).strip())
            citations = list(dict.fromkeys(sections + citations))
    if status == "answered" and not citations:
        notes.append("answered without a valid citation; downgraded to not_covered")
        status = "not_covered"
    if status == "not_covered":
        citations = []
        conflict = None
        if not closest and passages:
            closest = [passages[0].id]

    # 4b. Audit-informed escalation. The corpus audit already knows where the rulebook disagrees
    # with itself. If the model answered from one side of a known disagreement while the other
    # side was also on the table, the honest response is a conflict, whatever the model said.
    if status == "answered":
        retrieved = {p.id for p in passages}
        for pair, rec in known_conflicts().items():
            a, b = sorted(pair, key=lambda s: (s not in citations, s))  # cited member first
            if a in retrieved and b in retrieved and a in citations:
                status = "conflict"
                conflict = ConflictInfo(sections=[a, b], explanation=rec["explanation"])
                citations = list(dict.fromkeys([a, b] + citations))
                answer = (f"The rulebook contradicts itself on this point. {rec['explanation']} "
                          f"(Found by the corpus-wide audit, confidence {float(rec['confidence']):.2f}.) "
                          f"Read on its own, {a} would give: {answer}")
                notes.append(f"escalated to conflict: the audit found {a} and {b} disagree; both were retrieved and {a} was cited")
                break

    for p in passages:
        p.cited = p.id in citations
        p.closest = status == "not_covered" and p.id in closest

    # 5. When the rulebook argues with itself, say who gets to settle the argument.
    authority = None
    if status == "conflict":
        a = retriever.dense_only(AUTHORITY_QUERY, k=1)
        if a:
            authority = Authority(id=a[0].chunk.id, title=a[0].chunk.title, text=a[0].chunk.text)

    return done(status=status, answer=answer, citations=citations, conflict=conflict, resolution_authority=authority,
                llm_used=True, mode="llm", model=config.OPENROUTER_MODEL)
