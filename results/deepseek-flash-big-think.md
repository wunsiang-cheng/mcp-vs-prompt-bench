## Success rate · tool calls/run · bad calls/run  (n=50 runs, model=deepseek-flash, thinking=True)

| condition | easy | medium | hard | all |
|---|---|---|---|---|
| prompt_doc | — | — | 100% · 4.3 calls · 0.0 bad | 100% · 4.3 calls · 0.0 bad |
| native | — | — | 100% · 4.0 calls · 0.0 bad | 100% · 4.0 calls · 0.0 bad |
| mcp | — | — | 100% · 4.1 calls · 0.0 bad | 100% · 4.1 calls · 0.0 bad |
| prompt_doc_stale2 | — | — | 100% · 10.3 calls · 5.1 bad | 100% · 10.3 calls · 5.1 bad |
| native_stale2 | — | — | 100% · 8.8 calls · 4.1 bad | 100% · 8.8 calls · 4.1 bad |

## Tokens & latency per run (mean, all tasks)

| condition | prompt tok | cache hit % | completion tok | reasoning tok | turns | seconds |
|---|---|---|---|---|---|---|
| prompt_doc | 23672 | 94% | 448 | 87 | 4.3 | 5.0 |
| native | 16869 | 93% | 258 | 40 | 4.0 | 4.0 |
| mcp | 17325 | 93% | 272 | 39 | 4.1 | 5.3 |
| prompt_doc_stale2 | 69565 | 90% | 1428 | 671 | 8.3 | 11.6 |
| native_stale2 | 62282 | 90% | 1341 | 783 | 8.6 | 11.6 |

## Per task success (n/N)

| task | prompt_doc | native | mcp | prompt_doc_stale2 | native_stale2 |
|---|---|---|---|---|---|
| h1 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| h2 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
