# Coverage Matrix — L1–L5 vs Existing Framework

**Legend:** FULL = existing engine already produces it · PARTIAL = related logic exists, wrong window/grain ·
MISSING = no existing equivalent.
**Evidence:** `evidence/query_results/PHASE2_RESULTS.md` (08–14), Phase 1 live probes.

---

| Analysis | Requirement (REQ-001) | Existing coverage | Source if built (Option B) | Verdict |
|----------|------------------------|-------------------|----------------------------|---------|
| **L1** Zero-conv PPC | Spend > £3 AND conversions = 0 (7d) | PAID_MEDIA_BLEED is ACOS-based 30d, 2 records/1 SKU — not zero-conversion | `ppc_performance` (`record_type='ad'`, 7d) | **MISSING** |
| **L2** Shipping > 25% rev | shipping > 25% revenue (7d) | SHIPPING_HIGH exists, **same 25% threshold**, but 30-day NNR basis, 33 SKUs | `vw_fbm_uk_order_profitability` + `order_shipping_billing_detail` (7d) | **PARTIAL** |
| **L3** Net-neg + PPC>£5 | (rev×0.45)−ship−PPC<0 AND PPC>£5 (7d) | Net-negative detected (404) but not intersected with 7d PPC>£5; only 2/94 open SKUs have active PPC | `vw_fbm_uk_sku_daily_nnr` + `ppc_performance` (7d) | **PARTIAL** |
| **L4** Refund rate > 10% | refunded ÷ total > 10%, min 2 (30d) | RETURNS_ISSUE pattern defined but **0 records** | `order_transaction` (`order_status='Refunded'`, 30d) | **MISSING** |
| **L5** PH margin trend | declining ≥ 2 consecutive months (3mo) | SKU/30-day only; no monthly PH rollup or decline logic | `vw_fbm_uk_order_profitability` aggregated monthly by PH + `ppc_performance` | **MISSING** |

---

## Roll-up

| Verdict | Count | Analyses |
|---------|-------|----------|
| FULL | 0 | — |
| PARTIAL | 2 | L2, L3 |
| MISSING | 3 | L1, L4, L5 |

**Interpretation:** No analysis is fully delivered by the existing engine. Two are partially served (and are
the duplicate-truth hot spots). Three are absent. This is the evidence base for choosing Option B (extend):
reuse where PARTIAL, build where MISSING.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Map each protocol analysis to existing coverage with a FULL/PARTIAL/MISSING verdict |
| Business Question Supported | "Which of the 5 analyses already exist, and which must be built?" |
| Evidence Used | `PHASE2_RESULTS.md` (08–14); Phase 1 live L1/L4/L5 probes |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if every analysis has a verdict backed by a cited result |
| Next Step | Confirm each can actually be queried in `QUERYABILITY_CHECK.md` |
| Known Limitations | Verdicts reflect 2026-06-22 data; PARTIAL items depend on window-reconciliation decisions in the build |
