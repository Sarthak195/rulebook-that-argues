"""A multi-step answering agent over the rulebook.

The one-shot pipeline retrieves once and answers once. Some questions need more than one look:
"I have 58% attendance because I was in hospital, and I also missed a mid-term: what are my
options?" touches condonation (two clauses that disagree), the medical re-test rule, and
possibly the supplementary-exam route. This agent lets the model plan: it can search the
rulebook with its own queries, open a section by id, consult the audited contradictions, and
only then finish. Every step is recorded and shown.

The same honesty rules apply at the end: a citation must be a section the agent actually saw,
a conflict needs two real sections, and an answer whose own words say the rulebook is silent
is downgraded. If the agent cannot finish within the step budget, the one-shot pipeline
answers instead and the trace says so.
"""
from __future__ import annotations

import json
import time

from . import config, llm
from .audit import known_conflicts, load_audit
from .pipeline import SECTION_ID_RE, SILENCE_RE, ask, normalise_ids
from .retriever import Retriever
from .schemas import AgentResponse, AgentStep, Authority, ConflictInfo, Passage

MAX_STEPS = 5

AGENT_PROMPT = f"""You are the regulations desk of {config.INSTITUTE}, working step by step. You answer ONLY from rulebook text you have seen through your tools in this conversation. Never use outside knowledge.

Tools (call exactly one per turn, as JSON):
- search: {{"action": "search", "input": {{"query": "..."}}}}  -> the most relevant sections for a query (id, title, similarity, text). Use focused queries; one per aspect of the question.
- open: {{"action": "open", "input": {{"id": "AR §4.3"}}}}  -> the full text of one section by id.
- conflicts: {{"action": "conflicts", "input": {{}}}}  -> the list of places where the rulebook is known to contradict itself (pairs of section ids with the topic).
- finish: {{"action": "finish", "input": {{"status": "answered" | "not_covered" | "conflict", "answer": "...", "citations": ["AR §4.3", ...], "conflict": {{"sections": ["...", "..."], "explanation": "..."}} | null}}}}

Rules for finish:
- "answered": the sections you cite explicitly address each part of the question. Cite every section you rely on. Address each part of a multi-part question separately.
- "not_covered": no section you saw addresses the specific situation asked (a related rule for a different situation does not count; do not reason by analogy or add the word "only" to a rule). Say what the closest rule does cover.
- "conflict": two sections you saw give incompatible rules for something the question asks about. Quote both, do not pick a winner. A waiver or interpretation clause is not a conflict. If the question has several parts and only one is in conflict, still use "conflict" and answer the other parts in the same text.
- Before finishing, if any cited rule involves a number, threshold or deadline, call conflicts once to check it is not disputed.

Reply with ONE JSON object per turn: {{"thought": "one sentence on what you need next", "action": "...", "input": {{...}}}}. No prose outside the JSON. You have at most {MAX_STEPS} turns; finish before they run out."""


def _passage(chunk, score: float | None) -> Passage:
    return Passage(id=chunk.id, doc_code=chunk.doc_code, doc_title=chunk.doc_title, section=chunk.section, title=chunk.title,
                   parent_title=chunk.parent_title, source=chunk.source, format=chunk.format,
                   score=round(score, 4) if score is not None else 0.0, bm25=0.0, text=chunk.text)


