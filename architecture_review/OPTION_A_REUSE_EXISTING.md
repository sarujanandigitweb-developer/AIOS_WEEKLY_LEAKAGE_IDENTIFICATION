# Option A — Reuse the Existing Leakage Framework As-Is

**Premise:** Deliver the weekly protocol entirely from the existing `development` leakage engine
(`leakage_detection` + `leakage_classification` + `leakage_pattern_registry` + the 3 views), with no new
analysis logic.

---

## What this would mean

- Bietrick's weekly PH lists are generated from existing detections/classifications and `vw_top_10_leakage`.
- No new queries for L1–L5; the engine's existing root causes (PRICE_TOO_LOW, SHIPPING_HIGH, FEE_ANOMALY,
  PAID_MEDIA_BLEED) stand in for the protocol's analyses.

## Pros

- Zero new objects; lowest build effort.
- Single source of truth by construction — no duplicate truth risk.
- Reuses the better cost model (ACTUAL Amazon fees via `vw_fbm_uk_order_profitability`).

## Cons (evidence-backed)

| Gap | Evidence | Consequence |
|-----|----------|-------------|
| **L1 not covered** | PAID_MEDIA_BLEED is ACOS-based (30d), 2 records for 1 SKU; protocol needs zero-conversion 7d (50–120 ASINs) | Cannot produce L1 at all |
| **L4 not covered** | RETURNS_ISSUE pattern has **0** records | Cannot produce refund-rate list |
| **L5 not covered** | Engine is SKU-level/30-day; no monthly PH rollup or consecutive-decline logic | Cannot produce PH margin trend |
| **Wrong windows** | Engine is 30-day; L1–L3 require 7-day | Different result set; not the protocol |
| **Wrong grain/audience** | SKU-level internal monitor; protocol is ASIN/PH-facing HTML | No PH report output |
| **No closure loop** | 404 OPEN / 0 CLOSED | Protocol's Monday verification unsupported |

## Verdict

**REJECTED.** Option A cannot deliver 3 of the 5 analyses (L1, L4, L5) and cannot match the required windows,
grain, audience, or closure loop. Reuse-only is infeasible.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Evaluate pure reuse of the existing framework |
| Business Question Supported | "Can we satisfy the protocol with no new logic?" |
| Evidence Used | `PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md`, `PHASE2_RESULTS.md` (08–14) |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE — option rejected |
| Pass/Fail Rule | PASS(option) only if all 5 analyses are deliverable as-is → fails (3 missing) |
| Next Step | Evaluate Option B |
| Known Limitations | Assessment assumes the engine is not re-architected; only as-is reuse considered here |
