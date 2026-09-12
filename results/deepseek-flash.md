## Success rate · tool calls/run · bad calls/run  (n=200 runs, model=deepseek-flash, thinking=False)

| condition | easy | medium | hard | all |
|---|---|---|---|---|
| prompt_doc | 100% · 1.3 calls · 0.0 bad | 100% · 2.5 calls · 0.0 bad | 100% · 4.2 calls · 0.0 bad | 100% · 2.9 calls · 0.0 bad |
| native | 100% · 1.3 calls · 0.0 bad | 100% · 2.5 calls · 0.0 bad | 100% · 4.0 calls · 0.0 bad | 100% · 2.8 calls · 0.0 bad |
| mcp | 100% · 1.3 calls · 0.0 bad | 100% · 2.5 calls · 0.0 bad | 100% · 4.2 calls · 0.2 bad | 100% · 2.9 calls · 0.1 bad |
| prompt_doc_stale | — | 100% · 2.0 calls · 0.0 bad | 100% · 5.0 calls · 0.0 bad | 100% · 3.5 calls · 0.0 bad |
| native_stale | — | 100% · 2.0 calls · 0.0 bad | 100% · 5.0 calls · 0.0 bad | 100% · 3.5 calls · 0.0 bad |

## Tokens & latency per run (mean, all tasks)

| condition | prompt tok | cache hit % | completion tok | reasoning tok | turns | seconds |
|---|---|---|---|---|---|---|
| prompt_doc | 8717 | 89% | 274 | 0 | 3.2 | 3.3 |
| native | 6556 | 84% | 194 | 0 | 3.2 | 3.0 |
| mcp | 6640 | 84% | 201 | 0 | 3.2 | 4.5 |
| prompt_doc_stale | 8329 | 82% | 378 | 0 | 3.5 | 3.8 |
| native_stale | 6092 | 81% | 260 | 0 | 3.5 | 3.4 |

## Per task success (n/N)

| task | prompt_doc | native | mcp | prompt_doc_stale | native_stale |
|---|---|---|---|---|---|
| e1 | 5/5 | 5/5 | 5/5 | — | — |
| e2 | 5/5 | 5/5 | 5/5 | — | — |
| e3 | 5/5 | 5/5 | 5/5 | — | — |
| m1 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| m2 | 5/5 | 5/5 | 5/5 | — | — |
| m3 | 5/5 | 5/5 | 5/5 | — | — |
| m4 | 5/5 | 5/5 | 5/5 | — | — |
| h1 | 5/5 | 5/5 | 5/5 | — | — |
| h2 | 5/5 | 5/5 | 5/5 | — | — |
| h3 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| h4 | 5/5 | 5/5 | 5/5 | — | — |
| h5 | 5/5 | 5/5 | 5/5 | — | — |
