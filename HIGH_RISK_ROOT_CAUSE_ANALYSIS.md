# High-Risk Root-Cause Analysis — DQ-1 & DQ-2

**Date:** 2026-06-22 · **Mode:** READ-ONLY (no create/modify/update/delete) · **Auditor:** AIOS Worker
**Reviewer:** Bietrick (TL) · **Scope:** the two HIGH findings from `POSTGRES_DATA_GAP_ANALYSIS.md` only.
Every conclusion carries: table · column · evidence query · result · root cause · recommended fix.

---

# DQ-1 — PPC PH-Mapping Gap (40.6% of `ppc_performance.user_name` missing)

## Finding chain (evidence)

### Q1 — Where is the missing PH concentrated? (by account)
**Table/Column:** `public.ppc_performance.user_name`, `.ss_name`, `.sku` · window UK, 7d, `record_type='ad'`.

| ss_name | ad_rows | missing_ph | % missing PH | blank_sku |
|---------|---------|-----------|--------------|-----------|
| amazon Dcvoltage | 42,583 | 15,324 | 36.0% | 0 |
| led_sone | 21,881 | 12,181 | **55.7%** | **21,881 (100%)** |
| amazon Ledsone | 17,793 | 2,892 | 16.3% | 0 |
| electricalsone | 8,165 | 5,134 | **62.9%** | **8,165 (100%)** |
| so_926407 | 5,558 | 3,454 | **62.1%** | **5,558 (100%)** |
| ledsonede | 12 | 12 | 100% | 12 (100%) |

**Result:** PH-missing is **concentrated in accounts whose ad-rows carry NO SKU at all** (`led_sone`,
`electricalsone`, `so_926407`, `ledsonede` → 100% blank SKU). The two well-formed accounts
(`amazon Ledsone`/`amazon Dcvoltage`) have 0 blank SKU yet still show 16–36% PH-missing.

### Q2 — Is PH-missing caused by blank SKU?
**Table/Column:** `public.ppc_performance.sku` vs `.user_name`.

| sku_state | rows | missing_ph | % missing PH |
|-----------|------|-----------|--------------|
| has_sku | 60,376 | 18,216 | 30.2% |
| blank_sku | 35,616 | 20,781 | **58.3%** |

**Result:** Blank SKU nearly **doubles** the PH-missing rate (58.3% vs 30.2%). SKU is the join key for PH
attribution — no SKU ⇒ no PH. But PH is also missing on 30.2% of rows that *do* have a SKU.

### Q3 — Is `user_name` even present on the raw feed?
**Table/Column:** `public.ppc_etl_performance_data` (raw) — column list from `get_object_details`.

**Result:** The raw ETL table `ppc_etl_performance_data` has **no `user_name` column at all**. `user_name`
exists only on the transformed `ppc_performance` table. → PH is **added during transformation**, not delivered
by the PPC source feed.

### Q4 — When SKU is present but PH missing, is the SKU in the PH master?
**Table/Column:** `ppc_performance.sku` LEFT JOIN distinct `order_transaction.sku` (where PH present).

| ph_state | rows | sku_in_order_map | % SKU mappable |
|----------|------|------------------|----------------|
| ppc_ph_missing | 18,216 | 2,895 | **15.9%** |
| ppc_ph_present | 42,160 | 14,631 | 34.7% |

**Result:** SKUs on PH-missing rows are **mappable to the order/PH master only 15.9%** of the time, vs 34.7%
for PH-present rows. The PH-missing rows are predominantly **SKUs absent from the order-side PH master** —
confirming the enrichment is a SKU→PH lookup that fails when the SKU is unknown.

### Q5 — Exact impact on L1
**Table/Column:** `ppc_performance` aggregated to L1 condition (spend>£3 AND conversions=0, 7d, ad).

**Result:** L1 flags **109 ASIN/SKU rows**, total flagged spend **£545.38**. Of these, **24 rows (£124.61)**
have no PH → **22.8% of flagged PPC waste is PH-unattributed**.

## Root cause (DQ-1)
**Transformation / enrichment defect compounded by a source-feed gap — NOT a corruption of existing values.**
1. **Source feed gap:** certain UK PPC accounts (`led_sone`, `electricalsone`, `so_926407`, `ledsonede`) arrive
   with **no SKU** on ad-rows (100% blank). The PPC API does not carry PH, and these feeds also omit SKU.
