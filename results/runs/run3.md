# Evaluation report

Model `minimax/minimax-m3:free` via OpenRouter, embeddings `BAAI/bge-small-en-v1.5`, top_k=6, similarity gate=0.45.

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| answerable | 17 | 18 | 94% |
| conflict | 4 | 4 | 100% |
| not_covered | 23 | 25 | 92% |
| **all** | **44** | **47** | **94%** |

## Confusion matrix (rows: expected, columns: predicted)

| expected \ predicted | answered | not_covered | conflict | error |
|---|---|---|---|---|
| answered | 17 | 0 | 1 | 0 |
| not_covered | 2 | 23 | 0 | 0 |
| conflict | 0 | 0 | 4 | 0 |

Retrieval recall (every expected section inside the top-6 passages): 21/22
Median latency 2130 ms, p90 3510 ms.

## Per question

| id | expected | got | pass | detail |
|---|---|---|---|---|
| A01 | answered | answered | yes | cited ['AR §4.1'] |
| A02 | answered | answered | yes | cited ['AR §5.1'] |
| A03 | answered | answered | yes | cited ['AR §5.4'] |
| A04 | answered | answered | yes | cited ['AR §6.1'] |
| A05 | answered | answered | yes | cited ['AR §9.1'] |
| A06 | answered | answered | yes | cited ['EE §3.1'] |
| A07 | answered | answered | yes | cited ['EE §4.2', 'EE §2.2'] |
| A08 | answered | answered | yes | cited ['HH §2.1'] |
| A09 | answered | answered | yes | cited ['HH §5.2'] |
| A10 | answered | answered | yes | cited ['FS §3.1'] |
| A11 | answered | answered | yes | cited ['FS §2.1'] |
| A12 | answered | conflict | NO | status conflict != answered |
| A13 | answered | answered | yes | cited ['LM §3.2'] |
| A14 | answered | answered | yes | cited ['AR §12.2', 'EE §1.2'] |
| A15 | answered | answered | yes | cited ['AR §10.1'] |
| A16 | answered | answered | yes | cited ['AR §2.1'] |
| A17 | answered | answered | yes | cited ['HH §4.3'] |
| A18 | answered | answered | yes | cited ['LM §5.2'] |
| C01 | conflict | conflict | yes | named ['AR §4.3', 'LM §2.2'] |
| C02 | conflict | conflict | yes | named ['AR §4.3', 'LM §2.2'] |
| C03 | conflict | conflict | yes | named ['SF §6.2', 'FS §4.1'] |
| C04 | conflict | conflict | yes | named ['AR §11.2', 'SF §3.1'] |
| N01 | not_covered | not_covered | yes | silent, as expected |
| N02 | not_covered | answered | NO | status answered != not_covered |
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
| N21 | not_covered | answered | NO | status answered != not_covered |
| N22 | not_covered | not_covered | yes | silent, as expected |
| N23 | not_covered | not_covered | yes | silent, as expected |
| N24 | not_covered | not_covered | yes | silent, as expected |
| N25 | not_covered | not_covered | yes | silent, as expected |

## Failures in detail

### A12: Who is eligible for the merit-cum-means scholarship?

- expected `answered`, got `conflict` (status conflict != answered)
- retrieved: SF §2.2, SF §2.1, SF §3.1, AR §11.1, AR §11.2, SF §2.3
- answer: The rulebook contradicts itself on this point. AR §11.2 requires a CGPA of not less than 7.5 for continuation of the Merit Scholarship, whereas SF §3.1 requires a CGPA of not less than 8.0 for the same continuation condition. Both clauses address the same situation (continuing an awarded Merit Scholarship into the next academic year) but set different minimum CGPA thresholds. (Found by the corpus-wide audit, confidence 0.97.) Read on its own, SF §3.1 would give: You are eligible for the Merit-cum-Means Scholarship if your annual family income from all sources does not exceed Rs. 3,00,000 and you have a CGPA of at least 7.0 at the end of the preceding academic year (or, if you are a first-year student, at least 80 per cent marks in the qualifying examination). The scholarship is a waiver of 25% of the tuition fee, and you must attach an income certificate from a Tehsildar (or equivalent officer) that is not older than six months. Additionally, to keep the scholarship, you must maintain a CGPA of at least 7.0 at the end of each semester.

### N02: Can I get a re-test if I missed a mid-term test for a job interview?

- expected `not_covered`, got `answered` (status answered != not_covered)
- retrieved: EE §3.3, AR §9.1, LM §3.3, AR §9.3, AR §9.2, SF §3.1
- answer: It depends on whether the interview was arranged through the Institute's Training and Placement Cell. Under LM §3.3, if it was so arranged, you will be marked present for the duration of the interview, so you effectively don't 'miss' the test in the first place — no re-test is needed. The re-test provision in EE §3.3 applies only when a mid-term test is missed on medical grounds with a medical certificate submitted to the HoD within five working days; a job interview is not covered by that clause.

### N21: What happens if I fall ill in the middle of writing an exam?

- expected `not_covered`, got `answered` (status answered != not_covered)
- retrieved: LM §3.1, HH §8.1, EE §4.2, LM §2.4, AR §14.1, EE §3.3
- answer: If you fall ill during an exam itself, the rulebook's only specific exam-related sickness provision covers missed mid-term tests, not an illness that begins mid-exam. Per EE §3.3, if you miss a mid-term test on medical grounds and submit a medical certificate to the HoD within five working days, you will be given a re-test within two weeks of rejoining classes, of the same standard and duration as the original.

## Borderline questions (run, not graded)

Either response type is defensible for these; see `tests/questions.json` for why.

| id | question | got | cited | answer |
|---|---|---|---|---|
| B01 | Can I use a scientific calculator in the examination hall? | not_covered |  | The rulebook does not mention scientific calculators either as permitted or prohibited. Under EE §2.1, you may bring any item that is 'expressly permitted on the question paper,' so whether a scientific calculator is allowed depends on what your specific question paper states. You should check the instructions printed on the question paper for your examination. |
| B02 | Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid? | not_covered |  | The rulebook does not address whether an unpaid hostel fee affects hall-ticket issuance. The clauses on hall tickets (AR §12.2 and EE §1.2) only link the hall ticket to outstanding tuition fee dues, not to hostel rent or mess charges. |
| B03 | Is the examination fee refunded if I withdraw from an exam? | answered | FS §4.2 | No, the examination fee is not refundable if you withdraw. Per [FS §4.2], 'The examination fee and the development and laboratory fee are not refundable after the commencement of classes.' |
