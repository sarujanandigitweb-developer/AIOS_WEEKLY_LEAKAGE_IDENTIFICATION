# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-06-22 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | DISCOVERY |
| requirement_id | DP-WLSP-REQ-01 |
| deliverable_id | D01 |
| status | COMPLETE |
| evidence_location | daily_task.tbl_wlsp_sarujanan + daily_work_logs/2026_06_22_wlsp_work_log.csv |
| blos_keys_used | L1 spend>£3 & conv=0 (7d); L2 shipping>25% rev (7d); L3 (rev×0.45)−shipping−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 orders (30d); L5 net margin declining ≥2 consecutive months (3 mo); assumed COGS 20%, Platform fee 15%, VAT 20% |
| hardcoded_thresholds | YES — £3 PPC floor; 25% shipping ratio; 0.45 gross-margin factor; £5 PPC floor; 10% refund rate; minimum 2 orders; 2 consecutive months; COGS 20% / fee 15% / VAT 20% assumptions |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| BUSINESS_INTELLIGENCE \| LEAKAGE_ANALYSIS |

## File path (fill after saving):
# 2026-06-22__sarujanan__wlsp__REQ-01-D01.md

---

## 1. SYSTEM STATE

- Current system state: Live PostgreSQL with an existing **daily SKU-level leakage engine** in the `development` schema (`leakage_detection` 404 rows = 404 OPEN / 0 CLOSED, `leakage_classification` 343, `leakage_pattern_registry` 7) plus 3 views (`vw_fbm_uk_order_profitability`, `vw_fbm_uk_sku_daily_nnr`, `vw_top_10_leakage`). No weekly PH-facing protocol, no WLSP workspace, and no WLSP activity-memory table existed at session start.
- What was working: Core tables populated and queryable — `order_transaction` (1.22M), `ppc_performance` (24.5M), `order_shipping_billing_detail` (1.09M), `amazon_returns` (3,772), `amz_order_expenses` (412K). The `development` views compute 30-day NNR using ACTUAL Amazon fees + 20% COGS proxy.
- What was broken / missing: Existing engine covers only L2/L3 partially; **L1, L4, L5 absent**; `leakage_detection.pattern_id` never populated (all NULL); **0 closures** (no feedback loop); `daily_loss_gbp` formula changed mid-series (06-15→06-16). Two HIGH data-quality issues: PPC PH-mapping 40.6% missing (DQ-1) and refund-source conflict (DQ-2).
- Your starting point: `Bietrick_Weekly_Leakage_Protocol_v2.pdf` + `REQ-001`; no investigation, no decision, no memory record yet.

---

## 2. WHAT CHANGED TODAY

- Change 1: Ran read-only Phase 1 + Phase 2 discovery across 14 schemas and the existing leakage engine; produced the discovery doc set (`PHASE1_EXISTING_ASSET_SCAN.md`, `SOURCE_OBJECT_INVENTORY.md`, `PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md`, `DUPLICATE_TRUTH_ASSESSMENT.md`) with recorded SQL + results under `evidence/`.
- Change 2: Produced validation + analysis reports: `COVERAGE_MATRIX.md` (0 FULL / 2 PARTIAL / 3 MISSING), `QUERYABILITY_CHECK.md`, `VALIDATION_RESULT.md`, `POSTGRES_DATA_GAP_ANALYSIS.md` (PASS, ≈82% readiness), `HIGH_RISK_ROOT_CAUSE_ANALYSIS.md` (DQ-1/DQ-2), `ETL_TRACE_DQ1.md`, `VALIDATION_AUDIT.md` (PASS WITH WARNINGS).
- Change 3: Recorded architecture decision **OPTION B** in `FINAL_ARCHITECTURE_DECISION.md` (extend the existing framework, do not rebuild).
- Change 4: Created `daily_task.tbl_wlsp_sarujanan` (26 cols, `activity_id` text PRIMARY KEY, `imported_at timestamptz DEFAULT now()`); generated and imported `2026_06_22_wlsp_work_log.csv` → 10 inserted / 0 updated / 0 duplicates.

Evidence reference (Git SHA / workflow export / file path): `AIOS_Weekly_Leakage_Identification/` (23 docs) + `daily_work_logs/2026_06_22_wlsp_work_log.csv` + PostgreSQL object `daily_task.tbl_wlsp_sarujanan`. No git commits this session — deliverables are documents + one DB table.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

Table(s) involved: `public.order_transaction`, `public.ppc_performance`, `public.ppc_etl_performance_data`, `public.order_shipping_billing_detail`, `public.amazon_returns`, `public.amz_order_expenses`; `development.leakage_detection / leakage_classification / leakage_pattern_registry`; `development.vw_fbm_uk_order_profitability / vw_fbm_uk_sku_daily_nnr / vw_top_10_leakage`; `daily_task.tbl_wlsp_sarujanan`.

