# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-06-23 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | DISCOVERY |
| requirement_id | REQ-01 |
| deliverable_id | D02 |
| status | COMPLETE |
| evidence_location | daily_task.tbl_wlsp_sarujanan (D02-A11..D02-A20) + daily_work_logs/2026_06_23_wlsp_work_log.csv |
| blos_keys_used | L1 spend>£3 & conv=0 (7d); L2 shipping>25% rev (7d); L3 (rev×0.45)−shipping−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 orders (30d); L5 net margin declining ≥2 consecutive months (3 mo); assumed COGS 20%, Platform fee 15%, VAT 20% |
| hardcoded_thresholds | YES — £3 PPC floor; 25% shipping ratio; 0.45 gross-margin factor; £5 PPC floor; 10% refund rate; minimum 2 orders; 2 consecutive months; COGS 20% / fee 15% / VAT 20%; CSV must have exactly 24 columns per row |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| BUSINESS_INTELLIGENCE \| LEAKAGE_ANALYSIS |

## File path (fill after saving):
# 2026-06-23__sarujanan__wlsp__REQ-01-D02.md

---

## 1. SYSTEM STATE

- Current system state at start of day: D01 investigation & decision phase was COMPLETE — workspace authored, OPTION B recorded (pending Bietrick sign-off), `daily_task.tbl_wlsp_sarujanan` created and loaded with the morning batch D01-A01..D01-A10 (10 rows).
- What was working: all D01 discovery/validation/analysis artifacts; the activity-memory table with `activity_id` PK.
- What was broken / missing: `VALIDATION_AUDIT` stood at **PASS WITH WARNINGS** with 7 open corrections (C-1..C-7); the L1–L5 calculation approach was not yet designed; whether the existing PH workflow could host the closure lifecycle was unverified; today's developer work was not yet captured to memory.
- Your starting point: close out D01 documentation quality, validate source data, design the calculations, verify the closure lifecycle, and persist today's activities — all read-only except the approved activity-log import.

---

## 2. WHAT CHANGED TODAY

- Change 1: Applied audit corrections **C-1..C-7** to existing files and re-graded `VALIDATION_AUDIT` from PASS WITH WARNINGS to **PASS**; produced `CORRECTION_SUMMARY.md`.
- Change 2: Authored the WLSP **Daily Requirement Document** (`2026-06-22_sarujanan_REQ-wlsp_D01.md`) and the **D01 daily SKILL.md** (`2026-06-22__sarujanan__wlsp__REQ-01-D01.md`).
- Change 3: Ran **source-data validation** of the four source tables and authored the **L1–L5 CALCULATION_DESIGN.md** (formulas, joins, windows, PH method, DQ risks, render-vs-store hybrid).
- Change 4: Performed the **closure-lifecycle capability audit** (development.actions + ph_action_board + staging_ai ph_action_* framework).
- Change 5: Generated, corrected (date→2026-06-23, ids→D02-A11..A20, deliverable→D02), and **imported the end-of-day activity log** D02-A11..D02-A20 into `daily_task.tbl_wlsp_sarujanan` via idempotent UPSERT (table now 20 rows).

Evidence reference (Git SHA / workflow export / file path): `AIOS_Weekly_Leakage_Identification/` (CORRECTION_SUMMARY.md, CALCULATION_DESIGN.md, VALIDATION_AUDIT.md re-grade) + `daily_work_logs/2026_06_23_wlsp_work_log.csv` + PostgreSQL `daily_task.tbl_wlsp_sarujanan` (D02-A11..A20). No git commits this session — deliverables are documents + DB rows.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

Table(s) involved: `daily_task.tbl_wlsp_sarujanan`; `public.ppc_performance`, `public.order_transaction`, `public.order_shipping_billing_detail`, `public.amazon_returns`; `development.leakage_detection / leakage_classification / actions`; `ph_action_board.ph_daily_actions`; `staging_ai.ph_action_lifecycle_v1 / ph_action_verification_v1 / ph_action_verification_schedule_v1 / ph_lifecycle_status_taxonomy_v1`.

