"""InferCPI quickstart: standard library only."""
import json
import urllib.request

BASE = "https://infercpi.com/v1"
get = lambda path: json.load(urllib.request.urlopen(f"{BASE}/{path}"))

latest = get("latest.json")
L = latest["latest"]
print(latest["licence"])
print("What buyers pay:", L["weighted_index/paid_usd_1m"]["value"], "$/1M")
print("Same-model index (Sep 2023 = 100):", L["price_index/chained_price_idx"]["value"])
print("Cheapest model at ECI 145+:", L["price_index/cheapest_eci145_usd_1m"]["value"], "$/1M")

# full history of one series
pts = get("series/price_index/cheapest_eci145_usd_1m.json")["points"]
print(f"{len(pts)} weekly points, first {pts[0]}, last {pts[-1]}")

# every model priced this week, cheapest first
models = sorted(get("basket.json")["models"], key=lambda m: m["blended_usd_1m"])
for m in models[:5]:
    print(f'{m["key"]:40} {m["blended_usd_1m"]:8.3f} $/1M  ECI {m.get("eci")}')
