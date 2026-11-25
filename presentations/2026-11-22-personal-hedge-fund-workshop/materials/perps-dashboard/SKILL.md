---
name: perps-dashboard
description: Build a read-only portfolio dashboard for onchain perps and MOEX via authorised API/MCP.
---

# Портфель: ончейн-перпы и Мосбиржа · Человек 2.0

The existing slug `perps-dashboard` and ZIP URL are kept for workshop compatibility. The result supports both markets, not just perpetuals.

## Result and boundaries
Create dashboard.html from the supplied standalone template.html. It contains both market views, account filters, separate native-currency totals, positions, PnL, margin, liquidation data where applicable and a linear price scenario. Open it, test it and return the local URL, not only a file path.
Never install globally, place orders/cancellations, sign transactions, modify leverage/permissions, expose ports or run schedules. Never put tokens, cookies, full account numbers or personal data in prompts, HTML, snapshots, logs or the public website. The browser imports a local JSON; it DOES NOT authenticate to a broker. Existing authorised API/MCP in Codex obtains the data locally.

## First run without credentials
1. Read this instruction and the included scripts before execution. Use combined-demo.json. It has a real archived Hyperliquid snapshot from 22 November 2026 and a CLEARLY LABELLED educational MOEX account (conditional prices/positions, not broker data).
2. Copy template.html to dashboard.html. Its data and calculation code are embedded, so it works standalone. Keep it byte-identical for the first run rather than redesigning it.
3. Serve on 127.0.0.1 on an available port if needed. No internet publication. Keep the controls and import/export functionality.
4. Select each market; check two positions per market and scenario math. Never present the example as a connected real account.

## Onchain API
Use build_snapshot.py --wallet <explicit public address> --dexes ,xyz --output portfolio-current.json. It calls the public Hyperliquid /info clearinghouseState read for core and xyz; it needs no private key or signature. Keep portfolio.json as the dated fixture. Fresh positions may differ from the fixture. Mark unsupported dex/account modes as incomplete, not empty/zero. Other onchain venues need their own verified read adapter; support for Hyperliquid does not prove coverage of every DEX.

## MOEX through existing API/MCP
The owner first selects one authorised brokerage account and balance group. Inspect that exact connection's schemas and read-tool permissions; a matching tool name or README does not prove read-only enforcement. Do not create new tunnels, forward credentials or guess endpoints. Use only admitted read methods. A token may have trading rights even if we use it only for reads.

For native Alfa PRO MCP, the current official schema is https://alfadt.servicecdn.ru/alfadt/ad5/Alfa-Investments-Pro-MCP.pdf :
- get_positions({accountId:<selected integer>}) and get_balances({accountId:<same integer>}); do NOT read all accounts with null by default.
- get_stocks / get_equity_participations / get_futures for metadata of the returned instrument IDs; get_futures_info for priceStep and priceStepCost when needed.
- server time from get_server_time. Decode result.structuredContent or JSON text in result.content; reject protocol/provider errors.
- Save the read result LOCALLY as {as_of, positions, balances, instruments, futures_info?}. `instruments` is the merged metadata array, `futures_info` maps instrument ID strings to the actual info responses. Do not include credentials, owner names or account names. Raw account IDs stay local and are stripped from the normalised output.
- Run `python portfolio_model.py alfa --input alfa-read.json --account-id <selected ID> --balance-group <chosen group> --output moex-current.json`.
- `currentBalance` already includes positions. `money` is a separate cash field: do not add it again to total equity. Do not blindly sum Unified, Papers and Futures balance groups. If ambiguous, ask which group to use.
- Quantity is SHARES or CONTRACTS, NOT LOTS. For RUB stocks/funds the multiplier is 1. Futures multiplier = actual priceStepCost/priceStep; missing metadata excludes that row with a visible coverage warning. A futures price is in points, not rubles by itself.
- Balances are RUB; use currencyId=0 instrument prices in this adapter. Non-RUB instruments, bonds (percent of par), options and other unsupported types are explicitly listed as excluded. Never silently apply stock maths to them. Broker profitLoss is preserved and labelled, not reinterpreted as total return.
- For another broker's API/MCP, map its actual documented fields to schema 2 and independently verify amounts/units. This Alfa mapping is not a universal broker connector.

No existing broker connection? Keep the labelled educational account or ask the owner to provide an authorised, anonymised read export. Do not claim a successful API/MCP read merely because the converter or example runs.

## Combine and import
`python portfolio_model.py combine --input portfolio-current.json moex-current.json --output portfolio-combined.json`
Import portfolio-combined.json in the dashboard's file control. Legacy Hyperliquid schema 1 remains supported. Never overwrite the fixture. Duplicate account aliases are rejected to avoid double-counting.

## Schema 2
{schema_version:2, accounts:[{id:<safe alias>, label, market:"onchain"|"moex", mode:"snapshot"|"sample", currency:"USD"|"RUB", as_of:<ISO with timezone>, equity:<number|null>, cash?, margin_used?, source, source_url?, coverage:{included,excluded:[]}, positions:[]}]}
Each position: id, symbol, venue, kind:"perp"|"stock"|"fund"|"future", signed_size (positive long, negative short), quantity_unit, currency (same as account), multiplier>0, entry_price, mark_price, unrealized_pnl, margin_used, liquidation_price, leverage. Unknown numeric fields are null. Stocks/funds use multiplier 1. Only perps may have per-position liquidation/leverage fields here; MOEX shows margin requirements at account level instead of inventing an individual liquidation price.

## Formulas and checks
The independent calculation source is portfolio_core.js, embedded in template.html. Do not alter one copy without the other.
- signed exposure = signed_size × mark_price × multiplier; gross = sum(abs(exposure)).
- PnL = provider unrealized_pnl when available, otherwise signed_size × (mark−entry) × multiplier if both prices known; unknown stays unknown.
- stress change = sum(exposure × shift_pct/100), PER CURRENCY. A negative price move benefits shorts. Zero shift yields 0.
- concentration is within the same currency's known notional, not equity. Missing prices produce an incomplete-coverage label.
- perp liquidation distance long=(mark−liq)/mark; short=(liq−mark)/mark. Negative values mean inconsistent input, not an absolute-value repair.
- NEVER add USD and RUB; no FX conversion is implied. Total equity is unavailable if any selected balance is unknown. Stress is not a liquidation simulation and ignores fees/funding/gaps.
- Excluding a row changes only the scenario, not the original data, account equity or real positions.

## Acceptance
Fixed Hyperliquid fixture: four long positions, gross 3 211 801.91772 USD. At −3%: −96 354.0575316 USD; without HYPE: −50 724.9575316 USD. These checks apply only to the old fixture, not refreshed data.
Educational MOEX: SBER 300 shares @300, LKOH 10 @7000, GAZP 200 @150; capital 1 000 000 RUB, gross 190 000 RUB, provider PnL 2 000 RUB, −3% scenario −5 700 RUB. These are synthetic exercise values, not an API response.
Test both filters, account selection, nulls, shorts, multiplier, invalid JSON rollback, HTML escaping, duplicate accounts and mobile horizontal-table containment. Return which APIs were really read, which inputs were educational, exact timestamps, missing coverage, and one executable refresh step. No live authenticated brokerage readiness is implied by passing fixture tests.
