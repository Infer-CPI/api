"""InferCPI MCP server: the AI inference price index for agents. Read-only tools over the public
v1 JSON API (https://infercpi.com/v1). One file, one dependency (`pip install mcp`); the same file
is published in the public repo github.com/richovercash/infercpi-api.

  python3 mcp_server.py          stdio (Claude Desktop / Claude Code / any MCP client)
  python3 mcp_server.py --http   streamable HTTP on :8765 (remote agents)
Works with the mcp package 1.x (FastMCP) and 2.x (MCPServer).

Reads ./out/v1 when present (the index's own build box), else INFERCPI_BASE (default https://infercpi.com).
Data: CC BY 4.0, cite 'InferCPI, infercpi.com' (every payload carries the licence line).
ponytail: no auth, no caching layer; a reverse proxy adds both when a paid tier exists."""

import json
import os
import pathlib
import re
import sys
import urllib.request

BASE = os.environ.get("INFERCPI_BASE", os.environ.get("TOKEN_INDEX_BASE", "https://infercpi.com")).rstrip("/")
LOCAL = pathlib.Path(__file__).parent / "out" / "v1"
_STOP = {"instruct", "chat", "turbo", "latest", "preview", "it", "hf", "fp8", "exp"}


def norm(name):
    """the index's model-name join key (same as collectors/prices.norm): 'anthropic/claude-opus-5.5-20260921',
    'claude-opus-5-5' and 'Claude Opus 5.5' all -> 'claudeopus55'."""
    t = name.split("/")[-1].split(":")[0].lower()
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[-_]?(20\d{6}|20\d\d-\d\d-\d\d)$", "", t)
    return "".join(x for x in re.split(r"[^a-z0-9]+", t) if x and x not in _STOP)
NAME = "infercpi"
INSTRUCTIONS = ("InferCPI: AI inference prices, cost per capability, open vs closed, hosts, self-hosting and cost per task, "
                "from open-licence sources. Call index_latest first; cite the licence line it returns.")
try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer(NAME, instructions=INSTRUCTIONS)
    serve_http = lambda: mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP(NAME, instructions=INSTRUCTIONS, host="0.0.0.0", port=8765)
    serve_http = lambda: mcp.run(transport="streamable-http")


def load(path):
    f = LOCAL / path
    if f.exists():
        return json.loads(f.read_text())
    with urllib.request.urlopen(f"{BASE}/v1/{path}", timeout=20) as r:
        return json.load(r)


@mcp.tool()
def index_latest() -> dict:
    """Latest value of every index series (list-price chained/composition/hedonic, usage-weighted paid
    price, Törnqvist, OpenRouter shares, TPI replica) with dates, the latest editorial note, and the
    licence/attribution line. Start here."""
    return load("latest.json")


@mcp.tool()
def index_series(signal: str, key: str, since: str = "") -> dict:
    """Full weekly history of one series as [[unix_ts, value], ...] plus its method string.
    signal: price_index | weighted_index | or_rankings | implied_margin | self_host | task_cost | hf_downloads |
    gpu_spot | gpu_neocloud | aws_gpu | speed | hyperscaler_capex | seller_revenue | cloud_revenue | token_price ...
    key: see index_catalogue.
    since: optional ISO date to cut the history."""
    d = load(f"series/{signal}/{key}.json")
    if since:
        import datetime as dt
        cut = dt.datetime.fromisoformat(since).timestamp()
        d["points"] = [p for p in d["points"] if p[0] >= cut]
    return d


@mcp.tool()
def index_catalogue() -> dict:
    """Every series the index publishes: signal/key, point count, first and last date, method string."""
    return load("index.json")


@mcp.tool()
def basket() -> dict:
    """Every model priced in this week's list-price index: provider, blended $/1M (0.75 in + 0.25 out),
    Epoch capability score where matched."""
    return load("basket.json")


