# CALCULATION_DESIGN — WLSP L1–L5 (Source-Query Design)

**Date:** 2026-06-22 · **Developer:** sarujanan · **Deliverable:** D01 (design only) · **Reviewer:** Bietrick (TL)
**Status:** DESIGN — read-only. No CREATE/INSERT/UPDATE/DELETE/ALTER/DROP · no new tables · no new views · no implementation.
**Basis:** validated source tables (`SOURCE_DATA_READINESS_MATRIX`), protocol formulas (`REQ-001`), OPTION B.

**Global scope filters (every analysis unless noted):** `source_name ILIKE '%amazon%'` · `market_place ILIKE '%UK%'` · `fba_sales = false` · account normalised from `ss_name` via ILIKE (`ledsone*`/`led_sone`/`electricalsone` → LEDSone UK; `dcvoltage*` → DCVoltage UK).
**Shared data-quality rule:** `ppc_performance` is 24M rows — **always window-scope + `record_type='ad'`** (unscoped scans time out). Shipping is **per-order**, revenue is **per-line** — shipping must be **de-duplicated per `order_id`** before any ASIN ratio (else double-count on multi-line orders); follow the allocation used by `development.vw_fbm_uk_order_profitability` (`postage × line_revenue / order_revenue`).

---

## L1 — Zero-Conversion PPC (7 days)

1. **Source tables:** `public.ppc_performance` (single). Optional: `public.order_transaction` (PH fallback only).
2. **Source columns:** `date, record_type, ref_id (ASIN), sku, ss_name, user_name, spend, orders (=conversions), clicks, impressions, marketplace`.
3. **Formula (per ASIN):** `total_spend = SUM(spend)` · `total_conv = SUM(orders)` · `CTR = SUM(clicks)/NULLIF(SUM(impressions),0)` · `CVR = 0`. **Flag:** `total_spend > 3 AND total_conv = 0`.
4. **Filters:** `(ss_name ILIKE '%UK%' OR marketplace ILIKE '%UK%')` · `record_type='ad'` · `date >= CURRENT_DATE - INTERVAL '7 days'`.
5. **Date window:** last 7 days.
6. **Join logic:** none (single table). Optional `LEFT JOIN` SKU→PH map: `(SELECT sku, MAX(user_name) ph FROM order_transaction WHERE UK AND user_name<>'' GROUP BY sku)` on `ppc.sku`.
7. **Grouping level:** `ref_id (ASIN), sku, ss_name, user_name`.
8. **Output columns:** ASIN, account tag, SKU, spend, clicks, impressions, conversions(0), CTR, CVR, PH, `action='PAUSE PPC'`, deadline (Wed EOD).
9. **PH assignment method:** `ppc_performance.user_name` → fallback SKU→PH from `order_transaction` → else `'UNATTRIBUTED'`.
10. **Data-quality risks:** `user_name` **40.5% null** (HIGH — run/report at ASIN level, bucket UNATTRIBUTED); `sku` 37.1% blank (label only; ASIN 0% missing); must window-scope for performance.

---

## L2 — Shipping > 25% of Revenue (7 days)

1. **Source tables:** `public.order_transaction` + `public.order_shipping_billing_detail`.
2. **Source columns:** OT — `order_id, asin, sku, item_price, quantity, user_name, ss_name, order_status, order_date`; OSBD — `order_id, carrier_charge, carrier_charge_currency, shipping_template_price`.
3. **Formula (per ASIN):** `revenue = SUM(item_price*quantity)` · `shipping = SUM(order-deduped carrier_charge)` (+ `shipping_template_price` if present) · `shipping_pct = 100*shipping/NULLIF(revenue,0)`. **Flag:** `shipping_pct > 25`.
4. **Filters:** global scope + `order_status='Completed'` · `order_date >= CURRENT_DATE - 7` · `carrier_charge_currency='GBP'`.
5. **Date window:** last 7 days.
6. **Join logic:** `order_transaction ot JOIN order_shipping_billing_detail osbd ON ot.order_id = osbd.order_id`. **Critical:** resolve shipping **once per `order_id`** (carrier_charge is order-level) before grouping to ASIN — or allocate `carrier_charge × line_revenue/order_revenue` (mirror `vw_fbm_uk_order_profitability`).
7. **Grouping level:** `asin, sku, user_name, ss_name`.
8. **Output columns:** ASIN, account, SKU, revenue, shipping, shipping_pct, order_count, order_id(s), PH, `action ∈ {INCREASE PRICE, SWITCH CARRIER, DISCONTINUE}`, deadline.
9. **PH assignment method:** `order_transaction.user_name` (MAX per group); ~20% unattributed (30d).
10. **Data-quality risks:** **shipping double-count** on multi-line orders if not order-deduped (HIGH if mishandled); `carrier_charge` 99.6% present on this join (good); `shipping_template_price` 88.4% null (low impact); PH ~20% null.