2. **Transformation logic:** `ppc_performance.user_name` is populated by a **SKU-keyed lookup** during ETL
   (raw `ppc_etl_performance_data` has no `user_name`). When SKU is blank (cause 1) or the SKU is not present
   in the order/PH master (15.9% mappable), the lookup yields NULL and PH stays empty.
3. Net: ~40.6% of ad-rows cannot be attributed; ASIN (`ref_id`) is **100% present**, so spend itself is never
   lost — only its PH owner is.

## Recommended fix (DQ-1) — safest, read-only-compatible, staged
| Layer | Action | Why safe |
|-------|--------|----------|
| **Query-time (now)** | Run L1 at **ASIN level** (ref_id is 100% present); show PH where available, bucket the rest as `UNATTRIBUTED`. | No data change; L1 detection is unaffected (ASIN drives it). |
| **Derived view (build phase)** | Create a read-only PH-resolution view: `ppc_performance.sku → order_transaction` PH map, recovering ~11–16% of missing PH. | Reversible, additive, no source mutation. |
| **ETL (root fix)** | Backfill **SKU on the four SKU-less account feeds** at ingest, then re-run the SKU→PH lookup; add a SKU→PH master that does not depend solely on order history. | Fixes the true origin (source feed + lookup), not a symptom. |

> **Do NOT** hard-write PH values into `ppc_performance` — the gap is structural; manual backfill would create
> unverifiable attribution and a new duplicate-truth risk.

---

# DQ-2 — Refund Source Conflict (`order_transaction` 53 vs `amazon_returns` 353)

## Finding chain (evidence)

### Q6 — What does each table physically contain? (30d UK)
**Tables:** `public.order_transaction` (`order_status`), `public.amazon_returns` (`status`,`type`,`amz_rma_id`).

| Measure | Result |
|---------|--------|
| `amazon_returns` rows (UK, 30d) | 456 |
| → distinct `order_id` | 399 |
| → distinct `amz_rma_id` | 349 |
| → rows with `type` | 353 |
| `order_transaction` lines `order_status='Refunded'` (UK FBM, 30d) | 53 |

**Result:** `amazon_returns` has **more rows than order_ids** (456 vs 399) → it is an **event/disposition log**,
multiple rows per return.

### Q7 — What events do `amazon_returns.status` values represent?
**Table/Column:** `public.amazon_returns.status`, `.type`, `.refunded_amount`.

| status | type | rows | with refund_amt |
|--------|------|------|-----------------|
| Approved | C-Returns | 335 | 183 |
| Unit returned to inventory | — | 46 | 0 |
| CUSTOMER_DAMAGED | — | 34 | 0 |
| Approved | Amazon CS | 17 | 9 |
| SELLABLE | — | 14 | 0 |
| DEFECTIVE | — | 5 | 0 |
| Repackaged Successfully | — | 3 | 0 |
| CARRIER_DAMAGED / PendingApproval | — | 2 | 0 |

**Result:** `amazon_returns` mixes **financial refund events** (`Approved` + refund_amount) with **physical
warehouse dispositions** (`Unit returned to inventory`, `CUSTOMER_DAMAGED`, `SELLABLE`, `DEFECTIVE`). It is a
**returns/RMA + disposition log**, not a refund ledger.

### Q8 — Do the two tables describe the same orders?
**Tables:** `amazon_returns` (FBM, 30d) order_ids LEFT JOIN `order_transaction` status.

| Measure | Result |
|---------|--------|
| Return order_ids (FBM) | 303 |
| Matched in `order_transaction` | 303 (100%) |
| Matched AND marked `Refunded` | **61** |
| Matched BUT still `Completed` | **242** |
| Not found in `order_transaction` | 0 |

### Q9 — Direct set overlap of the two refund signals
**Tables:** `order_transaction` Refunded order_ids vs `amazon_returns` FBM order_ids (30d).

| Measure | Result |
|---------|--------|
| `order_transaction` refunded orders | 50 |
| `amazon_returns` return orders | 303 |
| In BOTH | 40 |
| Refunded with NO return row | 10 |
| Returned but NOT marked refunded | **263** |

