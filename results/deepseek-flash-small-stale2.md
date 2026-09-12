## Success rate · tool calls/run · bad calls/run  (n=100 runs, model=deepseek-flash, thinking=False)

| condition | easy | medium | hard | all |
|---|---|---|---|---|
| prompt_doc | — | 100% · 2.0 calls · 0.0 bad | 100% · 5.0 calls · 0.0 bad | 100% · 4.4 calls · 0.0 bad |
| native | — | 100% · 2.0 calls · 0.0 bad | 100% · 5.2 calls · 0.0 bad | 100% · 4.5 calls · 0.0 bad |
| prompt_doc_stale2 | — | 100% · 2.0 calls · 0.0 bad | 100% · 10.7 calls · 4.5 bad | 100% · 9.0 calls · 3.6 bad |
| native_stale2 | — | 100% · 2.0 calls · 0.0 bad | 95% · 11.3 calls · 5.2 bad | 96% · 9.5 calls · 4.1 bad |

## Tokens & latency per run (mean, all tasks)

| condition | prompt tok | cache hit % | completion tok | reasoning tok | turns | seconds |
|---|---|---|---|---|---|---|
| prompt_doc | 7962 | 88% | 400 | 0 | 3.8 | 3.8 |
| native | 5405 | 82% | 288 | 0 | 3.7 | 3.4 |
| prompt_doc_stale2 | 28451 | 86% | 841 | 0 | 6.6 | 7.2 |
| native_stale2 | 27253 | 84% | 674 | 0 | 6.8 | 7.1 |

## Per task success (n/N)

| task | prompt_doc | native | prompt_doc_stale2 | native_stale2 |
|---|---|---|---|---|
| m1 | 5/5 | 5/5 | 5/5 | 5/5 |
| h1 | 5/5 | 5/5 | 5/5 | 5/5 |
| h2 | 5/5 | 5/5 | 5/5 | 4/5 |
| h3 | 5/5 | 5/5 | 5/5 | 5/5 |
| h4 | 5/5 | 5/5 | 5/5 | 5/5 |

## Failures

- h2 native_stale2 #2: err=None calls=[('list_customers', 200), ('list_products', 404), ('list_products', 404), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422)] final="I'm unable to complete this task. Here's the situation:\n\n- **Customer found:** Henry Yang, ID 8 (hen"