---

## L3 — Net-Negative + PPC > £5 (7 days)

1. **Source tables:** `order_transaction` + `order_shipping_billing_detail` + `ppc_performance`.
2. **Source columns:** L2 set + `ppc_performance.spend, sku, ref_id, date, record_type`.
3. **Formula (per ASIN/SKU):** `revenue = SUM(item_price*quantity)` · `shipping = SUM(order-deduped carrier_charge)` · `ppc = SUM(ppc.spend 7d for sku)` · `net = (revenue*0.45) − shipping − ppc`. **Flag:** `net < 0 AND ppc > 5`.
4. **Filters:** global scope + `order_status='Completed'` + 7d (orders) + UK 7d `record_type='ad'` (ppc).
5. **Date window:** last 7 days (both legs).
6. **Join logic:** revenue/shipping CTE from `ot ⋈ osbd` (order-deduped shipping) `LEFT JOIN` `(SELECT sku, SUM(spend) ppc FROM ppc_performance WHERE UK 7d GROUP BY sku)` on `sku`. ASIN from `ot.asin` (= `ppc.ref_id`). Note SKU↔PPC is many-to-many over the window.
7. **Grouping level:** `sku, asin, user_name, ss_name`.
8. **Output columns:** ASIN, SKU, account, revenue, shipping, ppc, net, PH, `action='PAUSE PPC'`, deadline.
9. **PH assignment method:** prefer `order_transaction.user_name` (PPC PH is 40.5% null — do not rely on ppc side).
10. **Data-quality risks:** `0.45` flat factor is a protocol **assumption** (vs itemized actuals); PPC↔order SKU join cardinality; shipping dedupe; PH attribution.

---

## L4 — Refund Rate > 10% (30 days)

1. **Source tables:** `public.order_transaction` (spine). Optional enrichment: `public.amazon_returns`.
2. **Source columns:** OT — `asin, sku, user_name, ss_name, order_id, order_status, item_price, quantity, order_date`; AR (optional) — `order_id, sku, reason, refunded_amount`.
3. **Formula (per ASIN):** `total_orders = COUNT(DISTINCT order_id)` · `refunded = COUNT(DISTINCT order_id) FILTER (order_status='Refunded')` · `refund_rate = 100*refunded/total_orders` · `revenue_at_risk = SUM(item_price*quantity) FILTER (Refunded)`. **Flag:** `refund_rate > 10 AND total_orders >= 2`.
4. **Filters:** global scope + `order_date >= CURRENT_DATE - 30` (all statuses for denominator) + `HAVING total_orders >= 2`.
5. **Date window:** last 30 days.
6. **Join logic:** none required (single-table, self-consistent rate). Optional `LEFT JOIN amazon_returns ON order_id (+sku)` for reason/£ enrichment only.
7. **Grouping level:** `asin, sku, user_name, ss_name`.
8. **Output columns:** SKU, ASIN, account, total_orders, refunded_orders, refund_rate, revenue_at_risk, PH, return_reason (optional), `action='INVESTIGATE'`, deadline.
9. **PH assignment method:** `order_transaction.user_name`.
10. **Data-quality risks:** **DQ-2** — refund truth: use `order_transaction.order_status='Refunded'` as the **single rate source** (self-consistent); `amazon_returns.refunded_amount` **40.9% null** so use `item_price` proxy for revenue-at-risk; small denominators (min 2) are statistically volatile.

---

## L5 — PH Monthly Margin Trend (3 full months)

