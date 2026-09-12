"""Run the matrix: conditions x tasks x N, one line of JSON per run.

uv run python -m bench.run --n 5 --model deepseek-flash [--thinking] [--tasks e1,m2] [--conditions native,mcp]
Needs the mock API on :8000 and DEEPSEEK_API_KEY in .env.
"""
import argparse, asyncio, json, pathlib, re, time
import httpx, yaml
from agent.loop import run
from mock_api.tools import BASE_URL

ROOT = pathlib.Path(__file__).parents[1]
for line in (ROOT / ".env").read_text().splitlines():  # ponytail: 3-line .env loader, no python-dotenv
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        import os; os.environ.setdefault(k.strip(), v.strip())

TASKS = yaml.safe_load((ROOT / "tasks/tasks.yaml").read_text(encoding="utf-8"))
SEED_MAX_ID = 1075


def check(task, rec) -> bool:
    if rec["error"] or rec["final"] is None:
        return False
    c = task["check"]
    if "answer" in c:
        return c["answer"].lower() in re.sub(r"[,\s]", "", rec["final"].lower()).replace(" ", "")
    orders = httpx.get(BASE_URL + "/state").json()["orders"]
    return bool(eval(c["state"], {}, {"orders": orders, "new": [o for o in orders if o["id"] > SEED_MAX_ID]}))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--model", default="deepseek-flash")
    ap.add_argument("--thinking", action="store_true")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--conditions", default="prompt_doc,native,mcp")
    ap.add_argument("--stale", default="stale", help="drift suffix: stale (v1) or stale2 (v2)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    tasks = [t for t in TASKS if not a.tasks or t["id"] in a.tasks.split(",")]
    conds = a.conditions.split(",")
    out = pathlib.Path(a.out or ROOT / "results" / f"{a.model}{'-think' if a.thinking else ''}.jsonl")
    done = {(r["task"], r["condition"], r["rep"]) for r in map(json.loads, out.read_text().splitlines())} if out.exists() else set()
    with out.open("a", encoding="utf-8") as f:
        for task in tasks:
            for cond in conds + ([f"{c}_{a.stale}" for c in conds if c != "mcp"] if task.get("drift") else []):
                for rep in range(a.n):
                    if (task["id"], cond, rep) in done:
                        continue
                    httpx.post(BASE_URL + "/reset")
                    rec = await run(task["prompt"], cond, a.model, a.thinking)
                    rec.update(task=task["id"], tier=task["tier"], rep=rep, success=check(task, rec))
                    f.write(json.dumps(rec) + "\n"); f.flush()
                    print(f"{task['id']:3} {cond:17} #{rep} {'OK ' if rec['success'] else 'FAIL'} turns={rec['turns']:2} "
                          f"calls={len(rec['tool_calls']):2} tok={rec['usage']['prompt']}+{rec['usage']['completion']} "
                          f"{rec['elapsed']}s {rec['error'] or ''}", flush=True)

asyncio.run(main())
