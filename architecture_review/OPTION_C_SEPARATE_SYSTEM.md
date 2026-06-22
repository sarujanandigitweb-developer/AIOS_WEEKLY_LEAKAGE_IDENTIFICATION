# Option C — Build a Completely Separate Weekly Protocol System

**Premise:** Build the weekly protocol as a standalone system with its own tables, its own queries, and its
own report, ignoring the existing `development` leakage framework.

---

## What this would mean

- New independent objects compute L1–L5 directly from `public` base tables.
- The existing engine continues to run in parallel, untouched.

## Pros

- Clean-room design; full freedom over windows, grain, and output.
- No dependency on the engine's inconsistent `daily_loss_gbp` formula.
- Fast to reason about in isolation.

## Cons (evidence-backed — this is where it fails)

| Problem | Evidence | Consequence |
|---------|----------|-------------|
| **Guaranteed duplicate truth on L2 + L3** | SHIPPING_HIGH (148, 25% threshold) and 404 net-negative detections already exist | Two competing flagged-ASIN lists; a PH gets two different statuses for one ASIN |
| **Two closure states** | Existing engine has its own OPEN/CLOSED lifecycle | No single source of truth for "is this ASIN still leaking?" |
| **Re-derives an inferior cost model** | `vw_fbm_uk_order_profitability` already uses ACTUAL fees; a fresh build would re-assume 15% | Less accurate than what exists |
| **Wastes existing taxonomy** | `leakage_pattern_registry` already maps to 3 analyses | Re-inventing classification labels |
| **Violates Existing Asset First** | Phase 1/2 found reusable views + taxonomy | Direct breach of the governing principle |

## Verdict

**REJECTED.** Option C directly violates Duplicate Truth Prevention (it creates a second competing source for
L2 and L3) and Existing Asset First (it ignores reusable, more-accurate views). The only thing it adds over
Option B is isolation — which is precisely the property that causes the duplicate-truth harm.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Evaluate a standalone separate system |
| Business Question Supported | "Should the weekly protocol be built independently of the existing engine?" |
| Evidence Used | `DUPLICATE_TRUTH_ASSESSMENT.md`, Phase 2 results, view definitions |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE — option rejected |
| Pass/Fail Rule | PASS(option) only if it avoids duplicate truth → fails (creates duplicate L2/L3 truth) |
| Next Step | Record final decision in `FINAL_ARCHITECTURE_DECISION.md` |
| Known Limitations | A separate system could be made safe only by adding cross-system reconciliation — which converges on Option B anyway |
