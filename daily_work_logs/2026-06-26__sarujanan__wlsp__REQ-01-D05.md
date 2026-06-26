# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-06-26 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | HARDENING / REVIEW |
| requirement_id | REQ-01 |
| deliverable_id | D05 |
| status | COMPLETE |
| evidence_location | daily_task.tbl_wlsp_sarujanan (D05-A35..D05-A37) + daily_work_logs/2026_06_26_wlsp_work_log.csv |
| blos_keys_used | L1 spend>£3 & conv=0 (7d); L2 shipping>25% rev (7d); L3 (rev×0.45)−shipping−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 orders (30d); L5 net margin declining ≥2 consecutive months (3 mo); assumed COGS 20%, Platform fee 15%, VAT 20% |
| hardcoded_thresholds | YES — £3/25%/0.45/£5/10%/2 orders/2 months; COGS 20% / fee 15% / VAT 20%; sidebar counts derived live from l1-l4 rows (viewMatch); L5 global; CSV 24 columns/row |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| BUSINESS_INTELLIGENCE \| LEAKAGE_ANALYSIS \| DASHBOARD |

## File path (fill after saving):
# 2026-06-26__sarujanan__wlsp__REQ-01-D05.md

---

## 1. SYSTEM STATE

- Start of day: D04 COMPLETE (table 34 rows, D01-A01..D04-A34). The dashboard refresh pipeline (dashboard_refresh_prompt.md + refresh_dashboard.py) was in place with Amazon-only + distinct-ASIN + UNATTRIBUTED-exclusion fixes and regression guards. Multiple divergent dashboard JS lineages existed (summary-driven vs row-driven).
- What was working: the refresh SQL/business logic (Amazon-only filters, distinct rules, L5 global); the orchestrator launch+validate+log flow.
- What was broken / unclear: which dashboard JS design is canonical; an account-rail count colour was unreadable on the selected (blue) row; whether Margin Trend should react to the account filter.
- Starting point: review the refresh workflow, lock the final dashboard design, and fix the count-colour defect.

---

## 2. WHAT CHANGED TODAY

- Performed a read-only architectural **review** of the refresh workflow (leakage_dashboard.html + dashboard_refresh_prompt.md + refresh_dashboard.py).
- **Locked the final dashboard sidebar-count design**: counts are derived live from the l1-l4 detail rows via `viewMatch` (account AND PH filter); All accounts = LEDSone + DCVoltage; L5 (Margin Trend) is global/per-PH and excluded from flagged totals; **no account_breakdown** (explicit decision — the rows already carry account+ph, so per-account PH counts come from filtering the rows).
- Verified **Margin Trend (L5) is correctly account-independent** (renderL5 filters by PH/search only, not account) — confirmed by-design, not a bug.
- **Fixed the account-rail selected-count colour** (CSS specificity) in leakage_dashboard.html and index.html.

Evidence reference: file mtimes 2026-06-26 (leakage_dashboard.html 16:07, index.html 13:53); CSS rule `.acct-opt.on .ao-ct.oth{color:#fff}` present; `countFor=rowsFor(k).filter(viewMatch).length`; current embedded counts 125/212/17/33/9. No git repo — deliverables are files + DB rows.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

Table(s): `daily_task.tbl_wlsp_sarujanan`; source `public.ppc_performance`, `public.order_transaction`, `public.order_shipping_billing_detail`, `public.amazon_returns`.

Finding: read-only MCP confirmed the activity table at 34 rows (max D04-A34, no 2026-06-26 rows) → today is deliverable D05 (D05-A35..A37). The refresh prompt's SQL is correct (Amazon-only on all PPC, COUNT(DISTINCT asin) for summary.counts, L5 global, UNATTRIBUTED excluded). No DB writes other than today's activity-memory import.

SQL/architecture pattern: the production dashboard **counts live from the embedded l1-l4 rows** rather than from summary.counts/account_summary/ph_summary; this guarantees All == LEDSone + DCVoltage and PH→account roll-up, and makes account_breakdown unnecessary. Displayed KPI = flagged-row count for the current view.

Operational meaning: summary.counts/account_summary/ph_summary are still generated (and useful as evidence/rosters) but are not the counting source in this design; the rows are.

