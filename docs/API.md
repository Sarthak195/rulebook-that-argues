# API

Interactive docs: `/docs` (Swagger UI) and `/redoc`.

## `POST /ask`

Request:

```json
{"question": "What CGPA do I need to maintain to keep my merit scholarship?", "top_k": 6}
```

`top_k` is optional (1 to 12, default 6).

Response (`AskResponse`):

| field | type | meaning |
|---|---|---|
| `status` | `answered` \| `not_covered` \| `conflict` | the response type |
| `answer` | string | the answer, or the statement that the rulebook is silent, or both clauses quoted |
| `citations` | string[] | section ids the answer relies on; empty for `not_covered` |
| `passages` | Passage[] | every retrieved passage, in rank order, whether cited or not |
| `conflict` | `{sections, explanation}` or null | the disagreeing sections and why |
| `resolution_authority` | `{id, title, text}` or null | the clause that decides inconsistencies; only on `conflict` |
| `top_similarity` | float | best dense cosine among retrieved passages |
| `llm_used` | bool | false when the gate or the offline fallback answered |
| `mode` | `llm` \| `retrieval-gate` \| `offline-fallback` | how the response was produced |
| `model` | string or null | the OpenRouter model id |
| `latency_ms` | int | end-to-end |
| `validation_notes` | string[] | anything the validator changed about the model's output |

`Passage`:

| field | meaning |
|---|---|
| `id` | `AR §4.3` |
| `doc_code`, `doc_title`, `section`, `title`, `parent_title` | where it lives |
| `source`, `format` | file name and `markdown` \| `table` \| `pdf` |
| `score` | dense cosine similarity to the question |
| `bm25` | lexical score, for transparency |
| `text` | the clause, verbatim |
| `cited` | true if the answer relied on it |
| `closest` | true on `not_covered` for the nearest clause that still does not answer |

Example:

```bash
curl -s -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "What CGPA do I need to maintain to keep my merit scholarship?"}'
```

```json
{
  "question": "What CGPA do I need to maintain to keep my merit scholarship?",
  "status": "conflict",
  "answer": "There is conflicting information ... [AR §11.2] ... not less than 7.5 ... [SF §3.1] ... not less than 8.0 ...",
  "citations": ["AR §11.2", "SF §3.1"],
  "passages": [
    {"id": "AR §11.2", "doc_title": "Academic Regulations for the B.Tech. Programme (2026-27)", "section": "11.2",
     "title": "Continuation of Merit Scholarship", "parent_title": "Scholarships and Medals",
     "source": "01_academic_regulations.md", "format": "markdown", "score": 0.8513, "bm25": 9.12,
     "text": "A Merit Scholarship once awarded shall continue ... not less than 7.5 ...", "cited": true, "closest": false},
    {"id": "SF §3.1", "format": "pdf", "score": 0.8391, "cited": true, "...": "..."}
  ],
  "conflict": {"sections": ["AR §11.2", "SF §3.1"], "explanation": "One passage requires 7.5, the other 8.0."},
  "resolution_authority": {"id": "AR §15.1", "title": "Interpretation", "text": "If any question arises ... the decision of the Vice-Chancellor shall be final."},
  "top_similarity": 0.8513, "llm_used": true, "mode": "llm", "model": "minimax/minimax-m3:free",
  "latency_ms": 2439, "validation_notes": []
}
```

Errors: `422` on a malformed body, `502` with the OpenRouter message when the LLM call fails
after retries, `503` while the index is still loading.

## `GET /health`

```json
{"ok": true, "sections": 139, "embedding_model": "BAAI/bge-small-en-v1.5",
 "llm_available": true, "llm_model": "minimax/minimax-m3:free", "top_k": 6, "min_similarity": 0.45}
```

## `GET /sections`

All section ids with document, title, parent, format, source file and word count. Useful for
checking what a citation points at.

## `GET /questions`

The labelled test set from `tests/questions.json` (`answerable`, `conflict`, `not_covered`,
`borderline`). The front end uses it for the example chips and the evaluation tab.

## `GET /audit`

The cached corpus-wide contradiction audit (`results/conflict_audit.json`). If none has been run,
`{"available": false, "hint": "run: python scripts/audit.py"}`.

```json
{"available": true, "generated_at": "...", "model": "minimax/minimax-m3:free", "threshold": 0.78,
 "cross_document_only": true, "sections": 139, "pairs_checked": 50, "seconds": 140.2,
 "conflicts": [{"a_id": "AR §11.2", "b_id": "SF §3.1", "similarity": 0.94, "topic": "...", "explanation": "...",
                "confidence": 0.95, "a": {"id": "...", "doc_title": "...", "path": "...", "format": "...", "text": "..."}, "b": {"...": "..."}}],
 "cleared": [{"a_id": "...", "b_id": "...", "similarity": 0.81, "conflict": false, "explanation": "..."}]}
```
