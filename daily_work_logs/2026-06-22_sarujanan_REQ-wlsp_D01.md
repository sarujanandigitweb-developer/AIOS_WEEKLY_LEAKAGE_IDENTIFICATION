# WLSP Daily Requirement Document
**File:** `2026-06-22_sarujanan_REQ-wlsp_D01.md` · (also referenceable as `WLSP_DAILY_REQUIREMENT_DOCUMENT.md`)
*Evidence-only. Every value below traces to a WLSP project file, a PostgreSQL finding, a report, a validation, or the work log. Items absent from source evidence are marked "Not specified in source evidence".*

---

# 1. Metadata Block

| Field | Value |
| ----- | ----- |
| daily_requirement_submitted_date | 2026-06-22 (Monday — execution date of D01; protocol PDF dated June 2026) |
| expected_deadline_date | Not specified as a date in source evidence. Protocol states "first execution the Monday following receipt"; management status estimates ≈8 working days for the OPTION B build after sign-off |
| end_user | Bietrick (TL) — Protocol Owner & Executor (PH team are downstream consumers) |
| expected_roi | £800–£1,500 per week of identifiable leakage prevented across the PH team (protocol §Purpose) |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | wlsp |
| phase | D01 — Documentation-First Investigation (Phase 1 + Phase 2 discovery → architecture decision) |
| requirement_id | DP-WLSP-REQ-01 |
| deliverable_id | D01 |
| blos_keys | L1: PPC spend > £3 AND conversions = 0 (7d) · L2: shipping > 25% of revenue (7d) · L3: (revenue × 0.45) − shipping − PPC < £0 AND PPC > £5 (7d) · L4: refund rate > 10%, min 2 orders (30d) · L5: net margin declining ≥ 2 consecutive months (3 mo) · Assumed: COGS 20%, Platform fee 15%, VAT 20% |
| domain | Leakage Stop-Loss — Amazon FBM — UK |

---

# 2. Today Requirement Block

## 2.1 Today Requirement

### Task Name
WLSP Documentation-First Investigation (D01): verify database support for the 5 leakage analyses, review existing assets, prevent duplicate truth, decide architecture, and persist the daily activity memory.

### Business Purpose
Determine — with evidence, no dashboard dependency — whether the live PostgreSQL database can execute all 5 weekly leakage analyses for UK Amazon FBM, and how the Weekly Leakage Protocol should be delivered **without creating a second competing source of truth** alongside the existing `development` leakage engine.

### Source Information

#### Source Systems
- Live PostgreSQL database (MCP connector, read-only discovery)
- Filesystem workspace `AIOS_Weekly_Leakage_Identification/`

#### Tables / Views Used
- `public.order_transaction`, `public.ppc_performance`, `public.ppc_etl_performance_data`, `public.order_shipping_billing_detail`, `public.amazon_returns`, `public.amz_order_expenses`
- `development.leakage_detection`, `development.leakage_classification`, `development.leakage_pattern_registry`
- Views: `development.vw_fbm_uk_order_profitability`, `development.vw_fbm_uk_sku_daily_nnr`, `development.vw_top_10_leakage`
- `staging_ai.fbm_sku_daily_nnr_snapshot`
- `daily_task.tbl_wlsp_sarujanan` (created + loaded this deliverable)

#### Documents Used
- `Bietrick_Weekly_Leakage_Protocol_v2.pdf`, `requirements/REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md`
- `discovery/PHASE1_EXISTING_ASSET_SCAN.md`, `discovery/SOURCE_OBJECT_INVENTORY.md`, `discovery/PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md`, `discovery/DUPLICATE_TRUTH_ASSESSMENT.md`
- `validation/COVERAGE_MATRIX.md`, `validation/QUERYABILITY_CHECK.md`, `validation/VALIDATION_RESULT.md`
- `architecture_review/OPTION_A/B/C_*.md`, `architecture_review/FINAL_ARCHITECTURE_DECISION.md`
- `VALIDATION_AUDIT.md`, `POSTGRES_DATA_GAP_ANALYSIS.md`, `HIGH_RISK_ROOT_CAUSE_ANALYSIS.md`, `ETL_TRACE_DQ1.md`
- `daily_work_logs/2026_06_22_wlsp_work_log.csv`

### Filter Conditions
- Scope: UK Amazon FBM — `source_name = 'AMAZON'`, `fba_sales = false`, `market_place = 'UK'`
- Accounts: LEDSone UK + DCVoltage UK (normalise `ss_name` variants via ILIKE)
- Analysis windows: 7 days (L1–L3), 30 days (L4), 3 full calendar months (L5)
- PPC grain: `ppc_performance.record_type = 'ad'` (ASIN in `ref_id`)

