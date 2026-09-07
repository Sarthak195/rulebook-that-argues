# The Rulebook That Argues With Itself

A question-answering service over a university rulebook that **cites the clause it quotes**,
**admits when the rulebook is silent**, and **tells you when two sections disagree**.

Built for the IT Geeks vibe coding round, Problem 1. FastAPI, one `POST /ask`, a plain HTML page
on top. Everything the answer was built from is shown next to it, with section reference and
similarity score, not hidden behind a click.

> **Demo video:** _link goes here_

## What it does

Every question gets exactly one of three response types, and the system has to choose correctly:

| Status | When | What you see |
|---|---|---|
| `answered` | a passage explicitly addresses the situation | a direct answer, the cited section ids, the passages highlighted green |
| `not_covered` | the corpus is silent, **including when it covers a neighbouring situation** | a plain "the rulebook does not address this", plus the nearest clause (amber) and what it *does* cover |
| `conflict` | two sections give incompatible rules for the thing asked | both clauses quoted side by side, no winner picked, and the clause naming **who can settle it** |

The hard part is the middle row. "What if I miss the exam for a family wedding?" retrieves the
medical-absence clause with high similarity. A confident chatbot answers from it. This one says
the rulebook only covers illness and deputation, and stops.

Two things the brief did not ask for, added because they are what makes the system trustworthy:

- **Corpus-wide conflict audit** (`scripts/audit.py`, `Conflict audit` tab). Instead of waiting for
  somebody to ask the right question, the system reads every section against every similar
  section and lists the places the rulebook argues with itself. It must find the three planted
  contradictions and it must not flag the deliberate distractors (a waiver clause is not a conflict).
- **Live evaluation page** (`Evaluation` tab). The 47-question labelled test set runs in the
  browser and grades itself: response type *and* cited sections, with a confusion matrix.
  This is how the video shows "answering all your questions correctly" in one screen.

## Results

_Filled in after the evaluation run; see `results/eval_report.md`._

## How it works

```
question ─► hybrid retrieval ─► similarity gate ─► LLM classifies + answers ─► validator ─► response
             bge-small dense       < 0.45: silent,     JSON only, passages      citations must
             + BM25, fused by      no LLM call         only, no outside          exist in the
             reciprocal rank                           knowledge                 retrieved set
```

1. **Chunking** (`app/chunking.py`). Each numbered sub-section is one chunk with a stable id like
   `AR §4.3`. Regulations are already written in citation-sized units, so no sliding windows.
   Markdown headings drive the parser; the PDF is read with pypdf and its headings are recognised
   as bare `N.M Title` lines. Fee tables stay intact inside their section.
2. **Retrieval** (`app/retriever.py`). Dense cosine similarity with `BAAI/bge-small-en-v1.5`
   (local, no key) fused with BM25 by reciprocal rank. Regulations are full of exact tokens the
   embedding blurs ("65 per cent", "Rs. 800", "hall ticket"); BM25 keeps them sharp. The score
   shown to the user is always the dense cosine, because that is the number a reader can interpret.
3. **Gate**. If the best passage scores under 0.45 the corpus is silent and the LLM is not called.
   Measured on this corpus: off-topic questions peak near 0.44, the weakest covered question is 0.55.
4. **Classification** (`app/pipeline.py`). One LLM call via OpenRouter, temperature 0, JSON output,
   with a prompt that spells out what is and is not a conflict and forbids reasoning by analogy.
5. **Validation**. Citations are checked against the passages the model was shown. An `answered`
   with no valid citation is downgraded to `not_covered`; a `conflict` naming fewer than two real
   sections is downgraded. The model cannot invent a source.
6. **Authority**. On a conflict, the clause that decides inconsistencies (`AR §15.1`) is retrieved and
   shown as "who can settle this", because the brief's third clause is always the committee that can waive both.

## Corpus and test set

- `corpus/` is a rulebook for a fictional college, Shivalik Institute of Technology, Indore:
  six documents, 139 sections, about 7,200 words. Four markdown pages, a fee schedule made of
  tables, and one PDF generated from markdown so the ingester really parses a PDF.
  Details in [`corpus/README.md`](corpus/README.md).