---

## 4. GAP FOUND

Gap description: (1) **CSS specificity** — `.acct-opt .ao-ct.oth{color:var(--muted)}` (0,3,0) overrode `.acct-opt.on .ao-ct{color:#fff}` (0,3,0) by source order, so the count on the selected (blue) account row rendered muted-grey and unreadable. (2) **Refresh-prompt cap vs row-counting** — the prompt caps l1/l2 to top-60; because the cards count embedded rows, the KPI shows ≤60, not the true total (acceptable if the card means "rows shown"; embed full if it must mean the true total). (3) **refresh_dashboard.py** validates the data block but does not verify the non-data HTML/CSS/JS is byte-for-byte unchanged.

Impact if unresolved: unreadable selected-row count (UX); KPI under-display if true totals are expected; risk that an automated refresh silently alters non-data HTML.

Recommended action: (1) raise selected-state count rule to 4-class specificity → white (DONE). (2) decide card meaning; if true totals, embed l1/l2 full in the prompt (NOT changed — pending decision). (3) add a byte-for-byte non-data guard + atomic write/backup to refresh_dashboard.py (recommended, NOT changed).

Owner: WLSP build (sarujanan). Reviewer/TL: Bietrick.

---

## 5. VALIDATION RULE ADDED OR CHANGED

- **WLSP-VAL-07** — selected-state sidebar count must remain readable: `.acct-opt.on .ao-ct[,.led,.dcv,.oth]{color:#fff}` must out-specify the colour-variant rules (4 classes > 3).
- Reaffirmed: sidebar counts derive from l1-l4 rows (All == LEDSone + DCVoltage); L5 global and excluded from flagged totals; refresh replaces ONLY the dashboardData marker block; Amazon-only + distinct-ASIN + UNATTRIBUTED-exclusion in the prompt.

---

## 6. FAILURE MODE OR EDGE CASE

Failure scenario: a selected sidebar row shows its count in a low-contrast colour because a later, equal-specificity CSS rule re-colours it.
How triggered: colour-variant class (.led/.dcv/.oth) on the count badge ties the `.on` white rule and wins by source order.
How detected: visual review of the selected (blue) row; the count was muted-grey.
Recovery: give the selected-state rule higher specificity (add the variant classes) so white wins; no JS/data change.
Risk level: LOW (presentation only).

---

## 7. REVIEW OUTCOME (refresh workflow)

- leakage_dashboard.html — single WLSP_DATA_START/END block; HTML/CSS/JS complete; only dashboardData should change on refresh. ✅
- dashboard_refresh_prompt.md — SQL/business logic correct (Amazon-only, distinct, L5 global, UNATTRIBUTED excluded, no breakdown); one open item: l1/l2 top-60 cap vs row-counting cards. ⚠ (decision pending; not changed today)
- refresh_dashboard.py — validates JSON/keys/counts/forbidden tables/marketplace guards; missing byte-for-byte non-data preservation + atomic write. ⚠ (recommended; not changed today)

---

## 8. NEXT STEP

- Decide KPI card meaning: true total (embed l1/l2 full in the prompt) vs rows-shown (keep cap). Apply the one-line prompt change if true totals are required.
- Add to refresh_dashboard.py: byte-for-byte non-data guard + atomic write/backup + retry.
- Obtain Bietrick sign-off; run the first scheduled refresh on the cron host.

---

## 9. EVIDENCE / IMPORT

- Files changed today: `dashboard/leakage_dashboard.html`, `dashboard/index.html` (CSS count-colour fix). Reviewed read-only: `dashboard/dashboard_refresh_prompt.md`, `dashboard/refresh_dashboard.py`.
- Work log: `daily_work_logs/2026_06_26_wlsp_work_log.csv` (3 rows, D05-A35..A37, 24 columns each).
- Activity memory: `daily_task.tbl_wlsp_sarujanan` rows D05-A35..D05-A37 (idempotent UPSERT, activity_date 2026-06-26).
- Companion requirement doc (user-authored): `daily_work_logs/2026-06-26_sarujanan_REQ-wlsp_REQ-04-D01.md`.
