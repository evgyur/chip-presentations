---
name: perps-dashboard
description: Build a read-only perpetual-futures portfolio dashboard.
---

# Perps dashboard · Человек 2.0

## Result
Create dashboard.html in the owner's project using template.html and a normalized portfolio JSON. Open over a local HTTP server and verify it, not just file existence. Do not install anything globally. Default to portfolio.json for a first run: it contains the public Hyperliquid wallet 0xa00db4fbef1fe1dae76e3b975d0969663c11690c. Read hype-liquidation.json for its confirmed Friday HYPE liquidation. Show the wallet, capture timestamp and source links. build_snapshot.py refreshes the positions read-only.

## Inputs and adapters
- Centralized exchange: use existing authorized read-only API integration. Credentials stay in local secret configuration, never in HTML, JSON, prompts or logs. Do not enable orders or withdrawals.
- Hyperliquid: for a supplied public address, POST to https://api.hyperliquid.xyz/info with JSON {"type":"clearinghouseState","user":"<public address>"}. Map accountValue to equity and totalMarginUsed to margin_used from marginSummary; assetPositions[].position gives coin, szi, entryPx, liquidationPx and leverage.value. Fetch allMids for mark prices, and record UTC capture time. Report unsupported dex/account modes instead of reporting an empty account as zero.
- Other perps DEX: identify its official read API and actual address/account scheme first. Public address does not establish data coverage for every venue.
- No integration available: use the supplied public wallet snapshot; never fabricate a successful account connection.

## Schema v1
currency: USD (single valuation currency), mode: snapshot, as_of: ISO UTC date, source: description, equity: number or null, margin_used: number or null, positions: array of objects. Each position has symbol, venue, signed_size (long positive, short negative), entry_price, mark_price, liquidation_price (number or null), leverage (number or null). JSON number, not formatted strings. Never sum accounts in different currencies without an explicit FX rate, source and timestamp. Avoid double-counting equity and margin in aggregate totals.

## Formulas (linear contracts only)
- absolute notional = abs(signed_size * mark_price)
- unrealized PnL = signed_size * (mark_price - entry_price), before funding/fees
- margin utilization = margin_used / equity * 100 when known and equity > 0
- liquidation distance long = (mark_price - liquidation_price) / mark_price * 100
- liquidation distance short = (liquidation_price - mark_price) / mark_price * 100
- concentration = symbol absolute notional / total absolute notional, NOT percent of equity
- stress PnL = sum(signed_size * mark_price * shift_pct / 100)
Exclude inverse/quanto contracts until their own pricing/contract multiplier is implemented and tested. Never silently apply linear formulas to them. Stress is not an execution/liquidation simulation. Do not invent ROI without time-series equity and cash flows. Null stays unavailable, not zero. No invented risk score.

## Workflow
1. Read inputs and verify the public wallet and snapshot timestamp. Validate schema and source timestamps.
2. Normalize with a separate local script. Check two positions and account equity against the source.
3. Copy template.html into dashboard.html, replace the inline portfolio data with validated JSON or use its file-upload control. Preserve HTML escaping; do not inject data as untrusted HTML/script. For inline JSON escape < as \u003c to prevent a script-closing injection.
4. Serve on loopback using an available local HTTP server; do not expose to the internet. Open in browser, check desktop and mobile, import JSON, move stress slider and verify totals by code.
5. Return local URL, snapshot time, data file and refresh command. No background polling or scheduled tasks unless separately requested. A snapshot is not live monitoring.

## Acceptance
Wallet 0xa00db4fbef1fe1dae76e3b975d0969663c11690c: 6 positions, gross 1961.761806, net -1866.3675660000001, unrealized PnL 4.217506. Compare +3% with and without BTC using portfolio.json. HYPE liquidation: 2026-11-20 16:25:57 MSK, 31.65 HYPE at 62.231, closed PnL -112.45245. Match liquidatedUser to this wallet. Null fields render —. No credentials in output.
