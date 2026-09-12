# mcp-vs-prompt-bench

Does MCP change how well an AI agent uses an API? One mock API, one agent loop, three ways to wire them,
580 runs on DeepSeek V4.1 Flash. Findings in [`results/SUMMARY.md`](results/SUMMARY.md).

**Short version:** with a correct schema all three wirings score 100% at the same cost. MCP does not make
the model better at the API — it guarantees the schema the model sees is the schema the server runs.
When the schema is one quarter stale, hand-written tool schemas fail 60% of create-order tasks;
docs-in-prompt survives by improvising at 4x the tokens; MCP is unaffected by construction.

## The three conditions

| Condition | What the model sees | How it calls the API |
|---|---|---|
| **A. prompt_doc** | `docs/api.md` in the system prompt | one generic `http_request` tool |
| **B. native** | OpenAI-style `tools[]` | function calling, direct HTTP |
| **C. mcp** | `tools/list` from `mcp_server` over stdio | `tools/call` |

All three descriptions are generated from the same OpenAPI spec (`mock_api/app.py`), so nobody gets a
hand-polished version. The agent loop (`agent/loop.py`) is identical; only the tool source differs.

## Layout

```
mock_api/      FastAPI mock "OrderHub" API: 7 core endpoints, deliberate traps, /reset + /state for the bench
  extras.py    32 distractor endpoints, enabled with ORDERHUB_BIG=1
  tools.py     OpenAPI -> tool defs (B, C) and -> docs/api.md (A); stale_spec() for the drift conditions
mcp_server/    stdio MCP server, tools generated from the same spec
agent/loop.py  the agent loop + three backends
tasks/         12 tasks with deterministic checkers (answer substring or mock-server state)
bench/         run.py (matrix runner -> jsonl), report.py (jsonl -> markdown), chart.py (figure)
results/       raw traces (*.jsonl), tables (*.md), SUMMARY.md
docs/api.md    generated; do not edit by hand
```

## Run

```
uv sync
echo DEEPSEEK_API_KEY=sk-... > .env
uv run uvicorn mock_api.app:app --port 8000   # mock API (terminal 1)
uv run python smoke_test.py                   # checks traps + MCP round-trip
uv run python -m bench.run --n 5              # 12 tasks x conditions x 5 reps -> results/deepseek-flash.jsonl
uv run python -m bench.report results/deepseek-flash.jsonl
uv run python -m mock_api.tools               # regenerate docs/api.md after editing app.py
```

Round 2 — 39-endpoint API (32 distractor routes) and harsher drift. Set `ORDERHUB_BIG=1` on **both** the
uvicorn process and the bench process:

```
ORDERHUB_BIG=1 uv run uvicorn mock_api.app:app --port 8000
ORDERHUB_BIG=1 uv run python -m bench.run --n 5 --stale stale2 --out results/deepseek-flash-big.jsonl
ORDERHUB_BIG=1 uv run python -m bench.run --n 5 --stale stale2 --thinking --tasks h1,h2 --out results/deepseek-flash-big-think.jsonl
```

`bench.run` is resumable: re-running with the same `--out` skips (task, condition, rep) triples already recorded.

## Mock API traps (deliberate)

- `X-API-Key` required (injected by the tool executor in all conditions)
- `GET /products`: first call after `/reset` returns 429 + `Retry-After`
- `GET /orders`: cursor pagination, 20/page — 34 shipped orders span 2 pages
- `POST /orders`: 422 on unknown SKU or `qty < 1`; prices come from the catalog
- `PATCH /orders/{id}`: 409 on shipped/cancelled orders
- `POST /reset`, `GET /state`: hidden from schema, used by the bench runner / checkers

## Drift conditions (`*_stale`, `*_stale2`)

A and B get a spec "documented last quarter"; C discovers the live one.

- `stale`: query params `email→customer_email`, `status→state`. The API ignores unknown params → superset results.
- `stale2`: + body fields `items→line_items`, `status→new_status` (422 names the right field), and `/products` moved to `/catalog` (404, no hint).

Only tasks marked `drift: true` run under these. Round-1 results used `stale`; round 2 uses `stale2`.

## Caveats

Mock API, one model family, N=5 at temperature 0 (many reps are identical — treat numbers as directional).
MCP's extra ~1.3 s/run is this harness spawning a stdio subprocess per run, not the protocol.