Finding: Database is **GREEN/PASS** for all 5 analyses — 36 required fields, 23 full / 13 partial / **0 missing**. Live probes: L1 zero-conv flags returned; L2 shipping join **99.8%** on completed orders (corrects an earlier 73.5% measured over all statuses); L3 10 SKUs flagged; L4 31 ASINs flagged; L5 3 full months (Mar/Apr/May 2026, 24 PHs each).

SQL logic or pattern discovered: `ppc_performance.ref_id` = ASIN; `record_type='ad'` is the SKU grain. Refund rate must be self-consistent within `order_transaction` (`order_status='Refunded'` ÷ total). NNR is reusable via `vw_fbm_uk_order_profitability` (ACTUAL fees from `amz_order_expenses` Commission/DigitalServicesFee/RefundCommission + actual `carrier_charge` + 20% COGS proxy). Account names need ILIKE normalisation (`ledsone`/`led_sone`/`amazon Ledsone` → LEDSone; `dcvoltage`/`amazon Dcvoltage` → DCVoltage).

Operational meaning (why does this schema exist?): The `development` engine is an internal **daily 30-day SKU monitor**; the WLSP protocol is a **weekly 7-day PH-facing action layer**. They read the same base tables, so the protocol must reuse the engine's views and write back one status of record — not create a parallel list.

---

## 4. GAP FOUND

Gap description: (DQ-1) `ppc_performance.user_name` is 40.6% NULL on UK ad-rows — concentrated in 4 SKU-less accounts (`led_sone`, `electricalsone`, `so_926407`, `ledsonede`); raw `ppc_etl_performance_data` has no `user_name` column; only 11.3% recoverable via `order_transaction`. (DQ-2) Two refund sources disagree — `order_transaction` Refunded (50) vs `amazon_returns` FBM (303) over 30d; 242 returns still marked Completed; `refunded_amount` only 42.1% populated. Also: L1/L4/L5 not implemented; `shipping_template_price` only 21.2%; `daily_loss_gbp` formula inconsistent in existing engine.

Impact if unresolved: L1 by-PH grouping degraded (22.8% of flagged PPC spend = £124.61 of £545.38 unattributed); L4 refund rate unreliable without a reconciled numerator.

Recommended action: Run L1 at ASIN level now; build a SKU→PH derived view and fix PPC ETL (DQ-1). Use `order_transaction` as the L4 spine + `amazon_returns` (Approved, refunded_amount>0) as numerator enrichment (DQ-2). Standardise the `daily_loss_gbp` formula before reusing engine figures.

Owner (if known): WLSP build (sarujanan / OPTION B) for in-DB items; **external PPC-ETL owner** for the DQ-1 populator (code not in DB or repo — proven in `ETL_TRACE_DQ1.md`).

---

## 5. VALIDATION RULE ADDED OR CHANGED

Rule name / ID: WLSP-VAL-01 — Idempotent activity-memory dedup.
Condition checked: `activity_id` is PRIMARY KEY (NOT NULL + UNIQUE) on `daily_task.tbl_wlsp_sarujanan`; imports use `ON CONFLICT (activity_id) DO UPDATE` (updating only activity_summary, evidence_refs, gap_or_risk, next_action, status, imported_at).
What it prevents: Duplicate activity rows / duplicate memory truth on re-import.
Where implemented (file / node / function): `daily_task.tbl_wlsp_sarujanan` PK constraint; validated via V1–V5 (PK=activity_id, 26=26 column parity, 0 duplicates).
BLOS reference (if applicable): NONE (governance rule, not a BLOS key).

Additional documentation-validation rules enforced this session: every L1–L5 coverage verdict must cite a recorded query result; no fabricated facts (estimates labelled as estimates); no second competing source of truth per leakage fact.

---

## 6. FAILURE MODE OR EDGE CASE

Failure scenario: A separate WLSP system (OPTION C) issues a second flagged-ASIN list for L2/L3 alongside the existing 148 SHIPPING_HIGH + 404 net-negative detections → conflicting instructions and two closure states for one ASIN.
How it is triggered: Building the weekly protocol independently of `development.leakage_detection` instead of extending it.
How it is detected: An ASIN appears with different status in the weekly report vs the existing engine.
Recovery procedure: OPTION B routes the protocol through the existing views + one status of record; write closures back to `leakage_detection.status`.
Risk level: MEDIUM

Secondary edge cases (evidenced): `daily_loss_gbp` formula inconsistency (max loss 0.18→11.58→50.08 across runs) — do not reuse engine loss figures until standardised (MEDIUM); PPC spend with no PH owner falls into an UNATTRIBUTED bucket rather than a PH (HIGH for L1 accountability).

---

## 7. DECISIONS MADE TODAY

