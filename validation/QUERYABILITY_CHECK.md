# Queryability Check

**Principle applied:** Queryability First — confirm each analysis can actually be queried from live data
before designing on top of it.
**Date:** 2026-06-22 · **Method:** ran a representative query for each analysis and observed real rows.

---

| Analysis | Queryable today? | Proof observed (live) | Required objects present? |
|----------|------------------|------------------------|---------------------------|
| **L1** Zero-conv PPC | ✅ YES | Returned real flags, e.g. SKU `PLADBM+LSDO210BG3PK+ICST64E273PK` / B09YYSLDWP / Theepana — £17.84 spend, 0 conv | `ppc_performance` (spend, orders, clicks, impressions, ref_id, user_name, ss_name, date) ✅ |
| **L2** Shipping > 25% | ✅ YES | SHIPPING_HIGH classifications show live ratios (78.3%, 58.2%); join `order_transaction`↔`order_shipping_billing_detail` resolves at 73.5% | revenue + carrier_charge + identifiers ✅ (template price weak, 3.7%) |
| **L3** Net-neg + PPC | ✅ YES | `vw_fbm_uk_sku_daily_nnr` returns nnr_30d; `ppc_performance` returns 7d spend; intersection runs | NNR view + PPC table ✅ |
| **L4** Refund rate | ✅ YES | Returned real flags, e.g. B0DHGM5NP4 / utharsika — 2 orders, 1 refunded = 50% | `order_transaction` (order_status='Refunded') ✅ |
| **L5** PH margin trend | ✅ YES | Returned 3-month monthly revenue + shipping per PH (Abinayaa, Dilani, …) | `order_transaction` + shipping + `ppc_performance`, monthly group ✅ |

---

## Data-quality caveats surfaced (do not block, but flag in output)

| Caveat | Measure | Affected |
|--------|---------|----------|
| Shipping join coverage | 73.5% (26.5% orders no carrier_charge) | L2, L3, L5 |
| PH mapping | 83.4% (16.6% unattributed) | all |
| `shipping_template_price` | 3.7% populated | L2/L3/L5 "additional template" near-zero |
| COGS/fee/VAT | assumed 20/15/20 | L3, L5 absolute net directional only |
| `ss_name` variants | 8 spellings | normalise via ILIKE |

---

## Verdict

**All five analyses are queryable from existing live data today.** No analysis is blocked by absent data. The
caveats are disclosure items for the weekly report, not blockers.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Prove each analysis can be executed against live data before any build |
| Business Question Supported | "Can we actually query L1–L5 right now?" |
| Evidence Used | Phase 1 live L1/L4/L5 probes; `PHASE2_RESULTS.md` 12; coverage queries 04/05 |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if every analysis returns real rows from live data → passes (5/5) |
| Next Step | Roll up into `VALIDATION_RESULT.md` |
| Known Limitations | Probes were representative samples, not full production runs; caveats above persist |
