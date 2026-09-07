# Evaluation report

Model `minimax/minimax-m3:free` via OpenRouter, embeddings `BAAI/bge-small-en-v1.5`, top_k=6, similarity gate=0.45.

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
Median latency 2319 ms, p90 4756 ms.

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
| N21 | not_covered | answered | NO | status answered != not_covered |
| N22 | not_covered | not_covered | yes | silent, as expected |
| N23 | not_covered | not_covered | yes | silent, as expected |
| N24 | not_covered | not_covered | yes | silent, as expected |
| N25 | not_covered | not_covered | yes | silent, as expected |

## Failures in detail

### N21: What happens if I fall ill in the middle of writing an exam?

- expected `not_covered`, got `answered` (status answered != not_covered)
- retrieved: LM §3.1, HH §8.1, EE §4.2, LM §2.4, AR §14.1, EE §3.3
- answer: If you fall ill during an exam and miss it on medical grounds, you must submit a medical certificate to the HoD within five working days of the exam. You will then be given a re-test within two weeks of rejoining classes, of the same standard and duration as the original and set by the course instructor. If your illness is likely to keep you out of classes for more than half the instructional days of the semester, the Institute Medical Officer may instead advise you to apply for a break of study.

## Borderline questions (run, not graded)

Either response type is defensible for these; see `tests/questions.json` for why.

| id | question | got | cited | answer |
|---|---|---|---|---|
| B01 | Can I use a scientific calculator in the examination hall? | answered | EE §2.1 | Scientific calculators are not listed among the items you are permitted to bring into the examination hall. Under EE §2.1, only your hall ticket, Institute identity card, blue or black ball-point pens, pencils, an eraser, a transparent water bottle, and any item expressly permitted on the question paper are allowed. If the question paper itself expressly permits a scientific calculator, you may bring it; otherwise, it is not a permitted item. |
| B02 | Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid? | answered | AR §12.2, EE §1.2 | Yes, you should get your hall ticket. The regulations only require that tuition fee dues be cleared for a hall ticket to be issued; they do not mention hostel fee dues as a condition. Under AR §12.2, a hall ticket is withheld only for outstanding tuition fee dues, and under EE §1.2, hall tickets are issued to students who have 'no outstanding tuition fee dues.' Since your tuition fee is paid, the hostel fee being unpaid does not, on the face of these rules, prevent the hall ticket from being issued. |
| B03 | Is the examination fee refunded if I withdraw from an exam? | answered | FS §4.2 | No, the examination fee is not refundable once you have commenced classes. Per the rulebook, "The examination fee and the development and laboratory fee are not refundable after the commencement of classes." |