### Required Output

| Output | Purpose |
| ------ | ------- |
| Phase 1 + Phase 2 discovery docs | Establish existing assets and the existing leakage engine, with evidence |
| Coverage matrix (L1–L5) | Show which analyses are FULL / PARTIAL / MISSING vs the protocol |
| Data-gap analysis | Prove field-level readiness; confirm no analysis is blocked |
| Architecture decision (OPTION B) | Decide reuse-vs-extend-vs-rebuild without duplicate truth |
| Root-cause + ETL trace (DQ-1, DQ-2) | Explain the two HIGH data-quality findings |
| `daily_task.tbl_wlsp_sarujanan` + 10 activity rows | Persist the day's work as queryable activity memory |

---

# 3. Business Logic Block

### Purpose
Define how the collected database evidence is evaluated to answer "can the database support all 5 analyses, and which architecture is correct?"

### Rules (the 5 leakage analyses — BLOS keys)
- **L1** zero-conversion PPC: `SUM(spend) > £3 AND SUM(conversions) = 0` (7d) → PAUSE PPC
- **L2** shipping too high: `shipping_cost > 25% of revenue` (7d) → price / carrier / discontinue
- **L3** net-negative + PPC: `(revenue × 0.45) − shipping − PPC < £0 AND PPC > £5` (7d) → PAUSE PPC
- **L4** high refund: `refunded ÷ total > 10%`, min 2 orders (30d) → investigate
- **L5** margin decline: net margin declining ≥ 2 consecutive months (3 mo) → PH review

### Validation Conditions
- Each L1–L5 must be queryable from existing tables/views before any design.
- Every coverage verdict must cite a recorded query result.
- No fabricated facts; estimates labelled as estimates.
- No second competing source of truth for any leakage fact.

### PASS Criteria
- All 5 analyses supported with **no absent DB-required field** (COGS/fee/VAT are protocol-declared assumptions, not blockers).
- A single, evidence-traced architecture decision is recorded.

### FAIL Criteria
- Any protocol requirement blocked by missing data, OR architecture undecided, OR a finding unsupported by evidence.

---

# 4. Data Enrichment Block

### Source Systems
PostgreSQL `development` and `public` schemas (existing reusable assets for the OPTION B build).

### Tables
- `development.vw_fbm_uk_order_profitability` (joins `order_transaction` + `amz_order_expenses` + `order_shipping_billing_detail` + `amazon_returns`; uses ACTUAL Amazon fees + 20% COGS proxy)
- `development.vw_fbm_uk_sku_daily_nnr` (30-day SKU NNR rollup)
- `development.leakage_pattern_registry` (7 pattern classes used as report labels)
- `public.amazon_returns` (refund reason / £ enrichment for L4)

### Additional Data Required

| Field | Reason |
| ----- | ------ |
| `amz_order_expenses.charge_type / amount` | Actual Amazon referral/commission fees (better than the assumed 15%) for L2/L3/L5 |
| `order_shipping_billing_detail.carrier_charge` | Actual shipping cost (99.8% coverage on completed orders) for L2/L3/L5 |
| `amazon_returns.reason / refunded_amount` | Refund reason + revenue-at-risk enrichment for L4 (numerator correction) |
| `leakage_pattern_registry.pattern_class` | Classification labels (PAID_MEDIA_RUNAWAY→L1/L3, SHIPPING_HIGH→L2, RETURNS_ISSUE→L4) |
| External PPC ETL (DQ-1) | True `ppc_performance.user_name` (PH owner) — populator is external, not in DB/repo |

---

# 5. Evidence Block

### Documents Reviewed
Protocol PDF; REQ-001; PHASE1_EXISTING_ASSET_SCAN; SOURCE_OBJECT_INVENTORY; PHASE2_LEAKAGE_FRAMEWORK_REVIEW; DUPLICATE_TRUTH_ASSESSMENT; COVERAGE_MATRIX; QUERYABILITY_CHECK; VALIDATION_RESULT; OPTION_A/B/C; FINAL_ARCHITECTURE_DECISION; VALIDATION_AUDIT; POSTGRES_DATA_GAP_ANALYSIS; HIGH_RISK_ROOT_CAUSE_ANALYSIS; ETL_TRACE_DQ1.

