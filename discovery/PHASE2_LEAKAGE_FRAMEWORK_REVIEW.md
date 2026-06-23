# PHASE 2 — Existing Leakage Framework Review

**Principle applied:** Existing Asset First · Evidence First · Duplicate Truth Prevention
**Date:** 2026-06-22
**Scope:** `development.leakage_detection`, `development.leakage_classification`,
`development.leakage_pattern_registry` + the three supporting `development` views.
**Evidence:** `evidence/postgres_queries/08–14_*.sql` and matching results.

---

## 1. Why the framework exists

It is a **daily, SKU-level, 30-day-window net-negative monitoring engine** for UK Amazon FBM. Detection runs
are stamped `detect_YYYY-MM-DD_amazon_fbm_UK`; 11 runs were recorded between **2026-06-02 and 2026-06-17**.
It detects net-negative SKUs (via `vw_fbm_uk_sku_daily_nnr`), classifies them by root cause with an SLA, and
surfaces the worst via `vw_top_10_leakage`. It is an **internal continuous monitor**, not a weekly,
PH-facing, 7-day action protocol.

> **Labelled as inference (C-3):** the framework's *purpose* above is **inferred** from observable signals
> (run-id naming `detect_YYYY-MM-DD_amazon_fbm_UK`, daily cadence, and view structure) — no stored DB comment
> states it. Likewise, the **pattern→analysis mapping** (PAID_MEDIA_RUNAWAY→L1/L3, SHIPPING_HIGH→L2,
> RETURNS_ISSUE→L4) used here and in the architecture review is an **analyst inference from names/thresholds**,
> not a mapping stored in the database.

---

## 2. Pattern registry findings (`leakage_pattern_registry`, 7 rows)

| Pattern class | Threshold reference (BLOS key) | Default owner | recurrence_count | last_triggered_at |
|---------------|-------------------------------|---------------|------------------|-------------------|
| PRICING_DRIFT | `fbm_organic_margin_floor` | Bietrick | 0 | NULL |
| PAID_MEDIA_RUNAWAY | `acos_ceiling_pct`, `paid_media_bleed_pct` | Bietrick | 0 | NULL |
| SHIPPING_HIGH | `postage_ceiling_*` | Bietrick | 0 | NULL |
| RETURNS_ISSUE | `returns_high_pct`, `refund_rate_trigger_pct` | Bietrick | 0 | NULL |
| FEE_ANOMALY | `amazon_referral_fee_ceiling`, `fee_anomaly_pct` | Sathees | 0 | NULL |
| PRICE_TOO_LOW | `fbm_organic_margin_floor` | Bietrick | 0 | NULL |
| STOCK_RISK | `minimum_volume_for_detection` | Bietrick | 0 | NULL |

**Critical finding:** every pattern shows `recurrence_count = 0` and `last_triggered_at = NULL`, and **every
`leakage_detection.pattern_id` is NULL** (evidence `09_detection_by_pattern.sql`). The taxonomy was designed
but **never wired** to the detection data. It is a governance blueprint, structurally disconnected from the
live engine.

---

## 3. Detection findings (`leakage_detection`, 404 rows)

| Metric | Value | Evidence |
|--------|-------|----------|
| Total records | 404 | `08_leakage_row_counts.sql` |
| Status | **404 OPEN / 0 CLOSED** | `08_detection_summary.sql` |
| Channel / marketplace | 100% `amazon_fbm` / `UK` | `08_detection_summary.sql` |
| Distinct PHs flagged | 14 | `08_detection_summary.sql` |
| Total cumulative loss (open) | £96,301.55 ⚠ **caveat: mixes two incompatible `daily_loss_gbp` formulas (06-15→06-16) — treat as indicative only, do not quote as exact** | `09_detection_by_pattern.sql` |
| Oldest red date | 2025-10-17 (243 days) | `13_daily_loss_anomaly.sql` |

