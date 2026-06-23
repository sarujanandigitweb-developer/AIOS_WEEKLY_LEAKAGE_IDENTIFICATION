# Final Architecture Decision

**Decision:** **OPTION B — Build the weekly report layer on top of the existing leakage framework.**
**Date:** 2026-06-22 · **Status:** RECORDED — pending Bietrick sign-off · **Basis:** evidence only (no new findings invented).

---

## 1. Options compared

| Option | All 5 analyses? | Reuses existing assets? | Duplicate truth? | Closure loop? | Verdict |
|--------|-----------------|-------------------------|------------------|---------------|---------|
| **A — Reuse as-is** | ❌ No (L1, L4, L5 missing) | ✅ Yes | ✅ None | ❌ No | REJECTED |
| **B — Extend on top** | ✅ Yes | ✅ Yes | ✅ Controlled | ✅ Added | **CHOSEN** |
| **C — Separate system** | ✅ Yes | ❌ No | ❌ Creates L2/L3 duplicates | ⚠️ Two states | REJECTED |

## 2. Why B (evidence trace)

1. **The foundation already exists and uses actual Amazon fees rather than the protocol's 15% assumption.**
   `vw_fbm_uk_order_profitability` joins the four needed tables and uses **ACTUAL Amazon fees**
   (Commission/DigitalServicesFee/RefundCommission) plus actual postage — instead of the protocol's assumed 15%.
   Reuse it for L2/L3/L5. *(Evidence: view definition,
   `PHASE2_RESULTS.md`.)*
2. **3 of 5 analyses already have a pattern class.** PAID_MEDIA_RUNAWAY→L1/L3, SHIPPING_HIGH→L2,
   RETURNS_ISSUE→L4 in `leakage_pattern_registry`. The taxonomy is reusable as report labels. *(7-row registry.)*
3. **A separate system guarantees duplicate truth.** SHIPPING_HIGH (148, 25% threshold) and 404 net-negative
   detections already exist; an independent L2/L3 would issue a second competing status per ASIN.
   *(Evidence: `DUPLICATE_TRUTH_ASSESSMENT.md`.)*
4. **Reuse-only cannot deliver L1, L4, L5.** RETURNS_ISSUE has 0 records; PAID_MEDIA_BLEED is ACOS-based not
   zero-conversion; no monthly PH rollup exists. *(Evidence: `PHASE2_RESULTS.md` 10/11.)*
5. **The protocol supplies the missing closure loop.** Engine is 404 OPEN / 0 CLOSED; the protocol's
   Following-Monday verification (REQ-001 §6) becomes the closure mechanism written back to
   `leakage_detection`. *(Evidence: `08` status summary.)*

## 3. What OPTION B builds (scope outline — for the build phase, not this phase)

- **Reuse:** `vw_fbm_uk_order_profitability`, `vw_fbm_uk_sku_daily_nnr`, `leakage_pattern_registry`.
- **Add query logic:** L1 (zero-conv PPC 7d from `ppc_performance`, `record_type='ad'`), L4 (refund rate from
  `order_transaction` `order_status='Refunded'`), L5 (monthly PH margin trend over 3 months).
- **Add output:** weekly PH-facing HTML report (sidebar/tabs/ticks/ASIN tags/equations).
- **Add closure:** Monday verification updates `leakage_detection.status` → CLOSED, one status of record.
- **Standardise first:** resolve the `daily_loss_gbp` formula inconsistency (06-15 → 06-16 jump) before reuse.

## 4. Conditions / guardrails

- `ss_name` must be normalised to LEDSone UK / DCVoltage UK via ILIKE at query time.
- Treat absolute net as directional (COGS 20% / fee / VAT assumptions per REQ-001 §4).
- No build begins until Bietrick signs off this decision.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Record the architecture decision and its evidence trace |
| Business Question Supported | "Reuse, extend, or replace — and why?" |
| Evidence Used | Options A/B/C docs; Phase 1+2 results; duplicate-truth assessment; view definitions |
| Reviewer | Bietrick (TL) — sign-off required |
| Status | RECORDED — awaiting sign-off |
| Pass/Fail Rule | PASS if a single option is chosen with a complete evidence trace and no invented findings → passes |
| Next Step | Bietrick signs off OPTION B; build phase opens a separate implementation requirement |
| Known Limitations | Decision is architectural; effort, sequencing, and the formula fix are deferred to the build phase |
