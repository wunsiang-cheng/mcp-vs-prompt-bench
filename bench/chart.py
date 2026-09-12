"""Figure for the post: what a stale schema costs each wiring (h1+h2, 39-endpoint API, thinking off).
uv run python -m bench.chart  ->  results/stale-schema.png"""
import json
from statistics import mean
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = [json.loads(l) for l in open("results/deepseek-flash-big.jsonl", encoding="utf-8") if '"task": "h' in l]
rows = [r for r in rows if r["task"] in ("h1", "h2")]
COND = [("prompt_doc_stale2", "A\ndocs in prompt\n+ generic HTTP", "#2a78d6"),
        ("native_stale2", "B\nhand-written\ntool schemas", "#eb6834"),
        ("mcp", "C\nMCP\n(live schema)", "#1baf7a")]
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
stat = {c: [r for r in rows if r["condition"] == c] for c, _, _ in COND}
panels = [("Task success", lambda rs: mean(r["success"] for r in rs) * 100, "{:.0f}%", 125),
          ("Tool calls per run", lambda rs: mean(len(r["tool_calls"]) for r in rs), "{:.1f}", None),
          ("Input tokens per run", lambda rs: mean(r["usage"]["prompt"] for r in rs) / 1000, "{:.0f}K", None)]

plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 12})
fig, axes = plt.subplots(1, 3, figsize=(12.8, 6.4), facecolor=SURF)
fig.subplots_adjust(left=0.05, right=0.98, top=0.76, bottom=0.26, wspace=0.25)
for ax, (title, f, fmt, ymax) in zip(axes, panels):
    ax.set_facecolor(SURF)
    vals = [f(stat[c]) for c, _, _ in COND]
    bars = ax.bar(range(3), vals, width=0.58, color=[c for _, _, c in COND], edgecolor=SURF, linewidth=2)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", color=INK, fontsize=15, fontweight="bold")
    ax.set_title(title, loc="left", color=INK, fontsize=14, fontweight="bold", pad=14)
    ax.set_xticks(range(3), [l for _, l, _ in COND], color=MUTED, fontsize=10.5, linespacing=1.4)
    ax.set_ylim(0, ymax or max(vals) * 1.22)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="x", length=0)

fig.text(0.05, 0.93, "What a stale API schema costs an agent", color=INK, fontsize=20, fontweight="bold")
fig.text(0.05, 0.875, "DeepSeek V4.1 Flash · 39-endpoint mock API · two create-order tasks · 5 runs each · A/B use a spec with one moved path "
         "and two renamed fields; C discovers the live one", color=MUTED, fontsize=11)
fig.text(0.05, 0.045, "A never failed but improvised its way through (~11 calls, ~4x tokens). B had no lever to pull: the path is baked into the tool. "
         "C had nothing to recover from.\nWith the schema in sync, all three scored 100% at ~4 calls — MCP buys schema ownership, not model intelligence.",
         color=MUTED, fontsize=10.5, linespacing=1.5)
fig.savefig("results/stale-schema.png", dpi=150, facecolor=SURF)
print("wrote results/stale-schema.png")
