# Evaluation report

Models that answered: `mistral/ministral-14b-2512`, `mistral/ministral-8b-2512`, `mistral/open-mistral-nemo`; chain head `mistral/ministral-8b-2512`; spread=on; 6 workers; wall time 40s. Embeddings `BAAI/bge-small-en-v1.5`, top_k=6, similarity gate=0.45.

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| answerable | 29 | 30 | 97% |
| conflict | 4 | 4 | 100% |
| not_covered | 25 | 25 | 100% |
| **all** | **58** | **59** | **98%** |

## Confusion matrix (rows: expected, columns: predicted)

| expected \ predicted | answered | not_covered | conflict | error |
|---|---|---|---|---|
| answered | 29 | 1 | 0 | 0 |
| not_covered | 0 | 25 | 0 | 0 |
| conflict | 0 | 0 | 4 | 0 |

Retrieval recall (every expected section inside the top-6 passages): 32/34
Median latency 2408 ms, p90 3593 ms.

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
| A17 | answered | not_covered | NO | status not_covered != answered |
| A18 | answered | answered | yes | cited ['LM §5.2'] |
| A19 | answered | answered | yes | cited ['AR §2.2'] |
| A20 | answered | answered | yes | cited ['EE §7.1'] |
| A21 | answered | answered | yes | cited ['EE §6.1'] |
| A22 | answered | answered | yes | cited ['EE §4.2'] |
| A23 | answered | answered | yes | cited ['SG §2.2'] |
| A24 | answered | answered | yes | cited ['SG §2.3'] |
| A25 | answered | answered | yes | cited ['SG §3.1'] |
| A26 | answered | answered | yes | cited ['SG §3.3'] |
| A27 | answered | answered | yes | cited ['SG §4.2'] |
| A28 | answered | answered | yes | cited ['SG §5.2'] |
| A29 | answered | answered | yes | cited ['SG §4.4'] |
| A30 | answered | answered | yes | cited ['SG §6.1'] |
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

### A17: Can I get a mess rebate if I go home for two weeks?

- expected `answered`, got `not_covered` (status not_covered != answered)
- retrieved: HH §4.3, HH §4.1, HH §4.2, HH §7.2, AR §3.4, FS §4.2
- answer: The rulebook does not address this situation. The closest clause covers a related case: No, you are not eligible for a mess rebate if you go home for two weeks. The rule states that a rebate is only admissible for absences of seven days or more, and your absence of two weeks (14 days) does qualify. However, the rebate is only granted if the absence is recorded in advance in the leave register and the rebate form is submitted within seven days of your return.

## Borderline questions (run, not graded)

Either response type is defensible for these; see `tests/questions.json` for why.

| id | question | got | cited | answer |
|---|---|---|---|---|
| B01 | Can I use a scientific calculator in the examination hall? | not_covered |  | The rulebook does not specify whether a scientific calculator is permitted in the examination hall. It only lists permitted items like pens, pencils, and a transparent water bottle, and prohibits communication devices, books, or notes. |
| B02 | Will I get my hall ticket if my hostel fee is unpaid but my tuition fee is paid? | not_covered |  | The rulebook does not address whether a hall ticket will be issued if only the hostel fee is unpaid while the tuition fee is paid. The closest passages cover hall ticket issuance only in relation to outstanding tuition fee dues or attendance requirements. |
| B03 | Is the examination fee refunded if I withdraw from an exam? | not_covered |  | The rulebook does not address whether the examination fee is refunded if you withdraw from an exam. The closest passages cover refunds for tuition fees, caution deposits, hostel charges, and scholarship waivers, but not specifically the examination fee on withdrawal from an exam. |