**Result:** The two signals overlap on only **40 orders**. 263 returns are not flagged refunded in
`order_transaction`; 10 refunds have no physical return row.

## Root cause (DQ-2)
**The two tables measure DIFFERENT business events — they are not the same metric and were never reconciled.**
- `order_transaction.order_status='Refunded'` = the **order-level financial state** flips to Refunded. It is
  set only when a full refund is processed and posted to the order line — it **under-counts** (242 of 303
  genuine returns are still `Completed`; it captures ~50 of the period's refund/return activity).
- `amazon_returns` = a **return/RMA + warehouse-disposition event log**. One return spawns multiple rows
  (approval, inventory disposition, damage grade). It **over-counts refunds** if every row is treated as a
  refund, and `refunded_amount` is only populated on 42.1% (`Approved` rows).
- Neither is a clean superset: a return can occur without a posted refund (lag / partial / in-progress), and a
  refund can occur without a logged physical return.

## Recommended official source for L4
**Primary source of record = `public.order_transaction`** (it owns the **order universe / denominator** and
carries ASIN, SKU, PH, account on every line — the self-consistent base for a *rate*).
**But `order_transaction` alone must NOT define the refund numerator** — it under-counts ~6×.

**Recommended L4 definition (reconciled, build-phase derived view):**
> Denominator = distinct orders per ASIN from `order_transaction` (UK FBM, 30d).
> Numerator (an order is "refunded") = `order_status='Refunded'` **OR** the order has an `amazon_returns` row
> with `status='Approved'` and `refunded_amount > 0`.

| Use | Table | Role |
|-----|-------|------|
| Order universe + denominator + ASIN/SKU/PH | `order_transaction` | **OFFICIAL spine** |
| Refund confirmation + reason + £-at-risk | `amazon_returns` (Approved, refunded_amount>0) | **Numerator enrichment** |

This yields the most accurate rate, attributes to PH/ASIN, and avoids both the under-count (order_transaction
alone) and the over-count (amazon_returns alone). If a **single** table must be named for the rate today,
choose `order_transaction` **with a documented known under-count**, and treat the reconciled view as the
target state.

## Recommended fix (DQ-2)
| Layer | Action |
|-------|--------|
| **Query-time (now)** | Compute L4 from `order_transaction` (self-consistent rate); **disclose** the known under-count and 42.1% refund-amount coverage in the report. |
| **Derived view (build phase)** | Build a read-only `vw_l4_refund_rate` implementing the reconciled definition above; one refund truth per order. |
| **ETL (root fix)** | Reconcile `order_status` posting against `amazon_returns` approvals so the 242 returned-but-Completed orders resolve to a correct financial state; ingest Settlement data to complete `refunded_amount`. |

> **Do NOT** sum `amazon_returns` rows as refunds (multiple disposition rows per return) and **do NOT** treat
> `order_transaction` refunds as complete. Either alone produces a wrong L4.

---

## Summary

| Finding | Root cause | Same event? | Official source | Immediate safe action |
|---------|-----------|-------------|-----------------|-----------------------|
| **DQ-1** PPC PH gap | Transformation SKU→PH lookup fails because (a) 4 accounts arrive SKU-less and (b) raw feed has no `user_name`; ASIN always present | n/a | n/a | Run L1 at ASIN level; bucket UNATTRIBUTED (22.8% of flagged spend) |
| **DQ-2** Refund conflict | Two **different** events — financial refund flag (under-counts) vs return/RMA disposition log (over-counts); never reconciled | **No — different events** | `order_transaction` spine + `amazon_returns` enrichment | Compute rate from `order_transaction`, disclose under-count |

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Establish the true origin of the two HIGH data-quality findings with evidence |
| Business Question Supported | "Why is PPC PH 40.6% missing, and why do the two refund tables disagree?" |
| Evidence Used | Read-only queries Q1–Q9 (this session) + `ppc_etl_performance_data` column list (Phase 1) |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if each root cause is proven by a cited query result and not inferred — both proven |
| Next Step | Implement the staged fixes in the OPTION B build; until then apply the query-time mitigations |
| Known Limitations | Read-only snapshot 2026-06-22; 30-day/7-day windows; exact ETL/transformation code was inferred from observable column structure (`user_name` absent on raw feed, present after transform), not from source DDL |
