# Evaluation report

Model `nvidia/nemotron-3-super-120b-a12b:free` via OpenRouter, embeddings `BAAI/bge-small-en-v1.5`, top_k=6, similarity gate=0.45.

| Category | Passed | Total | Accuracy |
|---|---|---|---|
| answerable | 18 | 18 | 100% |
| conflict | 0 | 4 | 0% |
| not_covered | 0 | 25 | 0% |
| **all** | **18** | **47** | **38%** |

## Confusion matrix (rows: expected, columns: predicted)

| expected \ predicted | answered | not_covered | conflict | error |
|---|---|---|---|---|
| answered | 18 | 0 | 0 | 0 |
| not_covered | 0 | 0 | 0 | 25 |
| conflict | 0 | 0 | 0 | 4 |

Retrieval recall (every expected section inside the top-6 passages): 17/18
Median latency 94476 ms, p90 95141 ms.

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
| C01 | conflict | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| C02 | conflict | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| C03 | conflict | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| C04 | conflict | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N01 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N02 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N03 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N04 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N05 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N06 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N07 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N08 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N09 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N10 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N11 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N12 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N13 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N14 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N15 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N16 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N17 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N18 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N19 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N20 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N21 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N22 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N23 | not_covered | error | NO | LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat |
| N24 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |
| N25 | not_covered | error | NO | LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi / dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5 |

## Failures in detail

### C01: My attendance is 58% because I was hospitalised for three weeks. Can the shortage be condoned?

- expected `conflict`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### C02: What is the lowest attendance percentage that can still be condoned on medical grounds?

- expected `conflict`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### C03: If I withdraw my admission before classes begin, how much of my tuition fee will be refunded?

- expected `conflict`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### C04: What CGPA do I need to maintain to keep my merit scholarship?

- expected `conflict`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N01: What happens if I miss the end-semester exam because of a family wedding?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N02: Can I get a re-test if I missed a mid-term test for a job interview?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N03: Can I change my branch after the first year?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N04: Is there a dress code for laboratory sessions?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N05: Can a day scholar eat in the hostel mess by paying per meal?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N06: Are pets allowed in the hostel?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N07: What is the fee for a duplicate identity card?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N08: Can I get academic credit for a summer internship?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N09: Is there a scholarship for students from the EWS category?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N10: Are grace marks given if I fail a course by one or two marks?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N11: Can I write my answers in Hindi instead of English in the end-semester exam?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N12: What happens if there is a printing error in the question paper?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N13: How do I get a duplicate degree certificate if I lose the original?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N14: How many books can I borrow from the library at a time?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N15: What is the procedure to transfer to another university mid-course?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N16: Can I keep a two-wheeler in the hostel parking?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N17: Is there a fee concession if my sibling also studies at the institute?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N18: How do I get a bonafide student certificate for my bank loan?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N19: What is the minimum CGPA to be eligible for campus placements?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N20: Can I re-appear in a course I have already passed to improve my grade?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N21: What happens if I fall ill in the middle of writing an exam?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N22: How do I get my name corrected on the grade card?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N23: Can I audit a course without earning credits?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> nvidia/nemotron-3-super-120b-a12b:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | poolside/laguna-s-2.1:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-Rat)
- retrieved: 
- answer: 

### N24: Is there a discount if I pay the whole year's tuition fee in advance?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

### N25: What is the punishment for plagiarism in a project report?

- expected `not_covered`, got `error` (LLMError: every model in the chain failed -> inclusionai/ling-3.0-flash-sante:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"50","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1788912000000"},"limit_source":"openrouter_free_tier_daily","remedy_hi | dots-studio/dots-3-note-preview:free: OpenRouter HTTP 429: {"error":{"message":"Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"5)
- retrieved: 
- answer: 

