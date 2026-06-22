# Duplicate Truth Assessment

**Principle applied:** Duplicate Truth Prevention
**Date:** 2026-06-22
**Question:** If the Weekly Leakage Protocol runs, where would it produce a **second competing source** of a
fact the existing framework already produces — and how severe is the risk?

---

## 1. The two systems being compared

| Dimension | Existing framework (`development`) | Weekly protocol (REQ-001) |
|-----------|------------------------------------|---------------------------|
| Cadence | Daily | Weekly (Monday) |
| Window | 30-day rolling NNR | 7-day (L1–L3), 30-day (L4), 3-month (L5) |
| Grain | SKU | ASIN / SKU per PH |
| Audience | Internal monitor | PH-facing action lists (HTML) |
| Closure | None (404 OPEN / 0 CLOSED) | Following-Monday verification |

These are **different tools** — but they read the same underlying tables, so overlap is real.

---

## 2. Overlap and duplicate-truth risk

| Existing asset | Weekly protocol output | Nature of overlap | Risk | Recommendation |
|----------------|------------------------|-------------------|------|----------------|
| `leakage_detection` (net-neg SKU, 30d) | **L3** net-negative ASIN (7d) | Same SKUs surface in both; different window + formula | **MEDIUM** | Treat L3 as a 7-day early-warning view; existing detection is the 30-day structural confirmation. One closure status, not two. |
| `leakage_classification: SHIPPING_HIGH` (148, 25% threshold) | **L2** shipping >25% (7d) | Same root cause, same threshold, different window; 33 SKUs already carry `FIX_SHIPPING` | **MEDIUM** | Reuse classification as the seed; L2 adds 7-day urgency. Do not issue two separate shipping instructions for one ASIN. |
| `leakage_classification: PAID_MEDIA_BLEED` (2, ACOS-based) | **L1** zero-conv PPC (7d) | Both end in PAUSE_PPC but different logic + scale | **LOW** | Complementary, not duplicate — different detection methodology. |
| `staging_ai.amazon_fbm_returns_opportunity_engine_v1` | **L4** refund rate (30d) | Same `amazon_returns` source; £-leakage vs rate-% metric | **LOW** | No live collision (view not surfaced to Bietrick). Could feed L4. |
| `staging_ai.fbm_sku_daily_nnr_snapshot` / `v_fbm_nnr_trend_signals_v1` | **L5** PH margin trend (3mo) | NNR captured, but only 1 snapshot date | **LOW** (today) | No trend history yet; becomes MEDIUM as snapshots accumulate. |

---

## 3. The core duplicate-truth hazard

The single biggest hazard is **two systems telling the same PH two different things about the same ASIN**:
- Existing engine: a SKU flagged `FIX_SHIPPING` / OPEN since June, 30-day basis.
- Weekly L2/L3: the same ASIN on a fresh 7-day list with a Wednesday deadline.

If both are issued independently, the PH receives **conflicting instructions and conflicting "is this still a
problem?" signals**, and there is no single closure state. This is precisely the duplicate truth the AIOS
principle forbids.

---

## 4. Implication for architecture

Duplicate-truth analysis points away from a **separate** system (which guarantees two competing lists for L2
and L3) and toward **one shared truth**: the weekly protocol should read the existing profitability views and
write closure status back into the existing `leakage_detection` lifecycle, so each ASIN has **one** status of
record. This is examined in the architecture review.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Identify and rate every point where the weekly protocol would duplicate existing truth |
| Business Question Supported | "Will the weekly protocol create a second competing source of any leakage fact?" |
| Evidence Used | Phase 2 findings (`PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md`) + `14_detected_skus_vs_ppc.sql` + view defs |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if every overlap is rated and carries a de-duplication recommendation |
| Next Step | Feed risk ratings into `architecture_review/FINAL_ARCHITECTURE_DECISION.md` |
| Known Limitations | Overlap magnitude estimated from a single discovery snapshot; exact SKU-overlap counts would need a dedicated reconciliation query |
