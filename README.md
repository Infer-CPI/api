# InferCPI API

**InferCPI** tracks what AI inference costs: list prices, what buyers actually pay, the cost of a fixed level of capability, open vs closed models, third-party hosts, self-hosting, and cost per completed task. Site: **https://infercpi.com**.

This repo holds the public API docs, examples and the MCP server. The data is free, needs no key, and is licensed **CC BY 4.0**: cite as *InferCPI, infercpi.com*.

## API

Static JSON at `https://infercpi.com/v1/`. Full reference: **https://infercpi.com/api.html**.

| File | What |
|---|---|
| `latest.json` | Last value of every series, plus the weekly editorial note |
| `index.json` | Catalogue of every series: point count, dates, method string, URL |
| `series/<signal>/<key>.json` | Full history: `points: [[unix_ts, value], ...]` and `method` |
| `basket.json` | Every model priced this week: input, output and blended $/1M, context, Epoch ECI, open or closed |
| `events.json` | Launches, price cuts, increases and removals since Sep 2023 |
| `speed.json` | Our daily speed run: time to first token, tokens per second |
| `token_mix.json` | Tokens routed through OpenRouter per week, by lab and region |
| `capex.json` | Hyperscaler capex, chip and cloud revenue by quarter (SEC filings) |

```bash
curl -s https://infercpi.com/v1/latest.json | jq '.latest["weighted_index/paid_usd_1m"]'
```

More in [`examples/`](examples).

## MCP server

`mcp_server.py` gives agents ten read-only tools over the API: `index_latest`, `index_series`, `index_catalogue`, `basket`, `model_price`, `events`, `speed`, `open_vs_closed`, `self_hosting`, `cost_per_task`.

```bash
pip install mcp
claude mcp add infercpi -- python mcp_server.py      # Claude Code
python mcp_server.py --http                          # streamable HTTP on :8765
```

Claude Desktop (`claude_desktop_config.json`):

```json
{ "mcpServers": { "infercpi": { "command": "python", "args": ["/path/to/mcp_server.py"] } } }
```

It reads `https://infercpi.com` by default; set `INFERCPI_BASE` to point elsewhere.

## Method and sources

How every series is built: **https://infercpi.com/methodology.html**. Inputs: LiteLLM and pydantic/genai-prices (MIT), Epoch AI Capabilities Index (CC BY 4.0), OpenRouter rankings (CC BY 4.0), SEC filings (public domain). Speed and cost per task are our own measurements.

## Licence

Code in this repo: MIT. Index data: CC BY 4.0. Questions, corrections or a series you need: open an issue.
