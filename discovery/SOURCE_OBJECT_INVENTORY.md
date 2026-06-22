# Source Object Inventory

**Principle applied:** Queryability First · Evidence First
**Date:** 2026-06-22
**Evidence:** `evidence/postgres_queries/02_core_table_details.sql`, `07_relationships.sql` and results.

---

## 1. Tables

| Table | Purpose | Key columns | Est. rows | Last evidence observed |
|-------|---------|-------------|-----------|------------------------|
| `public.order_transaction` | Order lines: revenue, status, identifiers, PH, account | `order_id`, `asin`, `sku`, `item_price`, `quantity`, `order_status`, `order_date`, `ss_name`, `user_name`, `market_place`, `source_name`, `fba_sales` | 1,218,870 | order date max 2026-06-22 |
| `public.ppc_performance` | PPC metrics per SKU/day (+ PH owner, ASIN via `ref_id`) | `sku`, `ref_id`, `spend`, `clicks`, `impressions`, `orders` (=conversions), `user_name`, `ss_name`, `marketplace`, `date`, `record_type` | 24,565,917 | UK date max 2026-06-22 |
| `public.ppc_etl_performance_data` | Raw PPC ETL feed (no `user_name`) | `sku`, `ref_id`, `spend`, `orders`, `clicks`, `impressions`, `date` | 24,510,852 | — |
| `public.order_shipping_billing_detail` | Actual shipping cost per order | `order_id`, `carrier_charge`, `carrier_charge_currency`, `shipping_template_price`, `carrier_name` | 1,088,958 | — |
| `public.amazon_returns` | Amazon returns / refunds | `order_id`, `asin`, `sku`, `status`, `reason`, `refunded_amount`, `label_cost`, `fulfilment`, `market_place`, `request_date` | 3,772 | request date max 2026-06-17 |
| `public.amz_order_expenses` | Settlement fee/expense lines (ACTUAL fees) | `order_id`, `seller_sku`, `charge_type`, `amount`, `market_place_name`, `date` | 412,313 | — |
| `staging_ai.fbm_sku_daily_nnr_snapshot` | Pre-computed 30-day NNR per SKU | `sku`, `ph_owner`, `channel`, `marketplace`, `nnr_30d`, `daily_loss`, `sales_30d`, `expenses_30d`, `snapshot_date` | 2,287 | snapshot date 2026-06-17 (1 day only) |
| `development.leakage_detection` | Daily SKU leakage detections | `sku`, `asin`, `ph_user_name`, `nnr_30d`, `daily_loss_gbp`, `cumulative_loss_gbp`, `first_red_date`, `days_red`, `kill_recommended`, `pattern_id`, `status`, `detection_run_id` | 404 | detected_at max 2026-06-17 |
| `development.leakage_classification` | Root-cause + SLA per detection | `leakage_detection_id`, `sku`, `ph_user_name`, `root_cause`, `severity_tier`, `sla_hours`, `sla_deadline`, `recommended_action`, `shipping_pct`, `paid_media_pct`, `fee_pct`, `returns_pct` | 343 | classified_at max 2026-06-17 |
| `development.leakage_pattern_registry` | Leakage pattern taxonomy | `pattern_class`, `description`, `control_mechanism`, `default_owner`, `recurrence_count`, `last_triggered_at` | 7 | created 2026-06-02, never updated |

---

## 2. Views

| View | Purpose | Built from | Window | Notes |
|------|---------|-----------|--------|-------|
| `development.vw_fbm_uk_order_profitability` | Per-order, per-SKU NNR | `order_transaction` + `amz_order_expenses` + `order_shipping_billing_detail` + `amazon_returns` | 120 days | Uses **ACTUAL Amazon fees** (Commission/DigitalServicesFee/RefundCommission), actual postage, **20% COGS proxy**. Filters `source_name='AMAZON'`, `fba_sales=false`, `market_place='UK'` |
| `development.vw_fbm_uk_sku_daily_nnr` | 30-day SKU NNR rollup | `vw_fbm_uk_order_profitability` | 30 days | Emits `nnr_30d`, `daily_loss`, `orders_30d`, `expenses_30d`; nulls out figures when cost data incomplete |
| `development.vw_top_10_leakage` | Top 10 open leakages, priority-ranked | `leakage_detection` + `leakage_classification` + `leakage_pattern_registry` | latest run | Computes `priority_score = daily_loss × days_red × severity_weight`; `is_overdue` from SLA + `actions` table |

> Additional related views in `staging_ai` (not part of the development engine, observed during scan):
> `amazon_fbm_returns_opportunity_engine_v1` (returns classification over `amazon_returns`),
> `v_fbm_nnr_trend_signals_v1` (NNR trend over the snapshot), and the `v_sentinel_*` leakage views.

---

## 3. Relationship / join map

| Source | Join column | Target | Join type | Coverage |
|--------|------------|--------|-----------|----------|
| `order_transaction` | `order_id` | `order_shipping_billing_detail` | LEFT JOIN | 73.5% match (last 30d) |
| `order_transaction` | `order_id` | `amazon_returns` | LEFT JOIN | sparse (3,772 returns) |
| `order_transaction` | `order_id` | `amz_order_expenses` | LEFT JOIN | settlement-dependent |
| `order_transaction` | `sku` | `ppc_performance` | LEFT JOIN (via date window) | many-to-many |
| `order_transaction` | `asin` ↔ `ref_id` | `ppc_performance` | alternative ASIN join | `ref_id` confirmed = ASIN |
| `leakage_detection` | `id` | `leakage_classification` | 1-to-many (FK) | 343 of 404 classified |
| `leakage_detection` | `pattern_id` | `leakage_pattern_registry` | FK | **NEVER populated (all NULL)** |

**Confirmed identity facts (evidence `04_ppc_refid_is_asin.sql`):** in `ppc_performance`, `ref_id` holds the
ASIN (e.g. `B07QNR618G`); `record_type='ad'` is the SKU-level grain carrying ASIN; account names appear in
`ss_name` as variants ("amazon Ledsone", "ledsone", "amazon Dcvoltage", …) requiring `ILIKE` matching.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Authoritative catalogue of tables, views, columns, and joins used by the protocol |
| Business Question Supported | "What exactly can I query, and how do the objects connect?" |
| Evidence Used | `02_core_table_details`, `04_ppc_refid_is_asin`, `07_relationships`, view definitions from `pg_views` |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if every join in the 5 analyses maps to a row in the relationship table above |
| Next Step | Use this catalogue to assess coverage in `validation/COVERAGE_MATRIX.md` |
| Known Limitations | Column lists show the key/used columns, not every column; `ss_name` normalisation is required at query time |
