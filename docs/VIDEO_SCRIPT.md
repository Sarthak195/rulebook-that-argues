# Video script (target 2:30 to 3:00)

Record the browser at the deployed URL or `http://127.0.0.1:8000`. Keep the passages panel
visible the whole time; that is the point of the project. Talk plainly. Every claim in the
script is something the screen shows at that moment.

Before recording:
- open the app in one tab, the GitHub repo in a second tab, `results/conflict_audit.md` is not
  needed (the Conflict audit tab shows it)
- refresh the app once so the header shows `139 sections · bge-small · minimax/minimax-m3:free`
- **the `Evaluation` tab finishes in about 35 seconds on the deployed Mistral setup**, so you can
  click `Run all questions` on camera and watch it fill in; the finished table also stays on the
  tab across refreshes. Run it once before recording to be sure the key is healthy.
- single questions answer in about 2 seconds; a question that needs the verification pass takes 3 to 4

---

**0:00 Title card / header** (10 s)

> This is The Rulebook That Argues With Itself. It answers questions over a university
> rulebook: six documents, 139 sections, markdown pages, a fee table and a PDF. Every answer
> shows the clauses it came from, on the right, with the similarity score. It has three
> possible responses: answered with citations, not covered, and conflict. The job is to pick
> the right one.

**0:10 Start the evaluation** (15 s)

Click `Evaluation`, click `Run all questions`. Rows start filling in within seconds.

> This is the labelled test set, 47 questions, graded on the server: the response type has to
> be right and the cited sections have to be the expected ones. It takes about half a minute;
> I will come back to it.

Click back to `Ask`.

**0:25 Answered** (25 s)

Type: `What is the minimum attendance required to appear for the end-semester examination?`

> Answered. 75 per cent, from Academic Regulations section 4.1. The passage it used is green on
> the right, cosine 0.85. The other passages were retrieved but not used, and it says so.

**0:50 Not covered, the hard kind** (35 s)

Type: `What happens if I miss the end-semester exam because of a family wedding?`

> This is the case that breaks most chatbots. The rulebook covers absence for illness and for
> official deputation, and that clause is retrieved at 0.60 similarity. A confident bot would
> answer from it. This one says not covered, tells you what the nearest clause does cover, and
> marks it amber: closest, still silent. The prompt forbids reasoning by analogy, and the
> validator would downgrade an answer that had no real citation anyway.

**1:25 Conflict** (40 s)

Type: `My attendance is 58% because I was hospitalised for three weeks. Can the shortage be condoned?`

> Conflict. Academic Regulations 4.3 says medical shortage can be condoned only down to 65 per
> cent, and adds "under no circumstances" below that. The Leave and Medical Policy, a different
> document, says 55 per cent. Both are quoted, no winner is picked. And it shows who can settle
> it: section 15.1 makes the Vice-Chancellor the final authority on inconsistencies.

Optionally one more, fast: `If I withdraw my admission before classes begin, how much of my tuition fee will be refunded?`

> Same thing across formats: the fee table says 100 per cent, the scholarship PDF says 90.

**2:05 Conflict audit** (25 s)

Click `Conflict audit`.

> Nobody reads all six documents at once, so the system does. It compared every section with
> every similar section in another document and had the model judge each pair. It found the
> three contradictions I planted, and it cleared the distractors: the clause that lets the
> Academic Council waive rules is not a contradiction, and the audit knows that.

**2:05 (optional, if you have 25 s to spare) The agent**

Click `Agent`, click the first example chip (58% attendance after hospital, plus a missed mid-term).

> For questions with several parts there is an agent. It plans: searches the rulebook with its
> own queries, opens the sections it needs, checks the list of known contradictions, then
> answers. The steps are on the right. It can only cite sections it actually opened, and the
> same validators run on its answer.

**2:30 Evaluation results** (20 s)

Click `Evaluation`; the run has finished.

> Back to the test set. 18 answerable, 4 conflicts, 25 questions the corpus cannot answer,
> including the adjacent ones. This is the confusion matrix. Everything runs on Mistral's free
> plan, three small models sharing the work; the two misses are the cautious kind, "not
> covered" where the rule did apply, and they are recorded, not hidden. Embeddings are local.

Read the pass count off the screen. Do not quote a number from memory.

**2:50 Repo** (10 s)

Switch to the GitHub tab, scroll the README once, show the commit list.

> Repository, README with how to run and what is mocked, which is nothing, and the commit
> history from the corpus onward. Thanks.

---

## If something goes wrong on camera

- A free-model answer takes more than 10 seconds: say "free tier, it retries on rate limits"
  and wait. The client backs off automatically.
- The evaluation run has one or two failures: click `show failures only`, read the detail
  column aloud, and say whether you agree with the model. Judges trust that more than 47/47.
- The tunnel URL is down: use the plain IP URL or localhost. Both are in `docs/DEPLOYMENT.md`.

## Upload

Google Drive, "Anyone with the link", paste the link in the portal after the repository link.