- Three contradictions were planted across formats and are recorded in
  [`corpus/CONTRADICTIONS.md`](corpus/CONTRADICTIONS.md), along with the distractors that must
  *not* be flagged. The system never reads that file.
- [`tests/questions.json`](tests/questions.json): 18 answerable questions with expected sections,
  4 questions that hit the planted conflicts, and 25 questions the corpus cannot answer. The 25
  are deliberately adjacent: hostel-fee dues when the rule speaks of tuition dues, improving a
  passed grade when the rule covers failed courses, a calculator when the rule lists phones.

## Run it

```bash
git clone https://github.com/Sarthak195/rulebook-that-argues.git
cd rulebook-that-argues
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
copy .env.example .env            # then put your OpenRouter key in .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. First start downloads the embedding model (about 130 MB) and builds
the index in under a minute; later starts load it from `index/`.

Other commands:

```bash
python scripts/evaluate.py        # grade the 47-question test set -> results/eval_report.md
python scripts/audit.py           # corpus-wide contradiction audit  -> results/conflict_audit.md
python scripts/ingest.py          # rebuild the index after editing the corpus
python scripts/build_pdf.py       # regenerate the PDF from corpus/src
```

### API

```
POST /ask
{"question": "What CGPA do I need to keep my merit scholarship?"}
```

```json
{
  "status": "conflict",
  "answer": "The rulebook gives two different thresholds. AR §11.2 says the Merit Scholarship continues if you maintain a CGPA of not less than 7.5 ... SF §3.1 says ... not less than 8.0 ...",
  "citations": ["AR §11.2", "SF §3.1"],
  "conflict": {"sections": ["AR §11.2", "SF §3.1"], "explanation": "..."},
  "resolution_authority": {"id": "AR §15.1", "title": "Interpretation", "text": "..."},
  "passages": [{"id": "AR §11.2", "score": 0.85, "cited": true, "text": "...", "source": "01_academic_regulations.md", "format": "markdown", ...}],
  "top_similarity": 0.85, "mode": "llm", "model": "google/gemini-2.5-flash", "latency_ms": 2100
}
```

Also: `GET /health`, `GET /sections`, `GET /questions`, `GET /audit`, and `/docs` for the OpenAPI page.

## What is mocked, and other honest notes

- **Nothing in the answer path is mocked.** Embeddings run locally; the LLM is a real call through
  OpenRouter (`OPENROUTER_MODEL` in `.env`, default `google/gemini-2.5-flash`).
- **Without a key** the API still runs in an `offline-fallback` mode that returns the closest
  passage labelled as such, so the UI is usable, but it does not classify. Every response carries
  a `mode` field so you can tell.
- **The corpus is fictional.** Using a real university's regulations would have meant planting
  contradictions in someone else's text. The structure and language mirror real Indian B.Tech.
  regulations.
- **The similarity gate is tuned to this corpus and this embedding model.** Change either and
  re-measure; the number is in `app/config.py` with the measurements that justify it.
- **The LLM is the judge of "adjacent but not covered".** It is prompted hard and its citations
  are validated, but it can still be wrong; the evaluation page exists so that you can see how
  often, rather than take my word for it.

## Why this shape

IT Geeks builds Shopify Plus stores. The same failure this brief describes happens on every
merchant site: the returns page says 30 days, the FAQ says 14, and the support bot confidently
picks one. This service is corpus-agnostic. Point `CORPUS_DIR` at a folder of a store's shipping,
returns and warranty policies and you get a policy assistant that cites, abstains, and flags the
contradictions before a customer finds them.

## Layout

```
app/            chunking, retriever, llm client, pipeline, audit, FastAPI app
corpus/         the rulebook (md, tables, pdf) + CONTRADICTIONS.md answer key
scripts/        ingest, evaluate, audit, build_pdf
static/         single-page front end
tests/          questions.json, the labelled test set
results/        eval_report.md, conflict_audit.md (generated)
```

Built with Claude Code as the pair programmer; the commit history is the working log.
