# Evaluation report

Models that answered: `gemini#1/gemma-4-26b-a4b-it`, `gemini#2/gemma-4-26b-a4b-it`; chain head `gemini#1/gemma-4-26b-a4b-it`; spread=on; 4 workers; wall time 831s. Embeddings `BAAI/bge-small-en-v1.5`, top_k=6, similarity gate=0.45.

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| answerable | 16 | 18 | 89% |
| conflict | 3 | 4 | 75% |
| not_covered | 23 | 25 | 92% |
| **all** | **42** | **47** | **89%** |

## Confusion matrix (rows: expected, columns: predicted)

| expected \ predicted | answered | not_covered | conflict | error |
|---|---|---|---|---|
| answered | 16 | 0 | 0 | 2 |
| not_covered | 0 | 23 | 0 | 2 |
| conflict | 0 | 0 | 3 | 1 |

Retrieval recall (every expected section inside the top-6 passages): 19/19
Median latency 10088 ms, p90 123515 ms.

## Per question

| id | expected | got | pass | detail |
|---|---|---|---|---|
| A01 | answered | answered | yes | cited ['AR §4.1'] |
| A02 | answered | answered | yes | cited ['AR §5.1'] |
| A03 | answered | answered | yes | cited ['AR §5.4'] |
| A04 | answered | answered | yes | cited ['AR §6.1'] |
| A05 | answered | error | NO | LLMError: model returned malformed JSON (Extra data at 281): '<thought>*   Question: "How many days do I have to apply for re-evaluation after results are declared?"\n    *   Passages:\n        *   [AR §9.1]: "A student who is not satisfied with the marks awarded ' |
| A06 | answered | answered | yes | cited ['EE §3.1'] |
| A07 | answered | answered | yes | cited ['EE §4.2'] |
| A08 | answered | answered | yes | cited ['HH §2.1'] |
| A09 | answered | answered | yes | cited ['HH §5.2'] |
| A10 | answered | answered | yes | cited ['FS §3.1'] |
| A11 | answered | answered | yes | cited ['FS §2.1'] |
| A12 | answered | answered | yes | cited ['SF §2.2'] |
| A13 | answered | answered | yes | cited ['LM §3.2'] |
| A14 | answered | error | NO | LLMError: model did not return JSON: '<thought>*   Question: "Will I get my hall ticket if I have not paid my tuition fees?"\n    *   Passages provided:\n        *   [AR §12.2]: "A student who has outstanding tuition fee dues on the last da' |
| A15 | answered | answered | yes | cited ['AR §10.1'] |
| A16 | answered | answered | yes | cited ['AR §2.1'] |
| A17 | answered | answered | yes | cited ['HH §4.3'] |
| A18 | answered | answered | yes | cited ['LM §5.2'] |
| C01 | conflict | error | NO | LLMError: model did not return JSON: '<thought>*   Question: "My attendance is 58% because I was hospitalised for three weeks. Can the shortage be condoned?"\n    *   Key facts: Attendance = 58%. Reason = Hospitalization (medical grounds).' |
| C02 | conflict | conflict | yes | named ['LM §2.2', 'AR §4.3'] |
| C03 | conflict | conflict | yes | named ['SF §6.2', 'FS §4.1'] |
| C04 | conflict | conflict | yes | named ['AR §11.2', 'SF §3.1'] |
| N01 | not_covered | not_covered | yes | silent, as expected |
| N02 | not_covered | not_covered | yes | silent, as expected |
| N03 | not_covered | not_covered | yes | silent, as expected |
| N04 | not_covered | not_covered | yes | silent, as expected |
| N05 | not_covered | not_covered | yes | silent, as expected |
| N06 | not_covered | not_covered | yes | silent, as expected |
| N07 | not_covered | not_covered | yes | silent, as expected |
| N08 | not_covered | not_covered | yes | silent, as expected |
| N09 | not_covered | not_covered | yes | silent, as expected |
| N10 | not_covered | error | NO | LLMError: model did not return JSON: '<thought>*   Question: "Are grace marks given if I fail a course by one or two marks?"\n    *   Passages provided:\n        *   [AR §6.1]: Grading table (F grade is below 40 total or below 30 in end-sem' |
| N11 | not_covered | not_covered | yes | silent, as expected |
| N12 | not_covered | not_covered | yes | silent, as expected |
| N13 | not_covered | not_covered | yes | silent, as expected |
| N14 | not_covered | not_covered | yes | silent, as expected |
| N15 | not_covered | not_covered | yes | silent, as expected |
| N16 | not_covered | not_covered | yes | silent, as expected |
| N17 | not_covered | not_covered | yes | silent, as expected |
| N18 | not_covered | not_covered | yes | silent, as expected |
| N19 | not_covered | not_covered | yes | silent, as expected |
| N20 | not_covered | error | NO | LLMError: model did not return JSON: '<thought>*   Question: "Can I re-appear in a course I have already passed to improve my grade?"\n    *   Passages provided:\n        *   [AR §9.1]: Re-evaluation process for theory courses if unsatisfie' |
| N21 | not_covered | not_covered | yes | silent, as expected |
| N22 | not_covered | not_covered | yes | silent, as expected |
| N23 | not_covered | not_covered | yes | silent, as expected |
| N24 | not_covered | not_covered | yes | silent, as expected |
| N25 | not_covered | not_covered | yes | silent, as expected |

