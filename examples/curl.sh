#!/bin/sh
# InferCPI with curl and jq
B=https://infercpi.com/v1
curl -s $B/latest.json | jq '.latest["weighted_index/paid_usd_1m"]'             # what buyers pay
curl -s $B/index.json | jq -r '.series[].series' | head -20                      # what series exist
curl -s $B/series/price_index/open_host_discount_eci145_x.json | jq '.points[-1]' # open hosts vs closed
curl -s $B/events.json | jq '.events[:5]'                                         # latest price events
