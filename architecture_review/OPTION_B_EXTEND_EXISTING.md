# Option B — Build the Weekly Report Layer On Top of the Existing Framework

**Premise:** Reuse the existing profitability views and pattern taxonomy as the foundation; add the 3 missing
analyses (L1, L4, L5) and a weekly PH-facing report + closure loop **on top**, so each ASIN has one status of
record.

---

## What this would mean

- **Reuse** `vw_fbm_uk_order_profitability` and `vw_fbm_uk_sku_daily_nnr` as the cost/NNR foundation for L2,
  L3, L5 (they already use ACTUAL Amazon fees + actual postage + returns).
- **Reuse** `leakage_pattern_registry` classes as the report's classification labels
  (PAID_MEDIA_RUNAWAY→L1/L3, SHIPPING_HIGH→L2, RETURNS_ISSUE→L4).
- **Add** L1 (zero-conv PPC, 7d from `ppc_performance`), L4 (refund rate from `order_transaction`), L5
  (monthly PH margin trend) as new query logic in the weekly layer.
- **Add** the weekly HTML report (PH-facing) and write closure status back into the existing
  `leakage_detection` lifecycle — supplying the missing 404-OPEN/0-CLOSED feedback loop.

## Pros (evidence-backed)

| Strength | Evidence |
|----------|----------|
| Foundation already exists and **uses actual Amazon fees rather than the protocol's 15% assumption** | `vw_fbm_uk_order_profitability` definition |
| 3 of 5 analyses map to **existing pattern classes** | `leakage_pattern_registry` (7 rows) |
| Avoids duplicate truth on L2/L3 by sharing one status of record | `DUPLICATE_TRUTH_ASSESSMENT.md` |
| Adds the **closure loop** the engine lacks | 404 OPEN / 0 CLOSED |
| Data for the 3 missing analyses is **query-verified to exist** | `QUERYABILITY_CHECK.md`, Phase 1 live probes |

## Cons / costs

- Requires new query logic for L1, L4, L5 and a report generator (more than Option A).
- Must reconcile window differences (7-day weekly vs 30-day engine) carefully to avoid double-issuing
  instructions for the same ASIN.
- Inherits the engine's `daily_loss_gbp` formula inconsistency — must standardise before reuse.

## Verdict

**RECOMMENDED.** Option B is the only option that (a) delivers all 5 analyses, (b) reuses the existing
foundation and taxonomy, (c) prevents duplicate truth on the overlapping analyses, and (d) adds the closure
loop. It honours Existing Asset First and Duplicate Truth Prevention simultaneously.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Evaluate extending the existing framework with a weekly report layer |
| Business Question Supported | "Can we reuse the foundation and add only what's missing, without duplicate truth?" |
| Evidence Used | Phase 1 + Phase 2 results; view definitions; duplicate-truth assessment |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE — option recommended |
| Pass/Fail Rule | PASS(option) if all 5 analyses deliverable AND duplicate truth controlled → passes |
| Next Step | Confirm against Option C, then record in `FINAL_ARCHITECTURE_DECISION.md` |
| Known Limitations | Effort/timeline not estimated here; this is a feasibility/architecture judgement, not a build plan |