**Run history shows a formula change.** Runs 2026-06-02 → 06-15 show max `daily_loss_gbp` ≈ £0.67/SKU
(consistent with `nnr_30d ÷ 30`). Runs 06-16 and 06-17 jump to £11.58 and £50.08/SKU — a 25×–190× spike
(evidence `13_daily_loss_anomaly.sql`). One sampled SKU shows `nnr_30d = -4.49` but `daily_loss_gbp = 50.08`,
internally inconsistent with the earlier formula. **The £96k cumulative figure mixes two incompatible
formulas and must be treated with caution.**

**Zero closures = no feedback loop.** No record has ever moved to CLOSED. SKU `LSRP260YB+RPR44WH` (utharsika)
has been red for 217 days with no closure. The engine accumulates detections without verifying resolution —
the exact accountability gap the weekly protocol's "following Monday" verification is designed to fill.

---

## 4. Classification findings (`leakage_classification`, 343 rows)

| Root cause | Frequency | Severity | Distinct SKUs | Distinct PHs | Recommended action | Cost-% populated |
|------------|-----------|----------|---------------|--------------|--------------------|------------------|
| PRICE_TOO_LOW | 178 (51.9%) | avg 2.8 | 82 | 14 | FIX_PRICE | none |
| SHIPPING_HIGH | 148 (43.2%) | 3 | 33 | 7 | FIX_SHIPPING | `shipping_pct` ✅ (e.g. 78.3%, 58.2%) |
| FEE_ANOMALY | 15 (4.4%) | 3 | 3 | 1 | FIX_PRICE | actual fee data |
| PAID_MEDIA_BLEED | 2 (0.6%) | 3 | 1 | 1 (paulr) | PAUSE_PPC | `paid_media_pct` ✅ (643%) |
| **RETURNS_ISSUE** | **0** | — | — | — | — | — |

Notes (evidence `10–12_*.sql`):
- `SHIPPING_HIGH` uses the **same 25% threshold** as protocol L2 ("Shipping 78.3% > threshold 25.0%").
- `PAID_MEDIA_BLEED` uses an **ACOS/spend-ratio threshold (30%)**, e.g. "PPC 643.3% > threshold 30.0%" — this
  is **not** L1's zero-conversion test, and only 2 records exist for 1 SKU.
- `RETURNS_ISSUE` is defined in the registry but has **zero** detections/classifications — refund leakage is
  not being detected today.
- Many `PRICE_TOO_LOW` SLA deadlines (`sla_deadline = 2026-06-22 08:00`) are due today/overdue with no logged
  action.

---

## 5. Coverage findings vs the 5 protocol analyses

| Protocol | Existing coverage | Evidence | Verdict |
|----------|-------------------|----------|---------|
| L1 zero-conv PPC (7d) | ACOS-based PAID_MEDIA_BLEED only (30d, 2 records) — not zero-conversion | `11_paid_media_detail.sql` | **MISSING** |
| L2 shipping >25% (7d) | SHIPPING_HIGH exists, same 25% threshold, but 30-day NNR-based, 33 SKUs | `12_shipping_high_detail.sql` | **PARTIAL** |
| L3 net-neg + PPC>£5 (7d) | Net-negative detected (all 404) but not intersected with 7-day PPC>£5; only 2/94 open SKUs have active PPC | `14_detected_skus_vs_ppc.sql` | **PARTIAL** |
| L4 refund rate >10% (30d) | RETURNS_ISSUE pattern empty; no refund-rate detection | `10_root_cause_summary.sql` | **MISSING** |
| L5 PH margin trend (3mo) | SKU-level/30-day only; no monthly PH rollup or consecutive-decline logic | framework windows | **MISSING** |

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Establish exactly what the existing leakage engine does and does not do, with evidence |
| Business Question Supported | "Does the existing framework already perform any of L1–L5?" |
| Evidence Used | `evidence/postgres_queries/08–14` + matching results; `pg_views` definitions |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if each L1–L5 coverage verdict cites a query result |
| Next Step | Quantify collision risk in `DUPLICATE_TRUTH_ASSESSMENT.md` |
| Known Limitations | `daily_loss_gbp` formula changed mid-series; cumulative loss figures are not internally consistent |
