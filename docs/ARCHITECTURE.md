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

### Free models are volatile, so the client uses a chain

On the morning of 8 September, twelve hours after the evaluation above, OpenRouter withdrew
`minimax/minimax-m3:free` ("This model is unavailable for free. The paid version is available
now"). Every call failed, the API returned 502, and the Cloudflare tunnel replaced the 502 with
an HTML page, which surfaced in the browser as a JSON parse error. Three changes followed:

- **A model chain.** `OPENROUTER_MODEL` is tried first, then each of `OPENROUTER_FALLBACKS`. A
  model that answers "unavailable", 402, 403 or 404 is parked for ten minutes; one that fails
  after its retries is parked for ninety seconds. The concrete model that answered is returned
  in every response's `model` field, and `GET /health` shows the chain with each model's state.
- **Errors are always JSON.** A global handler turns any unhandled exception into
  `{"detail": ...}`, and the front end reads the body as text first, so a proxy's HTML error page
  is shown as a readable message instead of a parse error.
- **The probe script disables the chain** while measuring, so a dead model is reported as dead
  rather than silently answered by its fallback.

Later the same morning the OpenRouter key hit its free-tier quota of 50 requests per day, so the
client became provider-agnostic: any OpenAI-compatible endpoint can sit in the chain. The order
is `PROVIDER_ORDER`, default `codecraft,groq,gemini,openrouter`, and a provider without a key is
skipped. `scripts/liveness.py` pings every model a provider lists (one tiny call each, in
parallel) and `scripts/probe_models.py provider:model` runs the four-question quality probe.

Final choice for the submission: **Groq, `openai/gpt-oss-120b`** on the free tier, 4/4 on the
probe at 1.4 to 2.0 s per answer, with `openai/gpt-oss-20b` and `qwen/qwen3.8-27b` behind it,
then the OpenRouter free models.

### Pacing and spread

Groq's free tier allows 1,000 requests a day but only **8,000 tokens per minute per model**, and
a question costs about 2,500 tokens (system prompt, six passages, answer) plus the verification
call. Two rules keep batch work inside that:

- **At most two calls in flight per provider** (a semaphore in the client). A burst of parallel
  questions queues instead of turning into 429s, retries and parked models. A 429 after retries
  parks the model for 20 s, not 90.
- **Spread mode** for batch callers (`spread: true` on `/ask`, `--spread` on `evaluate.py`, on by
  default in the Evaluation tab): consecutive calls rotate round-robin across the live models of
  `SPREAD_PROVIDERS` (default `groq`), so three workers hit three separate per-minute buckets.
  Single questions keep the plain order and always get the preferred model when it is up.
  Adding `openrouter` to `SPREAD_PROVIDERS` uses its free models too, but on a free-tier key that
  is 50 requests a day, less than one evaluation run, so it is off by default.

Measured on the 47-question set (see `docs/EVALUATION.md`): accuracy is unchanged with spread
on, because the two smaller Groq models also pass the probe; the smaller models simply answer
a share of the questions.

Three more rules, each learned from a stack dump of the deployed service (`py-spy dump`) while
the evaluation ran and a live question hung:

- **A slot is held only while a request is in flight, never during a backoff sleep.** The
  first version held it through the sleep, so two batch workers asleep on a 429 blocked every
  other thread on the semaphore.
- **Route on the provider's bucket headers.** Groq reports remaining tokens and the refill
  time on every response. A batch call picks a model with a call's worth of headroom, or waits
  for the earliest refill; a live question prefers a sibling model with headroom over waiting
  for a drained favourite. Firing at a drained bucket and sleeping on the 429 was where the
  time went. A 429 that still happens gets at most three attempts with waits capped at 15 s,
  then the model is parked for 20 s.
- **Live questions come first.** Batch work pauses while any live question is waiting for a
  model, and batch calls never spill onto fallback providers (their daily quotas are small);
  they wait for their own pool to refill instead.

A gateway that is down (CodeCraft during its outage) must not slow the chain: a 5xx gets one
quick retry, and one 5xx parks every model of that provider for 90 s.

**Several keys per provider.** `GEMINI_API_KEYS` (and the same for the other providers) takes
a comma-separated list. Each key becomes its own quota slot: entries are named
`gemini#2/gemini-2.5-flash`, rate limits, buckets and parking are tracked per slot, and the
spread pool rotates across slots as well as models, so a batch run's throughput scales with
the number of keys. Ordering is model-major, so the preferred model on every key comes before
any fallback model. Google's free quota is per project; several projects under one account is
the intended way to get several quotas. Groq's catalogue had also changed since the code was first
written (Llama 3.3 70B was gone), which is why the liveness sweep exists: assumptions about
which models a provider serves today do not survive a night.

## 8. What the system cannot do

- It cannot tell that a *positive list* answers a question by omission unless the model reads
  it that way. Three test questions of that shape were moved to an ungraded borderline list
  because both readings are defensible; see `tests/questions.json`.
- Hinglish questions are not handled specially. The embedding model is English-only; the LLM
  copes with mixed-language questions, but retrieval quality drops.
- The gate and thresholds are calibrated to this corpus and embedding model. Swap either and
  re-measure with `scripts/evaluate.py`.