@mcp.tool()
def events(since: str = "", kind: str = "") -> dict:
    """Priced events in first-party price lists, newest first: launch, price_cut, price_increase, removed,
    each with key, provider, old/new blended $/1M and pct. since: ISO date; kind: filter to one kind."""
    d = load("events.json")
    ev = d["events"]
    if since:
        ev = [e for e in ev if e["date"] >= since]
    if kind:
        ev = [e for e in ev if e["kind"] == kind]
    return {**d, "events": ev}


@mcp.tool()
def speed() -> dict:
    """Latest daily speed run, measured by the index: per model and route (openrouter default routing,
    openrouter_pinned to the first-party host, anthropic and openai direct), median time to first token (ms),
    visible output tokens per second, host that served it. Same prompt every day."""
    return load("speed.json")


@mcp.tool()
def model_price(name: str) -> dict:
    """Blended list $/1M for one model by any common name ('Claude Opus 5.5', 'anthropic/claude-opus-5.5',
    'gpt-5.5'); matches by the index's name normaliser and returns every basket entry that matches."""
    n = norm(name)
    hits = [m for m in load("basket.json")["models"] if norm(m["key"]) == n]
    return {"query": name, "normalised": n, "matches": hits}


def _latest_prefix(prefix):
    d = load("latest.json")
    return {"licence": d["licence"], "values": {k: v for k, v in d["latest"].items() if k.startswith(prefix)}}


@mcp.tool()
def open_vs_closed() -> dict:
    """Cheapest blended $/1M at each capability level (Epoch ECI 130/145/160) for closed models, open models at
    their lab's price and open models at the cheapest third-party host; the open discount; DeepSeek's floor lift
    (cheapest price without DeepSeek / cheapest overall, at lab and at host prices); and the host discount per
    open model (lab price / cheapest host)."""
    d = _latest_prefix("price_index/")
    keep = ("cheapest_", "open_discount", "open_host_discount", "deepseek_", "host_")
    return {**d, "values": {k: v for k, v in d["values"].items() if k.split("/", 1)[1].startswith(keep)}}


@mcp.tool()
def self_hosting() -> dict:
    """What it costs per 1M tokens to leave the APIs: desk boxes (Mac Studio lease, RTX 5090 bought) at full and
    25% duty, H100 rented by source (Vast, AWS, RunPod, CoreWeave, Lambda, Nebius) and owned, against the API
    price of the same open model and of the cheapest closed model at equal capability; break-even volume and how
    far hardware cost must fall. Plus posted GPU-hour prices and Hugging Face download counts."""
    out = _latest_prefix("self_host/")
    for p in ("gpu_neocloud/", "gpu_spot/", "aws_gpu/", "hf_downloads/"):
        out["values"].update(_latest_prefix(p)["values"])
    return out


@mcp.tool()
def cost_per_task() -> dict:
    """Monthly measurement: dollars and tokens per completed task for the most-used models (fixed 8-task suite via
    OpenRouter at default settings, charged cost), reasoning share of output tokens, accuracy, and medians."""
    return _latest_prefix("task_cost/")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        lat = index_latest(); assert "price_index/chained_price_idx" in lat["latest"]
        s = index_series("price_index", "chained_price_idx", since="2026-01-01"); assert s["points"] and s["method"]
        mp = model_price("Claude Opus 5.5"); assert mp["matches"], mp
        ev = events(since="2026-10-01", kind="launch"); assert ev["events"], ev
        oc = open_vs_closed(); assert any("open_host_discount" in k for k in oc["values"]), oc
        sh = self_hosting(); assert any("mac_usd_1m_full" in k for k in sh["values"]), sh
        tc = cost_per_task(); assert any("median_usd_per_task" in k for k in tc["values"]), tc
        print("ok", lat["latest"]["price_index/chained_price_idx"], len(s["points"]), mp["matches"][0], len(oc["values"]), len(sh["values"]), len(tc["values"]))
    elif "--http" in sys.argv:
        serve_http()
    else:
        mcp.run()