Finding: (a) **Source-data validation** — all five analyses calculable directly from source; readiness ~85–95%; shipping coverage **99.6–99.7% on completed UK FBM** orders (not the raw 35.7% null); PPC PH attribution **40.5% null** (DQ-1); refund sources disagree (DQ-2) with `amazon_returns.refunded_amount` ~41% null. (b) **Population method** — leakage tables and the PH board are filled by an **external daily batch** (~08:00, dated `detection_run_id`); no in-DB trigger/function/`pg_cron`. (c) **Closure lifecycle** — already modelled: `development.actions` spine + `trg_enforce_evidence_on_close`, an **11-state status taxonomy** (incl. VERIFIED/CLOSED/PREVENTION_CONFIRMED), `ph_action_verification_v1`, and `ph_action_verification_schedule_v1` (82 rows, day 3/7/15/30/60 due dates). (d) **Import** — UPSERT inserted 10 rows; table now **20 rows, 0 duplicate activity_id**; D01-A01..A10 preserved.

SQL logic or pattern discovered: idempotent UPSERT `INSERT ... ON CONFLICT (activity_id) DO UPDATE SET ... imported_at=now()` with `RETURNING (xmax=0)` to count inserts vs updates. Shipping must be **de-duplicated per order_id** before any ASIN ratio. `ppc_performance` must be **window-scoped** (24M rows; unscoped scans time out).

Operational meaning (why does this schema exist?): the leakage tables are a **derived summary + lifecycle layer**, not a calculation source — WLSP computes L1–L5 from source and reuses the lifecycle/board for closure, keeping one status of record.

---

## 4. GAP FOUND

Gap description: (1) **CSV per-row defect** — generated row D02-A14 had **25 fields not 24** (a duplicated evidence value split `evidence_refs`); header-only validation missed it and the INSERT rejected the batch. (2) **DQ-1** PPC PH 40.5% null; (3) **DQ-2** refund-source conflict + ~41% null refund_amount; (4) leakage tables are **externally owned** — WLSP writes need a run_id/analysis_type convention agreed with the ETL owner.

Impact if unresolved: malformed CSV blocks import (hit today); L1 by-PH degraded; L4 revenue-at-risk weak; uncoordinated writes risk collision with the external batch.

Recommended action: add a **per-row column-count check (=24)** to CSV validation, not just the header; run L1 at ASIN level + SKU→PH fallback; use `order_transaction` as the single L4 rate source; coordinate run_id/analysis_type before any leakage-table write.

Owner (if known): WLSP build (sarujanan) for in-scope items; external PPC-ETL owner for DQ-1; Bietrick for OPTION B sign-off.

---

## 5. VALIDATION RULE ADDED OR CHANGED

Rule name / ID: WLSP-VAL-02 — CSV per-row column-count guard.
Condition checked: every data row of an import CSV must contain **exactly 24 fields** (`gsub(/","/) + 1 == 24`), checked per row, not only on the header.
What it prevents: a malformed row (e.g. a split `evidence_refs`) silently passing header validation and failing the PostgreSQL INSERT (`VALUES lists must all be the same length`).
Where implemented (file / node / function): pre-import CSV validation step for `daily_task.tbl_wlsp_sarujanan` loads.
BLOS reference (if applicable): NONE (data-quality guard).

Also reaffirmed: WLSP-VAL-01 — `activity_id` PK idempotent dedup (`ON CONFLICT (activity_id) DO UPDATE`); and the documentation rule that all C-1..C-7 audit findings must be closed before a clean PASS.

---

## 6. FAILURE MODE OR EDGE CASE

