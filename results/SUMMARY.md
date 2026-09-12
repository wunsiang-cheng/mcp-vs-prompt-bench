# Results summary — deepseek-flash (V4.1 Flash), thinking off, temperature 0, N=5

580 runs total. Raw traces: `*.jsonl`; tables: `*.md`.

## Round 1 — 7-endpoint API, live spec + drift v1 (200 runs)

All five conditions 100%. Cost per run (mean input tokens): A prompt_doc 8.7K · B native 6.6K · C mcp 6.6K.
Drift v1 (renamed query params, silently ignored by the API) was recovered by every run:
the model noticed the filter had not been applied and filtered locally.

## Round 2 — 39-endpoint API (32 distractor routes), live spec + drift v2 (230 runs)

Live spec: still 100% everywhere. Distractors cost everyone ~2.4x input tokens; nobody picked a wrong endpoint.

Drift v2 = query renames + body fields renamed (`items→line_items`, `status→new_status`, 422 names the right field)
+ `/products` moved to `/catalog` (404, no hint). Only tasks that touch those routes run under it.

| task | C mcp (live) | A prompt_doc_stale2 | B native_stale2 |
|---|---|---|---|
| h1 create order | 5/5 · 4.0 calls · 17K tok | 5/5 · 10.8 calls · 76K tok | **3/5** · 14.2 calls · 73K tok |
| h2 create paid order | 5/5 · 4.8 calls · 20K tok | 5/5 · 10.4 calls · 66K tok | **1/5** · 9.6 calls · 32K tok |
| h3 mark pending paid | 5/5 · 5.0 calls · 17K tok | 5/5 · 8.0 calls · 32K tok | 5/5 · 9.2 calls · 28K tok |
| h4 cancel pending >300 | 5/5 · 6.0 calls · 15K tok | 5/5 · 14.0 calls · 76K tok | 5/5 · 14.0 calls · 67K tok |
| m1 shipped total of bob | 5/5 · 2.0 calls · 12K tok | 5/5 · 2.0 calls · 17K tok | 5/5 · 2.0 calls · 13K tok |

## Round 2b — 7-endpoint API + drift v2 (100 runs, attribution)

A 25/25. B 24/25 (one h2 miss). With only 7 tools the model keeps exploring and eventually scrapes SKUs out of
`list_orders`; with 39 tools it gives up sooner. B's failures are drift x surface area, not drift alone.

## Round 2c — thinking mode, h1+h2 only, 39-endpoint API (50 runs)

Same subset with `thinking: enabled` (DeepSeek default, high effort).

| condition | thinking | h1+h2 ok | calls | input tok | reasoning tok | seconds |
|---|---|---|---|---|---|---|
| C mcp | off / on | 10/10 · 10/10 | 4.4 · 4.1 | 18.6K · 17.3K | 0 · 39 | 5.7 · 5.3 |
| A prompt_doc | off / on | 10/10 · 10/10 | 4.5 · 4.3 | 24.6K · 23.7K | 0 · 87 | 5.0 · 5.0 |
| B native | off / on | 10/10 · 10/10 | 4.1 · 4.0 | 17.2K · 16.9K | 0 · 40 | 4.4 · 4.0 |
| A prompt_doc_stale2 | off / on | 10/10 · 10/10 | 10.6 · 10.3 | 71K · 70K | 0 · 671 | 10.7 · 11.6 |
| B native_stale2 | off / on | **4/10 · 10/10** | 11.9 · 8.8 | 53K · 62K | 0 · 783 | 11.1 · 11.6 |

Reasoning rescues B: instead of retrying `list_products` and guessing SKUs, it goes to `list_orders`, scrapes real SKUs,
reads the 422 to rename `line_items`→`items`, and finishes in ~9 calls. Live-spec runs barely reason at all (39–87 tokens):
when the schema is right there is nothing to think about.

## What the numbers say

1. MCP does not make the model better at using an API. Same success, same call count, same tokens as hand-written
   function schemas (B ≈ C to within 1% on tokens), in both API sizes.
2. Docs-in-prompt (A) is the most expensive way to be right: +33% input tokens (small API), +27% (big API),
   and 4–5x tokens / 2x wall-clock when the doc is stale and the model has to improvise.
3. A stale schema hurts differently depending on how the API is wired:
   - generic HTTP tool (A): the model can improvise paths and fields, and did, every time — at 4–5x cost.
   - baked-in function schemas (B): the model has no lever; on a moved path it fails 60% (big API) or burns
     10+ calls (small API).
   - MCP (C): the schema is served by the API owner, so there is nothing to go stale. 4–6 calls, unchanged.
4. A silently-ignored parameter (drift v1) is harmless to a model that reads its results. A moved path is not.
5. A stronger model (thinking on) closes B's success gap — but not the cost gap: stale B still spends 3.7x the
   input tokens and 2x the calls of live C. Reasoning buys back correctness by paying for it on every run;
   a live schema removes the problem instead.

## Caveats

Mock API, one model family, N=5, temperature 0 (runs are near-deterministic — most reps are identical).
MCP latency (+1.3s/run) is this harness spawning a stdio subprocess per run, not the protocol.
Distractor endpoints are plausible but never needed; a harder benchmark would make them tempting.
