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
Median latency 1953 ms, p90 2671 ms.

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
- answer: If you fall ill during an exam, you should inform the hostel supervisor or Warden immediately so that the Institute Health Centre (open 8:00 a.m.–8:00 p.m.) or the on-call doctor/ambulance can attend to you. Note that the Examination Regulations also allow a missed mid-term test on medical grounds to be re-taken within two weeks of rejoining classes, provided you submit a medical certificate to the HoD within five working days of the test.

## Borderline questions (run, not graded)

Either response type is defensible for these; see `tests/questions.json` for why.

| id | question | got | cited | answer |
|---|---|---|---|---|
| B01 | Can I use a scientific calculator in the examination hall? | not_covered |  | The rulebook does not address whether a scientific calculator may be used in the examination hall. The closest passage, EE §2.1, lists permitted materials (hall ticket, ID card, pens, pencils, eraser, transparent water bottle, and any item expressly permitted on the question paper) but does not specifically mention calculators. |
| B02 | Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid? | not_covered |  | The rulebook does not address whether unpaid hostel fees will prevent you from getting your hall ticket. The closest passage addresses only outstanding tuition fee dues as a bar to the hall ticket, not hostel fees. See [AR §12.2] and [EE §1.2], which condition the hall ticket on payment of tuition fee dues. |
| B03 | Is the examination fee refunded if I withdraw from an exam? | answered | FS §4.2 | No. According to the Fee Schedule and Refund Rules, the examination fee is not refundable after the commencement of classes. This applies if you withdraw from the programme/exam after classes have begun. |
