# Architecture

```
                 ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
 question ──────►│  retrieval   │────►│  similarity gate │────►│  LLM (JSON)  │──┐
                 │ dense + BM25 │     │  < 0.45 → silent │     │ 3 outcomes   │  │
                 └──────────────┘     └──────────────────┘     └──────────────┘  │
                        ▲                                                         ▼
                 ┌──────┴───────┐                                        ┌──────────────┐
                 │ index/       │                                        │  validator   │
                 │ 139 sections │                                        │ cites ⊆ shown│
                 └──────────────┘                                        └──────┬───────┘
                                                                                ▼
                                                              response: status, answer, citations,
                                                              passages (all of them, scored),
                                                              conflict, resolution_authority, mode
```

## 1. Corpus and chunking (`app/chunking.py`)

Regulations are already written in citation-sized units, so the chunk is the numbered
sub-section and its id is `<doc code> §<number>`, e.g. `AR §4.3`. No sliding windows, no
overlap. Each chunk carries its parent heading, so the text embedded is
`Academic Regulations | Attendance | 4.3 Condonation of Shortage of Attendance` followed by the body.

Two parsers share one line walker:

- **Markdown**: `## N. Title` opens a parent section, `### N.M Title` opens a chunk.
- **PDF**: text is extracted with pypdf, wrapped lines are re-joined, and bare `N. Title` /
  `N.M Title` lines are recognised as headings. The PDF in the corpus is generated from markdown
  by `scripts/build_pdf.py` with reportlab so the layout is reproducible, but the ingester only
  ever sees the PDF.

Chunks containing a markdown table keep the table intact and are tagged `format: table`.
Sizes: 139 chunks, median about 50 words, longest 184 words (the fee table).

## 2. Retrieval (`app/retriever.py`)

Two rankers, fused by reciprocal rank (k = 60):

| ranker | why |
|---|---|
| dense cosine, `BAAI/bge-small-en-v1.5`, query instruction prefix, normalised vectors | paraphrase: "skip the exam for a wedding" finds "absence from examination" |
| BM25 over lower-cased alphanumeric tokens (numbers kept whole, `4.3` stays one token) | exact tokens embeddings blur: "65 per cent", "Rs. 800", "hall ticket", section numbers |

A BM25 score of zero does not vote, so a passage cannot be lifted by lexical noise. The top 6
fused passages are returned. The score shown next to each passage is always the dense cosine,
because that is the one a reader can interpret; the BM25 score is also returned for transparency.

Measured on this corpus:

| query type | best passage cosine |
|---|---|
| off-topic ("capital of France", "bake a cake") | 0.44 |
| weakest genuinely covered question ("grade for 85 marks") | 0.61 |
| adjacent but unanswered ("family wedding") | 0.55 to 0.75 |
| planted conflict pairs, both members | 0.68 to 0.89 |

So a gate at **0.45** catches nonsense without an LLM call and never blocks a real question, and
the adjacent cases go through to the model, which is the only component that can tell
"related" from "answered".

## 3. Classification (`app/pipeline.py`)

One chat completion, temperature 0, `response_format: json_object` where the model supports it
(with a fallback to prompt-only JSON and a tolerant extractor). The system prompt defines the
three outcomes and, more importantly, the negative space:

- `not_covered` explicitly includes "passages cover a related or similar situation", with
  concrete examples, and forbids "silence means permission or prohibition".
- `conflict` explicitly excludes waiver and interpretation clauses, agreeing passages, passages
  about different aspects, and general-rule-plus-procedure pairs, and requires the disagreement
  to be about what the user asked.

The model must return section ids exactly as shown in square brackets. It is told to be short
and to speak to the student.

## 4. Validation

The model's output is checked, not trusted:

| model says | check | if it fails |
|---|---|---|
| `answered` | at least one citation is a passage it was shown | downgrade to `not_covered`, note it |
| `conflict` | at least two distinct real sections in `conflict.sections` | downgrade to `answered` if it had citations, else `not_covered` |
| any | citation ids normalised (`AR 4.3`, `[AR §4.3]`, `AR§4.3` all map to `AR §4.3`) and unknown ids dropped | dropped silently |

