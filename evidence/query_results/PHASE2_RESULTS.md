# Phase 2 — Recorded Query Results

Captured 2026-06-22 from live Postgres.

---

## 08 — Row counts + detection status

Row counts: `leakage_detection` 404 · `leakage_classification` 343 · `leakage_pattern_registry` 7.

Detection status: **single group** — channel `amazon_fbm`, marketplace `UK`, status **OPEN**,
kill_recommended `false`, **count 404**. earliest_detected 2026-06-02, latest_detected 2026-06-17.
→ **404 OPEN / 0 CLOSED.**

## 09 — pattern_id population + loss

Single group: `pattern_id = NULL`, `pattern_class = NULL`, status OPEN, count 404, distinct_phs 14,
total_daily_loss **£489.23**, total_cumulative_loss **£96,301.55**. → every detection has NULL pattern_id.

## 10 — Classification root causes

| root_cause | frequency | avg_sev | skus | phs |
|------------|-----------|---------|------|-----|
| PRICE_TOO_LOW | 178 | 2.8 | 82 | 14 |
| SHIPPING_HIGH | 148 | 3.0 | 33 | 7 |
| FEE_ANOMALY | 15 | 3.0 | 3 | 1 |
| PAID_MEDIA_BLEED | 2 | 3.0 | 1 | 1 |

RETURNS_ISSUE: **0 rows.** recommended_action map: FIX_PRICE(PRICE_TOO_LOW)=178, FIX_SHIPPING(SHIPPING_HIGH)=148,
FIX_PRICE(FEE_ANOMALY)=15, PAUSE_PPC(PAID_MEDIA_BLEED)=2.

## 11 — PAID_MEDIA_BLEED detail

Both records SKU `WCDTBM2PK+RPR44WH2PK` / ASIN B0DTJ2HFFM / paulr. root_cause_detail:
"PPC 643.3% > threshold 30.0%" and "PPC 640.3% > threshold 30.0%". shipping_pct ~19%, paid_media_pct ~643%,
returns_pct 0. daily_loss_gbp £0.10. → ACOS/ratio-based, **not** L1's zero-conversion test.

## 12 — SHIPPING_HIGH detail (sample)

CERU36150RE/Jasmini "Shipping 58.2% > threshold 25.0%"; CL3TGY3PK "32.7%"; CENU25200BM "78.3%";
RWWPSN12GY/utharsika "66.5%". → uses **25% threshold = protocol L2 threshold**; FIX_SHIPPING action.

## 13 — daily_loss formula change

| run | skus | max_loss | sum_loss |
|-----|------|----------|----------|
| 2026-06-02 | 33 | 0.67 | 2.17 |
| 2026-06-11 | 27 | 0.67 | 2.51 |
| 2026-06-15 | 26 | 0.18 | 1.22 |
| **2026-06-16** | 73 | **11.58** | **55.10** |
| **2026-06-17** | 63 | **50.08** | **414.44** |

→ Formula visibly changes between 06-15 and 06-16 (max loss jumps 0.18 → 11.58 → 50.08). One sampled SKU:
nnr_30d −4.49 but daily_loss_gbp 50.08 (inconsistent with earlier nnr/30 basis).

## 14 — Detected SKUs vs active 7-day PPC (L3 overlap probe)

Of OPEN detections: total_detected_skus **94** · detected_with_active_ppc(>£3, 7d) **2** ·
active PPC spend on those = £55.67. → existing engine is **not** intersecting net-negative with live PPC;
L3's specific condition is essentially unaddressed.

## Supporting views confirmed (pg_views)

- `development.vw_fbm_uk_order_profitability` — joins order_transaction + amz_order_expenses (ACTUAL fees:
  Commission/DigitalServicesFee/RefundCommission) + order_shipping_billing_detail + amazon_returns; 20% COGS
  proxy; 120-day window; filters AMAZON / fba_sales=false / UK.
- `development.vw_fbm_uk_sku_daily_nnr` — 30-day SKU rollup; nulls figures when cost data incomplete.
- `development.vw_top_10_leakage` — priority_score = daily_loss × days_red × severity_weight; is_overdue via
  SLA + `development.actions`.