### PostgreSQL Objects Reviewed
14 user schemas; core tables (`order_transaction` 1.22M, `ppc_performance` 24.5M, `order_shipping_billing_detail` 1.09M, `amazon_returns` 3,772, `amz_order_expenses` 412K); `development.leakage_detection` (404 OPEN/0 CLOSED), `leakage_classification` (343), `leakage_pattern_registry` (7); 3 `development` views; `daily_task` activity-memory tables; created `daily_task.tbl_wlsp_sarujanan`.

### Reports Created
PHASE1 + PHASE2 discovery set, DUPLICATE_TRUTH_ASSESSMENT, COVERAGE_MATRIX, QUERYABILITY_CHECK, VALIDATION_RESULT, OPTION A/B/C + FINAL_ARCHITECTURE_DECISION, VALIDATION_AUDIT, POSTGRES_DATA_GAP_ANALYSIS, HIGH_RISK_ROOT_CAUSE_ANALYSIS, ETL_TRACE_DQ1, the work-log CSV (10 rows), and this requirement document.

### Validation Evidence
- Database readiness: **GREEN/PASS** — 36 required fields, 23 full / 13 partial / **0 missing**; ≈82% readiness.
- Documentation audit: **PASS WITH WARNINGS** (no fabricated facts; 7 corrections C-1…C-7).
- Memory load: `tbl_wlsp_sarujanan` — 10 inserted / 0 updated / **0 duplicates**; PK `activity_id`.
- Live probes: L1 zero-conv flags returned; L2 shipping join 99.8%; L3 10 SKUs flagged; L4 31 ASINs flagged; L5 3 full months present.

---

# 6. Current Status Block

### Completed Items
Phase 1 & 2 discovery; duplicate-truth assessment; coverage matrix; data-gap analysis (PASS); root-cause of DQ-1/DQ-2; ETL trace DQ-1; OPTION B decision recorded; documentation audit (PASS w/ warnings); `tbl_wlsp_sarujanan` created, validated, and loaded with 10 D01 activities.

### Pending Items
Bietrick sign-off on OPTION B; apply corrections C-1…C-7; build L1/L4/L5 + wire L2/L3; weekly per-PH HTML report; closure loop write-back; DQ-1 external ETL fix; DQ-2 refund-source reconciliation view; `daily_loss_gbp` formula standardisation.

### Risks
- 🔴 OPTION B not yet signed off (blocks build).
- 🔴 DQ-1: 40.6% of PPC spend PH-unattributed; populator external/inaccessible.
- 🔴 DQ-2: refund sources disagree (order_transaction 50 vs amazon_returns FBM 303; refund_amount 42.1%).
- 🟡 `daily_loss_gbp` formula inconsistency; COGS/fee/VAT assumed (net directional).

### Next Actions
Secure OPTION B sign-off → apply C-1…C-7 → build L1 (ASIN-level) → L4 (order_transaction spine + returns enrichment) → L5 → wire L2/L3 → request external PPC-ETL access for DQ-1.

---

# 7. Queryability Block

- **Can another developer continue tomorrow without verbal explanation?** **YES.** `START_HERE.md` defines the reading order; every conclusion cites a SQL file + result file + source object; the architecture decision and pending build are written down; the day's activities are queryable in `daily_task.tbl_wlsp_sarujanan`.
- **What evidence supports this?** 23-file evidence-backed workspace + `evidence/postgres_queries/` + `evidence/query_results/`; VALIDATION_AUDIT confirms traceability (PASS WITH WARNINGS); 10 activity rows persisted with stable `activity_id` keys.
- **What information is still missing?** The external **PPC ETL code** that populates `ppc_performance.user_name` (DQ-1) — proven absent from DB and repo; and an explicit **deadline date** for the build (not specified in source evidence).

---

# 8. Final Assessment

### Requirement Coverage
D01 (investigation & decision): **complete** — all 5 analyses assessed (0 FULL / 2 PARTIAL / 3 MISSING vs protocol; all queryable today). Full protocol build: **not started** (correctly gated).

### Validation Coverage
Data-gap **PASS**; documentation audit **PASS WITH WARNINGS** (7 non-blocking corrections); memory load validated (0 duplicates).

### Queryability Coverage
**YES** for all measured facts (each maps to SQL + result + source object); **PARTIAL by design** for architecture judgements (reasoned over cited evidence).

### Duplicate Truth Risk
🟢 **GREEN** — no second source of truth created. The memory table is PK-`activity_id` dedup-safe; OPTION B explicitly routes the weekly protocol through one status of record rather than a competing list.

### Overall Status
> ✅ **PASS** — D01 deliverable is complete, evidence-traced, and persisted; the WLSP project is **ON TRACK, awaiting OPTION B sign-off** before the build phase.