def run_agent(question: str, retriever: Retriever) -> AgentResponse:
    t0 = time.time()
    question = question.strip()
    steps: list[AgentStep] = []
    seen: dict[str, Passage] = {}      # every section the agent has looked at, by id
    notes: list[str] = []
    messages = [{"role": "system", "content": AGENT_PROMPT}, {"role": "user", "content": f"Question: {question}"}]
    used_model: str | None = None
    final: dict | None = None

    for n in range(1, MAX_STEPS + 1):
        try:
            content, usage = llm.chat(messages, max_tokens=700)
            used_model = usage.get("model") or used_model
            data = llm.extract_json(content)
        except llm.LLMError as e:
            steps.append(AgentStep(n=n, thought="", action="error", input={}, observation=str(e)[:300]))
            break
        action = str(data.get("action", "")).strip().lower()
        inp = data.get("input") if isinstance(data.get("input"), dict) else {}
        thought = str(data.get("thought", "")).strip()

        if action == "search":
            query = str(inp.get("query", "")).strip() or question
            hits = retriever.search(query, k=5)
            for h in hits:
                seen.setdefault(h.chunk.id, _passage(h.chunk, h.score))
            obs = "\n\n".join(f"[{h.chunk.id}] {h.chunk.doc_title} > {h.chunk.title} (similarity {h.score:.2f})\n{h.chunk.text}" for h in hits)
            summary = ", ".join(f"{h.chunk.id} ({h.score:.2f})" for h in hits)
        elif action == "open":
            ids = normalise_ids([str(inp.get("id", ""))], set(retriever.by_id))
            if ids:
                c = retriever.by_id[ids[0]]
                seen.setdefault(c.id, _passage(c, None))
                obs = f"[{c.id}] {c.doc_title} > {c.parent_title} > {c.title}\n{c.text}"
                summary = f"opened {c.id}"
            else:
                obs = f"No section called {inp.get('id')!r}. Section ids look like 'AR §4.3'; use search to find them."
                summary = "unknown section id"
        elif action == "conflicts":
            report = load_audit() or {"conflicts": []}
            rows = [f"{c['a_id']} vs {c['b_id']}: {c['topic']} (confidence {float(c.get('confidence', 0)):.2f})"
                    for c in report.get("conflicts", []) if float(c.get("confidence", 0)) >= 0.8]
            obs = "Known contradictions in the rulebook (from the corpus audit):\n" + ("\n".join(rows) if rows else "none recorded")
            summary = f"{len(rows)} known contradictions"
        elif action == "finish":
            final = inp
            steps.append(AgentStep(n=n, thought=thought, action="finish", input={"status": inp.get("status")}, observation="done"))
            break
        else:
            obs = f"Unknown action {action!r}. Use search, open, conflicts or finish."
            summary = "unknown action"
        steps.append(AgentStep(n=n, thought=thought, action=action, input=inp, observation=summary))
        messages.append({"role": "assistant", "content": json.dumps(data)})
        messages.append({"role": "user", "content": f"Observation:\n{obs}\n\nTurns used: {n} of {MAX_STEPS}."})

    passages = list(seen.values())

    if final is None:
        # Out of steps or the model lost the thread: the one-shot pipeline answers, and we say so.
        notes.append("agent did not finish within its step budget; answered by the one-shot pipeline")
        one = ask(question, retriever)
        return AgentResponse(question=question, status=one.status, answer=one.answer, citations=one.citations,
                             passages=one.passages, conflict=one.conflict, resolution_authority=one.resolution_authority,
                             steps=steps, model=one.model, latency_ms=int((time.time() - t0) * 1000),
                             validation_notes=notes + one.validation_notes, fell_back=True)

    # ---- validate the finish exactly as the one-shot pipeline validates its answer ----
    valid = set(seen)
    status = str(final.get("status", "")).strip().lower().replace("-", "_")
    answer = str(final.get("answer", "")).strip()
    citations = normalise_ids(final.get("citations", []), valid)
    raw_conflict = final.get("conflict") if isinstance(final.get("conflict"), dict) else None
    conflict: ConflictInfo | None = None
    if status not in {"answered", "not_covered", "conflict"}:
        notes.append(f"unknown status {status!r}; treated as not_covered")
        status = "not_covered"
    if status == "conflict":
        sections = normalise_ids((raw_conflict or {}).get("sections", []), valid)
        if len(sections) < 2:
            notes.append("conflict claimed with fewer than two sections the agent had seen; downgraded")
            status = "answered" if citations else "not_covered"
        else:
            conflict = ConflictInfo(sections=sections, explanation=str((raw_conflict or {}).get("explanation", "")).strip())
            citations = list(dict.fromkeys(sections + citations))
    if status == "answered" and not citations:
        notes.append("answered without citing a section the agent had seen; downgraded to not_covered")
        status = "not_covered"
    if status == "answered" and SILENCE_RE.search(answer.split(". ")[0] + "."):
        notes.append("agent's own answer says the rulebook is silent; downgraded to not_covered")
        status = "not_covered"
    if status == "answered":
        for pair, rec in known_conflicts().items():
            a, b = sorted(pair, key=lambda s: (s not in citations, s))
            if a in citations and b in valid:
                status = "conflict"
                conflict = ConflictInfo(sections=[a, b], explanation=rec["explanation"])
                citations = list(dict.fromkeys([a, b] + citations))
                notes.append(f"escalated to conflict: the audit found {a} and {b} disagree and the agent had both in view")
                break
    if status == "not_covered":
        citations, conflict = [], None
    for p in passages:
        p.cited = p.id in citations
    authority = None
    if status == "conflict":
        hit = retriever.dense_only("inconsistency between these regulations and another policy, interpretation, decision shall be final", k=1)
        if hit:
            authority = Authority(id=hit[0].chunk.id, title=hit[0].chunk.title, text=hit[0].chunk.text)

    return AgentResponse(question=question, status=status, answer=answer, citations=citations, passages=passages,
                         conflict=conflict, resolution_authority=authority, steps=steps, model=used_model,
                         latency_ms=int((time.time() - t0) * 1000), validation_notes=notes, fell_back=False)
