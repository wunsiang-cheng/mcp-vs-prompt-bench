"""results/*.jsonl -> markdown tables on stdout.  uv run python -m bench.report results/deepseek-flash.jsonl"""
import json, sys
from collections import defaultdict
from statistics import mean

rows = [json.loads(l) for f in sys.argv[1:] for l in open(f, encoding="utf-8")]
TIERS = ["easy", "medium", "hard"]
CONDS = ["prompt_doc", "native", "mcp", "prompt_doc_stale", "native_stale", "prompt_doc_stale2", "native_stale2"]


def agg(rs):
    if not rs:
        return "—"
    ok = mean(r["success"] for r in rs) * 100
    bad = mean(sum(1 for c in r["tool_calls"] if c["status"] in (0, 400, 404, 409, 422)) for r in rs)
    return f"{ok:.0f}% · {mean(len(r['tool_calls']) for r in rs):.1f} calls · {bad:.1f} bad"


by = defaultdict(list)
for r in rows:
    by[(r["condition"], r["tier"])].append(r)
    by[(r["condition"], "all")].append(r)
    by[(r["condition"], r["task"])].append(r)

conds = [c for c in CONDS if any(k[0] == c for k in by)]
print(f"## Success rate · tool calls/run · bad calls/run  (n={len(rows)} runs, model={rows[0]['model']}, thinking={rows[0]['thinking']})\n")
print("| condition | " + " | ".join(TIERS + ["all"]) + " |")
print("|---|" + "---|" * (len(TIERS) + 1))
for c in conds:
    print(f"| {c} | " + " | ".join(agg(by[(c, t)]) for t in TIERS + ["all"]) + " |")

print("\n## Tokens & latency per run (mean, all tasks)\n")
print("| condition | prompt tok | cache hit % | completion tok | reasoning tok | turns | seconds |")
print("|---|---|---|---|---|---|---|")
for c in conds:
    rs = by[(c, "all")]
    u = lambda k: mean(r["usage"][k] for r in rs)
    print(f"| {c} | {u('prompt'):.0f} | {u('cache_hit') / max(u('prompt'), 1) * 100:.0f}% | {u('completion'):.0f} | {u('reasoning'):.0f} | "
          f"{mean(r['turns'] for r in rs):.1f} | {mean(r['elapsed'] for r in rs):.1f} |")

print("\n## Per task success (n/N)\n")
tasks = sorted({r["task"] for r in rows}, key=lambda t: (TIERS.index(next(r["tier"] for r in rows if r["task"] == t)), t))
print("| task | " + " | ".join(conds) + " |")
print("|---|" + "---|" * len(conds))
for t in tasks:
    print(f"| {t} | " + " | ".join(f"{sum(r['success'] for r in by[(c, t)])}/{len(by[(c, t)])}" if by[(c, t)] else "—" for c in conds) + " |")

fails = [r for r in rows if not r["success"]]
if fails:
    print("\n## Failures\n")
    for r in fails:
        print(f"- {r['task']} {r['condition']} #{r['rep']}: err={r['error']} calls={[(c['name'], c['status']) for c in r['tool_calls']][:8]} final={str(r['final'])[:100]!r}")