Decision: Adopt **OPTION B** — build the weekly report layer on top of the existing `development` leakage framework.
Alternatives considered: OPTION A (reuse engine as-is); OPTION C (separate standalone system).
Reason for choice: A cannot deliver L1/L4/L5 (RETURNS_ISSUE has 0 rows; PAID_MEDIA_BLEED is ACOS-based not zero-conversion; no monthly PH rollup) and uses 30-day not 7-day windows. C guarantees duplicate truth on L2/L3 and re-derives an inferior cost model. B reuses the more-accurate `vw_fbm_uk_order_profitability` (actual fees) + the pattern taxonomy, adds the 3 missing analyses + the closure loop, and keeps one status of record.
Trade-off accepted: B needs new query logic for L1/L4/L5 + an HTML report and must reconcile 7d-vs-30d windows; it also inherits the engine's `daily_loss_gbp` formula issue (to be standardised first).
Who approved (if applicable): Decision RECORDED — **pending Bietrick (TL) sign-off** before any build.

---

## 8. COMPANY KNOWLEDGE EXTRACT

### Business Rule:
Weekly UK Amazon FBM leakage is detected by five rules and acted on per PH: **L1** pause PPC when spend > £3 with 0 conversions (7d); **L2** fix price/carrier/discontinue when shipping > 25% of revenue (7d); **L3** pause PPC when (revenue × 0.45) − shipping − PPC < £0 and PPC > £5 (7d); **L4** investigate when refund rate > 10% with ≥2 orders (30d); **L5** review any PH whose net margin declines ≥2 consecutive months (3 mo). Each week not executed leaves an estimated £800–£1,500 of identifiable leakage unchecked.

### Operational Assumption:
COGS (20%), Platform fee (15%) and VAT (20%) are **assumed** — absolute net carries a margin of error, but relative comparisons between PHs/ASINs remain directionally accurate ("an ASIN losing money on assumed rates is almost certainly losing money on actual rates"). Shipping is near-complete (99.8%) on **completed** orders only; PH attribution is incomplete in PPC (40.6% missing).

### Reusable Logic / Formula:
NNR per order = revenue − amazon_fees − refund − return_cost − postage − (0.20 × revenue), from `development.vw_fbm_uk_order_profitability`; 30-day rollup in `vw_fbm_uk_sku_daily_nnr`. Refund rate (L4) = `COUNT(order_status='Refunded') ÷ COUNT(*)` within `order_transaction`, with `amazon_returns` (Approved, refunded_amount>0) as numerator enrichment. Activity-memory dedup = `activity_id` PK + `ON CONFLICT DO UPDATE`.

### Canonical Vocabulary:
PH = Portfolio Holder; FBM = Fulfilled By Merchant; NNR = Net Normalised Revenue; BLOS = business-logic threshold key; WLSP = Weekly Leakage Stop-loss Protocol; L1–L5 = the five analyses; accounts = LEDSone UK / DCVoltage UK; `ref_id` = ASIN in `ppc_performance`; `record_type='ad'` = SKU grain; activity-memory table naming = `daily_task.tbl_<projectcode>_<developer>`.

### Cross-Project Applicability:
(1) The **Mini-AIOS investigation workspace template** (requirements/discovery/evidence/architecture_review/validation/closure + per-file document-control block) is reusable for any AIOS investigation. (2) The **per-developer/project activity-memory table** (`activity_id` PK, 24-field standard, idempotent UPSERT) is the company standard for daily knowledge capture and is reusable across all developers/projects.

---

## 9. LLM STANDARD CHECK

| Check | YES / NO |
|---|---|
| Could an unknown developer continue from this file without reading source code? | YES |
| Is every business threshold visible (not buried in code)? | YES |
| Is the GAP section completed or marked NONE? | YES |
| Is the COMPANY KNOWLEDGE EXTRACT section substantive? | YES |
| Are evidence locations referenced? | YES |
| Is metadata complete? | YES |
| Is this extracting knowledge — not just logging activity? | YES |

**Three-AM Standard self-assessment:**
> A developer with no context could **resume the WLSP build tomorrow — execute OPTION B, implement L1/L4/L5, reuse the existing `development` views, and avoid duplicate truth — and verify today's 10 activities in `daily_task.tbl_wlsp_sarujanan`** using this file.

---

## — SUBMISSION CHECKLIST —

- [x] File named correctly: `2026-06-22__sarujanan__wlsp__REQ-01-D01.md`
- [x] All metadata fields filled
- [x] Sections 1–9 completed (or explicitly marked NONE)
- [x] No credentials, passwords, or API keys included
- [x] LLM Standard Check table completed
- [x] Three-AM Standard self-assessment written
- [x] Evidence location referenced

---
*DIGITWEB LK LTD — Daily Skill Increment System — v3.0 — May 2026*