Failure scenario: a generated activity CSV row carries an extra column, so the multi-row INSERT fails with "VALUES lists must all be the same length".
How it is triggered: free-text fields (e.g. `evidence_refs`) accidentally split into two quoted fields during generation (D02-A14 had 25 fields).
How it is detected: per-row field count (`gsub(/","/)+1`) flags the row != 24 — header-only checks do NOT catch it.
Recovery procedure: merge the split fields back into one, re-validate all rows = 24, re-run the UPSERT (which is idempotent, so partial prior success is safe).
Risk level: MEDIUM

Secondary: storing leakage results in the activity-memory table would create duplicate truth — prevented by keeping streams separate (activity → daily_task; leakage → lifecycle). Risk MEDIUM.

---

## 7. DECISIONS MADE TODAY

Decision: Adopt the **hybrid render-and-persist** model for WLSP output, and **reuse the existing PH closure lifecycle** rather than build any new tracking/storage table.
Alternatives considered: pure on-demand (no storage); a new WLSP tracking/closure table.
Reason for choice: pure on-demand cannot support the protocol's following-Monday verification (no prior-week record); a new tracking table duplicates `development.actions` + the 11-state taxonomy + `ph_action_verification_v1` (duplicate truth). The existing lifecycle already provides PH-complete, evidence enforcement, TL verification, and day-N verification scheduling.
Trade-off accepted: WLSP must coordinate a run_id/analysis_type convention with the external ETL owner before writing into the shared leakage tables.
Who approved (if applicable): design decisions recorded; **OPTION B build remains gated on Bietrick sign-off** — no schema writes made.

---

## 8. COMPANY KNOWLEDGE EXTRACT

### Business Rule:
WLSP runs five weekly UK Amazon FBM leakage rules (L1 zero-conv PPC; L2 shipping>25%; L3 net-negative+PPC>£5; L4 refund>10%; L5 PH margin decline ≥2 months) and routes flagged items to PHs for same-week action and following-Monday verification.

### Operational Assumption:
The `development.leakage_*` tables are a **derived summary/lifecycle layer**, not a calculation source — they hold no PPC, raw revenue, raw shipping, or refund-count fields. All L1–L5 measures must come from the four source tables; COGS/fee/VAT remain assumed (20/15/20), so net is directional.

### Reusable Logic / Formula:
Idempotent activity-memory load: `INSERT ... ON CONFLICT (activity_id) DO UPDATE SET ..., imported_at=now()` with `RETURNING (xmax=0)` to split insert/update counts. CSV guard: `fields_per_row = gsub(/","/)+1 == 24`. Shipping de-dupe per `order_id` before ASIN ratios; PPC always window-scoped.

### Canonical Vocabulary:
WLSP; PH (Portfolio Holder); FBM; NNR; DQ-1 (PPC PH attribution gap); DQ-2 (refund-source conflict); OPTION B (extend existing framework); activity-memory table = `daily_task.tbl_<projectcode>_<developer>`; closure lifecycle states NEW→…→VERIFIED→CLOSED→PREVENTION_CONFIRMED.

### Cross-Project Applicability:
(1) The **per-row CSV column-count guard (=24)** applies to every daily_task activity-memory import across all developers/projects. (2) The **reuse-the-existing-PH-lifecycle** principle (one status of record via `development.actions` + `ph_action_*`) applies to any AIOS workflow that needs closure tracking — never build a parallel tracker.

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
> A developer with no context could **close out WLSP D02 — verify the 20 activity rows in `daily_task.tbl_wlsp_sarujanan`, apply the per-row CSV guard, and proceed to the OPTION B build (calculate L1–L5 from source, reuse the existing PH closure lifecycle) on Bietrick sign-off** using this file.

---

## — SUBMISSION CHECKLIST —

- [x] File named correctly: `2026-06-23__sarujanan__wlsp__REQ-01-D02.md`
- [x] All metadata fields filled
- [x] Sections 1–9 completed (or explicitly marked NONE)
- [x] No credentials, passwords, or API keys included
- [x] LLM Standard Check table completed
- [x] Three-AM Standard self-assessment written
- [x] Evidence location referenced

---
*DIGITWEB LK LTD — Daily Skill Increment System — v3.0 — May 2026*