## Failures in detail

### A05: How many days do I have to apply for re-evaluation after results are declared?

- expected `answered`, got `error` (LLMError: model returned malformed JSON (Extra data at 281): '<thought>*   Question: "How many days do I have to apply for re-evaluation after results are declared?"\n    *   Passages:\n        *   [AR §9.1]: "A student who is not satisfied with the marks awarded ')
- retrieved: 
- answer: 

### A14: Will I get my hall ticket if I have not paid my tuition fees?

- expected `answered`, got `error` (LLMError: model did not return JSON: '<thought>*   Question: "Will I get my hall ticket if I have not paid my tuition fees?"\n    *   Passages provided:\n        *   [AR §12.2]: "A student who has outstanding tuition fee dues on the last da')
- retrieved: 
- answer: 

### C01: My attendance is 58% because I was hospitalised for three weeks. Can the shortage be condoned?

- expected `conflict`, got `error` (LLMError: model did not return JSON: '<thought>*   Question: "My attendance is 58% because I was hospitalised for three weeks. Can the shortage be condoned?"\n    *   Key facts: Attendance = 58%. Reason = Hospitalization (medical grounds).')
- retrieved: 
- answer: 

### N10: Are grace marks given if I fail a course by one or two marks?

- expected `not_covered`, got `error` (LLMError: model did not return JSON: '<thought>*   Question: "Are grace marks given if I fail a course by one or two marks?"\n    *   Passages provided:\n        *   [AR §6.1]: Grading table (F grade is below 40 total or below 30 in end-sem')
- retrieved: 
- answer: 

### N20: Can I re-appear in a course I have already passed to improve my grade?

- expected `not_covered`, got `error` (LLMError: model did not return JSON: '<thought>*   Question: "Can I re-appear in a course I have already passed to improve my grade?"\n    *   Passages provided:\n        *   [AR §9.1]: Re-evaluation process for theory courses if unsatisfie')
- retrieved: 
- answer: 

## Borderline questions (run, not graded)

Either response type is defensible for these; see `tests/questions.json` for why.

| id | question | got | cited | answer |
|---|---|---|---|---|
| B01 | Can I use a scientific calculator in the examination hall? | not_covered |  | The rulebook does not address whether you can use a scientific calculator in the examination hall. The regulations do specify which items are permitted, such as hall tickets, identity cards, and pens, as well as which items are prohibited, such as mobile phones and books. |
| B02 | Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid? | not_covered |  | The rulebook does not address whether unpaid hostel fees affect your hall ticket issuance. The existing regulations only specify that hall tickets are withheld for students who have outstanding tuition fee dues [AR §12.2, EE §1.2]. |
| B03 | Is the examination fee refunded if I withdraw from an exam? | not_covered |  | The rulebook does not address whether the examination fee is refunded if you withdraw from an exam. The closest passage, [FS §4.2], states that the examination fee is not refundable after the commencement of classes in the context of withdrawing admission. |