Every downgrade is recorded in `validation_notes` on the response and shown in the UI. A test
in `tests/test_pipeline.py` proves both downgrades with a stubbed model.

### Attribution check (second pass)

The first call answers and classifies in one go, and on the hardest not-covered questions a
free model sometimes builds an answer out of a neighbouring rule ("falling ill during the exam"
answered from the missed-mid-term clause). So every `answered` gets a second, narrower call:
the question and *only the cited passages*, with one job, decide whether a cited passage
explicitly governs this situation or a different one. The prompt gives both sides examples
(a "seven days or more" rule explicitly governs a two-week absence; an illness rule does not
govern a wedding). If the verdict is "not explicit", the response becomes `not_covered`, the
former citations become the "closest" passages, and the note "attribution check" is recorded.
Costs one extra call per answered question; `VERIFY_ANSWERS=0` disables it.

### Audit-informed escalation

The corpus audit (section 6) already knows where the rulebook disagrees with itself. After
validation, if the model said `answered` and cited one member of an audited contradiction
(confidence ≥ 0.8) while the other member was also among the retrieved passages, the response is
escalated to `conflict`: both sections are named, the audit's explanation becomes the conflict
explanation, and the model's original reading is kept in the answer text. The note
"escalated to conflict" appears in `validation_notes`.

This exists because free-tier models are not deterministic: in one browser run the condonation
question came back `answered` citing `AR §4.3` alone, although the same model had flagged the
conflict in the batch evaluation. The escalation makes the behaviour stable, and it is the
system doing what the brief asks, reading all the documents at once and remembering what it
found. The audit is produced from the corpus by the model, not written by hand; if it has not
been run, nothing is escalated.

## 5. Authority

When the status is `conflict`, one more dense query ("inconsistency between these regulations
and another policy, interpretation, decision shall be final") retrieves the clause that decides
inconsistencies. On this corpus that is `AR §15.1`. The brief's third clause is always the
committee that can waive both; the UI shows it under the conflict as "who can settle this".

## 6. Corpus-wide audit (`app/audit.py`)

Contradictions are, by definition, about the same topic, so they sit close together in
embedding space. The audit:

1. computes cosine similarity between every pair of sections (139² / 2 = 9,591 pairs);
2. keeps pairs above a threshold, optionally only cross-document pairs (real rulebooks
   contradict themselves between documents far more than within one);
3. asks the LLM, per pair, whether the two clauses give incompatible rules for the same
   situation, with the same list of non-conflicts as the answering prompt;
4. caches the verdicts to `results/conflict_audit.json`, served by `GET /audit`.

On this corpus cosine ≥ 0.78 cross-document gives 50 pairs; the planted contradictions sit at
0.87, 0.90 and 0.94. `scripts/audit.py` reports how many planted pairs were found and lists any
extra pairs flagged for a human to review.

## 7. Model choice

Everything runs on free OpenRouter models. `scripts/probe_models.py` runs one question of each
response type against candidate models:

| model | probes | latency | verdict |
|---|---|---|---|
| `minimax/minimax-m3:free` | 4/4 | 1.5 to 9 s | **default** |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 4/4 | 75 to 200 s | correct but unusable live |
| `google/gemma-4-31b-it:free` | rate-limited upstream | | |
| `nvidia/nemotron-3-super-120b-a12b:free` | provider overloaded | | |
| `openrouter/free` (router) | routed one call to a content-safety classifier that replied "User Safety: safe" | | rejected |

The client retries with exponential backoff on 429 and 5xx, which free tiers need.
`AUDIT_MODEL` can point the batch audit at a different model than the live answerer.

## 8. What the system cannot do

- It cannot tell that a *positive list* answers a question by omission unless the model reads
  it that way. Three test questions of that shape were moved to an ungraded borderline list
  because both readings are defensible; see `tests/questions.json`.
- Hinglish questions are not handled specially. The embedding model is English-only; the LLM
  copes with mixed-language questions, but retrieval quality drops.
- The gate and thresholds are calibrated to this corpus and embedding model. Swap either and
  re-measure with `scripts/evaluate.py`.
