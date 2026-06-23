# PHASE 1 — Existing Asset Scan

**Principle applied:** Existing Asset First · Evidence First
**Date of scan:** 2026-06-22 (live Postgres)
**Method:** `list_schemas` → `list_objects` per schema → `get_object_details` per core table → targeted SQL.
**Evidence:** `evidence/postgres_queries/01_*.sql` … `06_*.sql` and matching files in `evidence/query_results/`.

---

## 1. Schemas discovered

14 user schemas exist. The ones relevant to leakage:

| Schema | Relevance | Why |
|--------|-----------|-----|
| `public` | **PRIMARY** | Core operational data — orders, PPC, shipping, returns |
| `development` | **HIGH** | Existing leakage detection engine + profitability views (see Phase 2) |
| `staging_ai` | MEDIUM | FBM NNR snapshot, returns opportunity view, HTML backups, AI governance |
| `analytics`, `ph_action_board`, `validation`, `audit`, `governance`, `cppc_*`, `daily_task`, `raw_data`, `message`, `business_intelligence` | LOW / REFERENCE | Not primary to the 5 analyses |

---

## 2. Core data assets that solve the protocol's needs

| Asset (table) | Problem it solves | Est. rows | Owner / origin | Evidence | Status |
|---------------|-------------------|-----------|----------------|----------|--------|
| `public.order_transaction` | All-channel order lines — revenue, status, ASIN/SKU, PH, account, date | 1,218,870 | Platform ETL | `02_core_table_details` | ACTIVE — current to 2026-06-22 |
| `public.ppc_performance` | PPC spend / conversions / clicks / impressions per SKU per day, with PH owner and ASIN (`ref_id`) | 24,565,917 | PPC ETL | `02_core_table_details`, `04_ppc_*` | ACTIVE — UK data 2025-01-01 → 2026-06-22 |
| `public.ppc_etl_performance_data` | Raw ETL feed behind `ppc_performance` (no `user_name`) | 24,510,852 | PPC ETL | `02_core_table_details` | ACTIVE (raw layer) |
| `public.order_shipping_billing_detail` | Actual `carrier_charge` + `shipping_template_price` per order | 1,088,958 | Shipping ETL | `02_core_table_details`, `05_shipping_*` | ACTIVE — 73.5% join coverage (last 30d) |
| `public.amazon_returns` | Amazon return records — reason, refunded amount, status | 3,772 | Returns ETL | `03_returns_*` | ACTIVE — 2026-01-01 → 2026-06-17 |
| `public.amz_order_expenses` | Settlement-style fee/expense breakdown per order (ACTUAL Amazon fees) | 412,313 | Settlement ETL | `02_core_table_details` | ACTIVE |
| `staging_ai.fbm_sku_daily_nnr_snapshot` | Pre-computed 30-day NNR per SKU with `ph_owner` | 2,287 | AIOS snapshot job | `06_nnr_snapshot` | ACTIVE but only **1 snapshot date** (2026-06-17) |

---

## 3. Existing leakage-specific assets (handed to Phase 2 for deep review)

| Asset | Schema | Problem it claims to solve | Rows | Status |
|-------|--------|----------------------------|------|--------|
| `leakage_detection` | development | Daily SKU-level net-negative detection | 404 | ACTIVE, all OPEN |
| `leakage_classification` | development | Root-cause + SLA classification of detections | 343 | ACTIVE |
| `leakage_pattern_registry` | development | Canonical 7-pattern leakage taxonomy | 7 | STATIC (never triggered) |
| `vw_fbm_uk_order_profitability` | development | Per-order NNR using actual fees + postage + returns | view | ACTIVE |
| `vw_fbm_uk_sku_daily_nnr` | development | 30-day SKU NNR rollup | view | ACTIVE |
| `vw_top_10_leakage` | development | Priority-ranked top 10 open leakages | view | ACTIVE |

> These six objects are the heart of the investigation and are fully analysed in
> `PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md`. Phase 1's role was only to **discover that they exist**.

---

## 4. What is NOT in the database (confirmed gaps)

| Missing / weak | Evidence | Impact |
|----------------|----------|--------|
| Actual COGS, Platform fee, VAT | Protocol §5 + absence in schema | Assumed 20% / 15% / 20% — directional only |
| `shipping_template_price` largely empty | `05_shipping_template_check` → only 358 / 9,766 rows populated (3.7%) | Protocol's "additional shipping template" has near-zero data |
| Shipping coverage < stated | `05_shipping_coverage` → 73.5% (protocol stated 77%) | 26.5% of orders have no carrier charge |
| PH mapping incomplete | `04_ph_mapping` → 83.4% mapped in last 30d | ~1 in 6 UK FBM orders unattributed |
| PH count: observed vs protocol | `04_ph_mapping` → **24 distinct PHs observed** (last-30d Amazon UK FBM) vs **28 PHs listed in the protocol** | The 4-PH gap is **observed-vs-protocol**, not missing data — likely PHs with no orders in the window. Do not conflate the measured 24 with the protocol's 28 |
| No PostgreSQL views in `public` | `list_objects(public, view)` returned `[]` | All reusable views live in `development`/`staging_ai` |

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Record every existing asset relevant to the protocol, with evidence, before any build |
| Business Question Supported | "What already exists that could serve the 5 leakage analyses?" |
| Evidence Used | `evidence/postgres_queries/01–06` + matching `query_results/` |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if every asset claim cites a recorded query result |
| Next Step | Catalogue exact columns + joins in `SOURCE_OBJECT_INVENTORY.md` |
| Known Limitations | Row counts are `pg_stat` estimates; coverage % measured on last-30-day windows only |
