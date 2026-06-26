# WLSP Daily Requirement Document — D03
**File:** `2026-06-24_sarujanan_REQ-wlsp_D03.md`
*Evidence-only. Every value traces to a WLSP project file, a live PostgreSQL/MCP finding, or the work log.*

---

# 1. Metadata Block

| Field | Value |
| ----- | ----- |
| daily_requirement_submitted_date | 2026-06-24 |
| expected_deadline_date | 2026-06-24 (same-day dashboard build) |
| end_user | Bietrick (TL) — Protocol Owner; PH team are downstream consumers |
| expected_roi | £800–£1,500 per week of identifiable leakage prevented (protocol §Purpose) |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | wlsp |
| phase | D03 — Build (live dashboard generation from source + executive UI) |
| requirement_id | DP-WLSP-REQ-01 |
| deliverable_id | D03 |
| blos_keys | L1 spend>£3 & conv=0 (7d); L2 shipping>25% (7d); L3 (rev×0.45)−ship−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 (30d); L5 margin declining ≥2 months (3 mo) |
| domain | Leakage Stop-Loss — Amazon FBM — UK |

---

# 2. Today Requirement Block

## 2.1 Requirement
Generate the WLSP weekly-leakage dashboard from **live** source data via MCP, deliver it as a display-only two-file artifact (`index.html` + `data.js`), refactor it to a management-ready UI, and persist today's developer work to activity memory — without storing any leakage results in the database.

## 2.2 Business Objective
Give Bietrick a same-day, professional view of the five leakage analyses (per PH and account) that always reflects current source data, with PostgreSQL as the single source of truth and no duplicate leakage storage.

## 2.3 Data Sources (source tables only)
- `public.ppc_performance` (L1, L3, L5 PPC)
- `public.order_transaction` (revenue, refunds, PH/account)
- `public.order_shipping_billing_detail` (carrier_charge)
- `public.amazon_returns` (refund enrichment)
- Excluded from calculation: `development.leakage_detection`, `development.leakage_classification`, `ph_action_board.ph_daily_actions`
- Activity memory: `daily_task.tbl_wlsp_sarujanan`

## 2.4 Validation Requirements
- Re-validate source (row counts, date coverage, key-null %) before generating data.
- L1–L5 computed only from source; shipping de-duped per `order_id`; PPC window-scoped.
- Dashboard counts must equal: **L1=144, L2=214, L3=15, L4=31, L5=9**.
- `index.html` must contain no DB/MCP/SQL/calculation; reads only `data.js`.
- CSV exactly 24 columns per row; `activity_id` continues from `D02-A20` → `D03-A21`.

## 2.5 Current Status
-  Source re-validated live (2026-06-24).
-  L1–L5 executed from source; `data.js` generated with real values.
-  Display-only `index.html` built, frontend-validated, and refactored to executive UI.
-  Activity memory prepared (D03-A21..A27 CSV) — **import pending approval**.

## 2.6 Evidence
Live MCP validation + L1–L5 results (2026-06-24); `dashboard/data.js`; `dashboard/index.html`; Node binding-replay (counts 144/214/15/31/9, 0 JS errors); table validation (20 rows, max `D02-A20`, 26-col activity-memory schema).

## 2.7 Expected Output
1. `dashboard/index.html` + `dashboard/data.js` (display-only, real data).
2. `2026-06-24__sarujanan__wlsp__REQ-01-D03.md` (SKILL).
3. `2026_06_24_wlsp_work_log.csv` (D03-A21..A27 activity memory).
4. MCP import plan (idempotent UPSERT) — executed only after approval.
