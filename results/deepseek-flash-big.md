## Success rate · tool calls/run · bad calls/run  (n=230 runs, model=deepseek-flash, thinking=False)

| condition | easy | medium | hard | all |
|---|---|---|---|---|
| prompt_doc | 100% · 1.3 calls · 0.0 bad | 100% · 2.5 calls · 0.0 bad | 100% · 4.2 calls · 0.0 bad | 100% · 2.9 calls · 0.0 bad |
| native | 100% · 1.3 calls · 0.0 bad | 100% · 2.5 calls · 0.0 bad | 100% · 4.0 calls · 0.0 bad | 100% · 2.9 calls · 0.0 bad |
| mcp | 100% · 1.3 calls · 0.0 bad | 100% · 2.5 calls · 0.0 bad | 100% · 4.3 calls · 0.2 bad | 100% · 3.0 calls · 0.1 bad |
| prompt_doc_stale2 | — | 100% · 2.0 calls · 0.0 bad | 100% · 10.8 calls · 4.7 bad | 100% · 9.0 calls · 3.7 bad |
| native_stale2 | — | 100% · 2.0 calls · 0.0 bad | 70% · 11.8 calls · 6.6 bad | 76% · 9.8 calls · 5.3 bad |

## Tokens & latency per run (mean, all tasks)

| condition | prompt tok | cache hit % | completion tok | reasoning tok | turns | seconds |
|---|---|---|---|---|---|---|
| prompt_doc | 20179 | 95% | 279 | 0 | 3.3 | 3.5 |
| native | 15846 | 92% | 196 | 0 | 3.2 | 3.3 |
| mcp | 16353 | 91% | 204 | 0 | 3.3 | 4.5 |
| prompt_doc_stale2 | 53284 | 92% | 867 | 0 | 6.8 | 8.0 |
| native_stale2 | 42750 | 92% | 766 | 0 | 6.4 | 8.2 |

## Per task success (n/N)

| task | prompt_doc | native | mcp | prompt_doc_stale2 | native_stale2 |
|---|---|---|---|---|---|
| e1 | 5/5 | 5/5 | 5/5 | — | — |
| e2 | 5/5 | 5/5 | 5/5 | — | — |
| e3 | 5/5 | 5/5 | 5/5 | — | — |
| m1 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| m2 | 5/5 | 5/5 | 5/5 | — | — |
| m3 | 5/5 | 5/5 | 5/5 | — | — |
| m4 | 5/5 | 5/5 | 5/5 | — | — |
| h1 | 5/5 | 5/5 | 5/5 | 5/5 | 3/5 |
| h2 | 5/5 | 5/5 | 5/5 | 5/5 | 1/5 |
| h3 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| h4 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| h5 | 5/5 | 5/5 | 5/5 | — | — |

## Failures

- h1 native_stale2 #2: err=None calls=[('list_customers', 200), ('list_products', 404), ('list_products', 404), ('create_order', 422), ('create_order', 422), ('list_products', 404), ('list_orders', 200), ('list_orders', 200)] final="I was unable to complete this task. Here's what happened:\n\n- **Customer found:** carol@example.com →"
- h1 native_stale2 #3: err=None calls=[('list_customers', 200), ('list_products', 404), ('list_products', 404), ('create_order', 422), ('create_order', 422), ('list_orders', 200), ('list_orders', 200), ('list_orders', 200)] final="I've hit a blocker. Let me summarize the situation.\n\nI was unable to create the order as requested. "
- h2 native_stale2 #0: err=None calls=[('list_customers', 200), ('list_products', 404), ('list_products', 404), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422)] final="I've hit a blocker: the product catalog endpoint (`list_products`) returns 404, so I have no way to "
- h2 native_stale2 #1: err=None calls=[('list_customers', 200), ('list_products', 404), ('list_products', 404), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422)] final="I'm unable to complete this task. Here's the situation:\n\n- **Customer found:** Henry Yang, ID 8 (hen"
- h2 native_stale2 #3: err=None calls=[('list_customers', 200), ('list_products', 404), ('list_products', 404), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422)] final="I'm unable to complete this task. Here's why:\n\n- The customer was found: Henry Yang, ID 8.\n- However"
- h2 native_stale2 #4: err=None calls=[('list_customers', 200), ('list_products', 404), ('list_products', 404), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422), ('create_order', 422)] final="I'm unable to complete this task. Here's why:\n\n- The customer was found: Henry Yang, ID 8.\n- However"
