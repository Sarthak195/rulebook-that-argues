# Evaluation report

Models that answered: `gemini/gemini-3.1-flash-lite`, `gemini/gemini-3.5-flash-lite`; chain head `gemini/gemini-3.5-flash-lite`; spread=on; 4 workers; wall time 182s. Embeddings `BAAI/bge-small-en-v1.5`, top_k=6, similarity gate=0.45.

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| answerable | 18 | 18 | 100% |
| conflict | 4 | 4 | 100% |
| not_covered | 24 | 25 | 96% |
| **all** | **46** | **47** | **98%** |

## Confusion matrix (rows: expected, columns: predicted)

| expected \ predicted | answered | not_covered | conflict | error |
|---|---|---|---|---|
| answered | 18 | 0 | 0 | 0 |
| not_covered | 1 | 24 | 0 | 0 |
| conflict | 0 | 0 | 4 | 0 |

Retrieval recall (every expected section inside the top-6 passages): 21/22
Median latency 3530 ms, p90 7618 ms.

## Per question

| id | expected | got | pass | detail |
|---|---|---|---|---|
| A01 | answered | answered | yes | cited ['AR §4.1'] |
| A02 | answered | answered | yes | cited ['AR §5.1'] |
| A03 | answered | answered | yes | cited ['AR §5.4'] |
| A04 | answered | answered | yes | cited ['AR §6.1'] |
| A05 | answered | answered | yes | cited ['AR §9.1'] |
| A06 | answered | answered | yes | cited ['EE §3.1'] |
| A07 | answered | answered | yes | cited ['EE §4.2'] |
| A08 | answered | answered | yes | cited ['HH §2.1'] |
| A09 | answered | answered | yes | cited ['HH §5.2'] |
| A10 | answered | answered | yes | cited ['FS §3.1'] |
| A11 | answered | answered | yes | cited ['FS §2.1'] |
| A12 | answered | answered | yes | cited ['SF §2.2'] |
| A13 | answered | answered | yes | cited ['LM §3.2'] |
| A14 | answered | answered | yes | cited ['AR §12.2', 'EE §1.2'] |
| A15 | answered | answered | yes | cited ['AR §10.1'] |
| A16 | answered | answered | yes | cited ['AR §2.1'] |
| A17 | answered | answered | yes | cited ['HH §4.3'] |
| A18 | answered | answered | yes | cited ['LM §5.2'] |
| C01 | conflict | conflict | yes | named ['AR §4.3', 'LM §2.2'] |
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
| N10 | not_covered | not_covered | yes | silent, as expected |
| N11 | not_covered | not_covered | yes | silent, as expected |
| N12 | not_covered | not_covered | yes | silent, as expected |
| N13 | not_covered | not_covered | yes | silent, as expected |
| N14 | not_covered | not_covered | yes | silent, as expected |
| N15 | not_covered | not_covered | yes | silent, as expected |
| N16 | not_covered | not_covered | yes | silent, as expected |
| N17 | not_covered | not_covered | yes | silent, as expected |
| N18 | not_covered | not_covered | yes | silent, as expected |
| N19 | not_covered | not_covered | yes | silent, as expected |
| N20 | not_covered | not_covered | yes | silent, as expected |
| N21 | not_covered | not_covered | yes | silent, as expected |
| N22 | not_covered | not_covered | yes | silent, as expected |
| N23 | not_covered | not_covered | yes | silent, as expected |
| N24 | not_covered | not_covered | yes | silent, as expected |
| N25 | not_covered | answered | NO | status answered != not_covered |

## Failures in detail

### N25: What is the punishment for plagiarism in a project report?

- expected `not_covered`, got `answered` (status answered != not_covered)
- retrieved: AR §5.5, EE §4.2, AR §13.1, SF §7.1, AR §9.1, AR §13.2
- answer: The use of unfair means in any evaluation is handled according to the Examination and Evaluation Regulations. Under these regulations, a first offence results in the cancellation of the examination for that course and the assignment of an F grade. Subsequent offences carry progressively harsher penalties, including the cancellation of all semester examinations for a second offence and expulsion for a third offence.

## Borderline questions (run, not graded)

Either response type is defensible for these; see `tests/questions.json` for why.

| id | question | got | cited | answer |
|---|---|---|---|---|
| B01 | Can I use a scientific calculator in the examination hall? | not_covered |  | The rulebook does not address this situation. The closest clause covers a related case: You may only bring items into the examination hall that are expressly permitted on the question paper, in addition to the hall ticket, identity card, writing implements, and a transparent water bottle. As a scientific calculator is not listed as a generally permitted item, you may only use one if it is expressly permitted on your specific question paper. |
| B02 | Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid? | not_covered |  | The rulebook does not address whether unpaid hostel fees affect the issuance of a hall ticket. The existing regulations only specify that hall tickets are withheld due to outstanding tuition fee dues. |
| B03 | Is the examination fee refunded if I withdraw from an exam? | answered | FS §4.2 | The examination fee is not refundable after the commencement of classes. The provided regulations do not specify a refund policy for examination fees if withdrawal occurs before the commencement of classes. |
