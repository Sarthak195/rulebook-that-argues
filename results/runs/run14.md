# Evaluation report

Models that answered: `mistral/ministral-14b-2512`, `mistral/ministral-8b-2512`, `mistral/open-mistral-nemo`; chain head `mistral/ministral-8b-2512`; spread=on; 6 workers; wall time 30s. Embeddings `BAAI/bge-small-en-v1.5`, top_k=6, similarity gate=0.45.

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| answerable | 16 | 18 | 89% |
| conflict | 4 | 4 | 100% |
| not_covered | 25 | 25 | 100% |
| **all** | **45** | **47** | **96%** |

## Confusion matrix (rows: expected, columns: predicted)

| expected \ predicted | answered | not_covered | conflict | error |
|---|---|---|---|---|
| answered | 16 | 2 | 0 | 0 |
| not_covered | 0 | 25 | 0 | 0 |
| conflict | 0 | 0 | 4 | 0 |

Retrieval recall (every expected section inside the top-6 passages): 21/22
Median latency 2608 ms, p90 4361 ms.

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
| A15 | answered | not_covered | NO | status not_covered != answered |
| A16 | answered | answered | yes | cited ['AR §2.1'] |
| A17 | answered | not_covered | NO | status not_covered != answered |
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
| N25 | not_covered | not_covered | yes | silent, as expected |

## Failures in detail

### A15: How long can a break of study be?

- expected `answered`, got `not_covered` (status not_covered != answered)
- retrieved: AR §10.1, AR §10.2, AR §10.3, LM §2.4, EE §1.1, AR §2.1
- answer: The rulebook does not address this situation. The closest clause covers a related case: You may be granted a break of study for either **one semester or one academic year**, but only once during your B.Tech. programme and **only on medical grounds** certified by the Institute Medical Officer and approved by the Dean. No other grounds or longer breaks are permitted.

### A17: Can I get a mess rebate if I go home for two weeks?

- expected `answered`, got `not_covered` (status not_covered != answered)
- retrieved: HH §4.3, HH §4.1, HH §4.2, HH §7.2, AR §3.4, FS §4.2
- answer: The rulebook does not address whether a mess rebate applies for a two-week absence. The closest passage covers rebates for absences of **seven days or more** only.

## Borderline questions (run, not graded)

Either response type is defensible for these; see `tests/questions.json` for why.

| id | question | got | cited | answer |
|---|---|---|---|---|
| B01 | Can I use a scientific calculator in the examination hall? | not_covered |  | The rulebook does not specify whether scientific calculators are permitted in the examination hall. The closest sections only mention permitted and prohibited materials like pens, identity cards, and communication devices. |
| B02 | Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid? | not_covered |  | The rulebook does not specify whether a hall ticket will be issued if only the hostel fee is unpaid while the tuition fee is paid. The closest passages address hall ticket issuance only in relation to outstanding tuition fees, not hostel fees. |
| B03 | Is the examination fee refunded if I withdraw from an exam? | not_covered |  | The rulebook does not address whether the examination fee is refunded if you withdraw from an exam. The closest passage covers refunds for tuition fees and caution deposits upon withdrawal from the programme or before classes commence. |