1. **Source tables:** `order_transaction` + `order_shipping_billing_detail` + `ppc_performance`.
2. **Source columns:** `item_price, quantity, order_date, user_name` (OT); `carrier_charge` (OSBD); `spend, date` (PPC).
3. **Formula (per PH per month):** `revenue = SUM(item_price*quantity)` · `shipping = SUM(order-deduped carrier_charge)` · `ppc = SUM(ppc.spend that month for PH)` · `net = revenue − (revenue*0.55) − shipping − ppc` · `net_margin_pct = 100*net/NULLIF(revenue,0)`. **Flag:** margin declines for **≥2 consecutive months** (via `LAG()` over month per PH).
4. **Filters:** global scope + `order_status IN ('Completed','Refunded')` + **last 3 FULL calendar months** (exclude the partial current month).
5. **Date window:** 3 full months (e.g. Mar/Apr/May when run in June).
6. **Join logic:** monthly per-PH CTEs: revenue/shipping from `ot ⋈ osbd` (order-deduped shipping) grouped by `DATE_TRUNC('month',order_date), user_name`; PPC grouped by month + PH (via `ppc.user_name`, or SKU→PH). Then `LAG()` window for decline detection.
7. **Grouping level:** `user_name, DATE_TRUNC('month', order_date)`.
8. **Output columns:** PH, month, revenue, shipping, ppc, net, net_margin_pct, decline_flag, months_declining.
9. **PH assignment method:** `order_transaction.user_name` is the grouping key; **PPC→PH allocation is the weak link** (ppc `user_name` 40.5% null → PPC per PH is understated).
10. **Data-quality risks:** PPC-per-PH incompleteness (HIGH); ~20% revenue unattributed; `0.55` cost factor assumed (net directional); **must exclude the partial current month** or the latest "decline" is an artifact.

---

## Can the weekly HTML report be generated directly from source queries, without storing results?

**Advantages**
- **Always fresh** — reflects live data at run time; no ETL lag.
- **Zero stored duplication** — nothing persisted, so no second source of truth competing with `development.leakage_*` or `ph_action_board`.
- **No schema/storage cost** — pure SELECT; no new objects (matches the read-only mandate).
- **Single source of figures** — the source tables, consistent with the C-6 "source of figures" principle.

**Risks**
- **No closure/verification history** — the protocol's "**following-Monday verification**" (REQ-001 §6) needs last week's flagged set to compare against; pure on-demand keeps **no prior-week record** → week-over-week verification is impossible without persistence.
- **Non-reproducible** — re-running later yields different numbers as data mutates (no point-in-time snapshot / audit trail).
- **Tick/closure state** — the HTML's tick system persists only in browser `localStorage`, not in the DB → no team-wide, durable action status.
- **Heavy queries** — `ppc_performance` (24M rows) and the L3/L5 3-way joins are expensive; an unscoped run **timed out** this session.

**Duplicate-truth impact**
- **On-demand (no storage): NIL duplicate truth** — nothing is written.
- **Storing results: only safe via OPTION B** — persist the *flagged set* into the existing `leakage_detection` lifecycle (with an `analysis_type` discriminator) + surface through `ph_action_board`, giving **one** status of record. Storing into a *new parallel table* would re-create the L2/L3 duplicate-truth hazard already documented.

**Performance impact**
- L1 (single table, 7d, `record_type='ad'`, ~96k rows) — light, uses `idx_ppc_perf_source_date`.
- L2 (2-table, 7d completed) — light–moderate.
- L3 / L5 (3-table joins; L5 over 3 months) — **moderate–heavy**; must window-scope PPC and pre-aggregate per `order_id`/month. Full-table PPC scans must be avoided (evidence: timeout).

**Recommendation**
> **HYBRID (render-from-source + persist-the-flagged-set).** Generate the weekly HTML report **directly from source queries** at run time (fresh, zero duplication, no schema change), **but persist the resulting flagged ASIN/SKU set into the existing leakage lifecycle** (OPTION B: `leakage_detection` + `ph_action_board`, `analysis_type` discriminator) **so the following-Monday verification and closure loop have a prior-week record.** Pure on-demand cannot satisfy the protocol's verification requirement; pure storage risks duplicate truth. The hybrid keeps one status of record and one source of figures. *(This is design only — no objects created; persistence is gated on OPTION B sign-off.)*

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Define the exact source-query design for L1–L5 + the render-vs-store decision |
| Business Question Supported | "How will each analysis be calculated from source, and should results be stored?" |
| Evidence Used | `SOURCE_DATA_READINESS_MATRIX`, `REQ-001`, `vw_fbm_uk_order_profitability` allocation pattern, this session's source profiles |
| Reviewer | Bietrick (TL) |
| Status | DESIGN COMPLETE — read-only; no implementation |
| Pass/Fail Rule | PASS if every analysis has tables/columns/formula/filters/window/join/grain/output/PH/DQ defined and the store decision is justified |
| Next Step | On OPTION B sign-off: implement L1 first (ASIN-level), render report, persist flagged set for closure |
| Known Limitations | Formulas use protocol assumptions (0.45/0.55 factors, COGS/fee/VAT); PPC→PH attribution weak (DQ-1); refund source per DQ-2 |
