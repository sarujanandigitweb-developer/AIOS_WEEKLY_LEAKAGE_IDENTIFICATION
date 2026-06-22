# Phase 1 — Recorded Query Results

Captured 2026-06-22 from live Postgres. These are the verbatim outputs the discovery conclusions rely on.

---

## 01 — Leakage/report asset search

```
development.leakage_classification
development.leakage_detection
development.leakage_pattern_registry
staging_ai.google_cppc_leakage_execution_queue
staging_ai.google_cppc_leakage_opportunity_engine_v1
staging_ai.marketing_leakage_root_cause_register
```
`list_objects(public, view)` → `[]` (no views in public).

## 02 — Row counts (estimated) + sizes

| Table | Rows | Size |
|-------|------|------|
| ppc_performance | 24,565,917 | 8,288 MB |
| ppc_etl_performance_data | 24,510,852 | 5,709 MB |
| amz_fbm_performance_data | 2,063,468 | 1,132 MB |
| order_transaction | 1,218,870 | 643 MB |
| order_shipping_billing_detail | 1,088,958 | 411 MB |
| amz_order_expenses | 412,313 | 97 MB |
| amazon_returns | 3,772 | 3.7 MB |
| fbm_sku_daily_nnr_snapshot | 2,287 | 1.3 MB |

Order status (UK Amazon): Completed 376,582 · Cancelled 8,628 · Refunded 7,706 · Canceled 1,349 · others.

## 03 — amazon_returns

earliest 2026-01-01 · latest 2026-06-17 · rows 3,772 · distinct asins 2,179 · distinct skus 2,315 · UK rows 2,746.

## 04 — ref_id = ASIN + account/PH profile

`ref_id` values are ASINs (e.g. `B07QNR618G`, `B07CWDD16N`). `record_type='ad'` carries SKU+ASIN.
Account names in `ss_name`: `amazon Dcvoltage`, `amazon Ledsone`, `dcvoltage-2`, `electricalsone`, `led_sone`,
`ledsone`, `ledsonede`, `so_926407` → require ILIKE normalisation to LEDSone / DCVoltage.
PH mapping (UK FBM, 30d): 6,274 rows · 5,234 with PH · **83.4% mapped** · 24 distinct PHs.

## 05 — Shipping coverage + template price

Shipping: 5,446 Amazon orders · 4,001 with carrier_charge · **73.5% coverage** (last 30d).
Template price: 9,766 sample rows · only **358 populated (3.7%)** · avg carrier_charge £3.50 · avg template £0.27.

## 06 — NNR snapshot

latest = earliest = **2026-06-17** · snapshot_days = 1 · rows 2,287 · skus 1,832 · phs 24. (No trend history.)

## 07 — PPC UK range

earliest 2025-01-01 · latest 2026-06-22 · rows 17,243,468 · unique skus 50,953.
Last-7-day UK `record_type` grain: ad 95,992 rows / 7,865 skus; product 44,396; asset 1,631; campaign 1,309.

## Live feasibility probes (single-query confirmations)

- **L1** sample returned real flags, e.g. SKU `PLADBM+LSDO210BG3PK+ICST64E273PK` / ASIN B09YYSLDWP / Theepana —
  spend £17.84, 46 clicks, 2,980 impressions, **0 conversions**.
- **L4** sample returned real flags, e.g. ASIN B0DHGM5NP4 / `LSCY290WH2PK+RPR44WH2PK` / utharsika — 2 orders,
  1 refunded, **50% refund rate**.
- **L5** sample returned 3-month monthly revenue + shipping per PH (Abinayaa, Arudchelvi, Dilani, Illakkiya…).
