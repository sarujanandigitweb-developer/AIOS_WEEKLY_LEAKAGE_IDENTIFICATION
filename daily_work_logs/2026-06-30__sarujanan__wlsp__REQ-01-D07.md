# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-06-30 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | PRODUCTION / PUBLICATION (automation + dashboard upload) |
| requirement_id | REQ-01 |
| deliverable_id | D07 |
| status | COMPLETE |
| evidence_location | daily_task.tbl_wlsp_sarujanan (D07-A45..D07-A51) + daily_work_logs/2026_06_30_wlsp_work_log.csv |
| blos_keys_used | L1 spend>£3 & conv=0 (7d); L2 shipping>25% rev (7d); L3 (rev×0.45)−shipping−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 orders (30d); L5 net margin declining ≥2 consecutive months (3 mo); reporting window = previous Mon–Sun via `date_trunc('week',CURRENT_DATE)` |
| hardcoded_thresholds | YES — £3/25%/0.45/£5/10%/2 orders/2 months; report_date = previous Sunday (header Start=report_date−6, End=report_date); accent rgba(79,156,249) literal replaces color-mix; PH dashboards = master shell + per-PH data block |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| BUSINESS_INTELLIGENCE \| LEAKAGE_ANALYSIS \| DASHBOARD \| AUTOMATION |

## File path (fill after saving):
# 2026-06-30__sarujanan__wlsp__REQ-01-D07.md

---

## 1. SYSTEM STATE

- Start of day: D06 COMPLETE (table 44 rows, D01-A01..D06-A44). leakage_dashboard.html held validated live data (Mon–Sun window, account-aware L5); refresh_dashboard.py launched+validated the master only; 24 per-PH dashboards existed but as static snapshots cloned before the latest master edits; tech_team_outputs.ph_task had no WLSP row.
- What was working: the master refresh orchestration (PostgreSQL → master → validate → PASS); the Amazon-only / UNATTRIBUTED-exclusion business logic; the Mon–Sun window.
- What was broken / unclear: master defaulted to dark and single-PH dashboards showed a redundant "All Portfolio Holders" entry; CSS used color-mix() and scrollbar-width (browser-compat warnings for deploy); per-PH dashboards were not part of the automated refresh; no DB row for the dashboard in ph_task; whether the 232 KB HTML could be uploaded via MCP.
- Starting point: finish production-readiness — theme/UX + deploy-safe CSS, fold per-PH generation into the refresh, prove the end-to-end automated workflow, and publish the dashboard into tech_team_outputs.ph_task.

---

## 2. WHAT CHANGED TODAY

- **Light theme default + single-PH sidebar fix**: set the master root to Light Mode (html data-theme=light, initTheme fallback light, toggle label Light); added a renderPhRail guard so "All Portfolio Holders" only renders when >1 PH (single-PH files show the lone holder selected). Regenerated all 24 PH dashboards; JS identical, only dashboardData differs.
- **Deploy-safe CSS**: replaced color-mix(in srgb,var(--accent) X%,transparent) with the exact rgba(79,156,249,.X) (accent is always blue) and replaced Firefox-only scrollbar-width/scrollbar-color with ::-webkit-scrollbar rules — across master, index.html and all 24 PH files. Zero flagged properties remain across 26 HTML files; visuals unchanged.
- **Automated per-PH generation**: extended refresh_dashboard.py with build_ph_data() + generate_ph_dashboards() so each refresh reuses the SAME dashboardData (no extra SQL, no duplicated logic/rendering) to regenerate every PH dashboard by swapping only the marker block, with per-PH validation (shell byte-identical + PH-isolated) and total-time logging.
- **End-to-end refresh PASS**: ran the full pipeline (PostgreSQL → master → 24 PH dashboards → validation → PASS) in 477.4s; verified the window auto-resolved to Mon 2026-06-22 → Sun 2026-06-28 (run on a Tuesday); counts L1 147 / L2 270 / L3 45 / L4 40 / L5 10; L1 = COUNT(DISTINCT ASIN); no UNATTRIBUTED in ph_summary.
- **ph_task publication workflow**: reviewed the ph_task schema + prior rows, validated the HTML (16 checks PASS), prepared the row, and inserted the metadata row (id 8); TL added task_id WLSP_Bietrick_Leakage_Dashboard-V1. Diagnosed that html_content (232 KB) cannot be loaded from this env and prepared a TL upload strategy with verification.

Evidence reference: refresh.log RESULT PASS 2026-06-30 11:57:50; ph_task id 8; source sha256 d07f8d54, md5 6d689e06, 237665 bytes.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

Table(s): `daily_task.tbl_wlsp_sarujanan` (activity memory); `tech_team_outputs.ph_task` (hosted-tool task feed); source `public.ppc_performance`, `public.order_transaction`, `public.order_shipping_billing_detail`, `public.amazon_returns`.

Finding: review confirmed the activity table at 44 rows (max D06-A44) → today is **D07** (D07-A45..A51, INSERT ON CONFLICT DO NOTHING). ph_task review: it is the task feed where developers publish HTML in html_content; lifecycle created → viewed → acted; completion implicit (action_took_by NULL = pending); project_code non-unique; version_level increments per project (first WLSP row → 1). The target DB (`project_db` @ pg.severdigitweb.uk) is reachable ONLY via the claude_ai_postgres MCP connector.

SQL/architecture pattern: **generate dashboardData once, fan out per-entity files** by replacing only the marker block — no per-PH SQL. **Publish workflow**: validate artifact → row preview → approve → insert metadata → load large html_content separately.

Operational meaning: large binary/text artifacts (>~28 KB) cannot transit the MCP from this build box; they must be loaded from a host that resolves the DB, then verified by byte count + md5/sha256.

---

## 4. GAP FOUND

Gap description: (1) **Single-PH UX** — every per-PH dashboard showed a redundant "All Portfolio Holders" and defaulted to dark. (2) **Browser-compat CSS** — color-mix() (Chrome <111) and scrollbar-width (Chrome <121/Safari/Samsung) tripped Edge Tools compat warnings for deploy. (3) **Per-PH not automated** — PH dashboards were static, drifting from the master. (4) **Large-HTML upload** — the 232 KB html_content cannot be written via MCP from here: host NXDOMAIN on system + public DNS, MCP is SQL-only, and the harness strips large output from context so chunked SQL is not byte-safe.

Impact if unresolved: stale/dark per-PH dashboards; deploy lint warnings; PH dashboards diverge from the validated master each refresh; the published dashboard row has no renderable HTML.

Recommended action: (1) Light default + renderPhRail row-count guard (DONE). (2) rgba literal + ::-webkit-scrollbar (DONE). (3) build_ph_data/generate_ph_dashboards in refresh_dashboard.py (DONE). (4) hand the upload to the TL via a psycopg2 one-liner that reads the file into a bound parameter, then verify md5 6d689e06 + 237665 bytes (PREPARED).

Owner: WLSP build (sarujanan). Reviewer/TL: Bietrick.

---

## 5. VALIDATION RULE ADDED OR CHANGED

- **WLSP-VAL-11** — every per-PH dashboard MUST be byte-identical to the master outside the `WLSP_DATA_START/END` markers and isolated to its own PH (ph_summary length 1; all l1–l5 rows that PH); only dashboardData differs.
- **WLSP-VAL-12** — per-PH generation MUST reuse the single master dashboardData and issue ZERO PostgreSQL queries (no duplicate SQL / business logic / rendering); the refresh fails if any PH file drifts or is not PH-isolated.
- **WLSP-VAL-13** — deployed dashboard HTML MUST contain no `color-mix()`, `scrollbar-width`, or `scrollbar-color`; accent tints use the rgba literal and scrollbars use `::-webkit-scrollbar`.
- **WLSP-VAL-14** — a ph_task row is PASS only when stored `html_content` matches the source file by byte count AND md5/sha256; insert metadata first, load html_content separately, then read back to verify.

---

## 6. FAILURE MODE OR EDGE CASE

Failure scenario: a large validated HTML artifact cannot be persisted into the remote DB from the build environment.
How triggered: attempting to UPDATE html_content (232 KB) via MCP execute_sql; direct psql/psycopg2 fails because the host does not resolve.
How detected: NXDOMAIN for pg.severdigitweb.uk on the system resolver and on 8.8.8.8/1.1.1.1 (while outbound to 8.8.8.8:53 succeeds); Bash output >~28 KB is persisted to a file and stripped from context, so chunked SQL cannot be assembled byte-safely.
Recovery: insert metadata via MCP; load html_content from a host that resolves the DB (TL machine / MCP host) by reading the file into a bound parameter; verify by octet_length + md5; report PASS only on exact match.
Risk level: MEDIUM (publication blocked until the external loader runs; no data corruption).

---

## 7. REVIEW OUTCOME (production + publication)

- leakage_dashboard.html — Light default; single-PH guard; rgba + webkit scrollbars; refresh validator PASS. ✅
- dashboard/portfolio_holders/*_leakage.html (24) — regenerated from master; 0 shell drift; PH-isolated. ✅
- index.html — CSS browser-compat fixes applied. ✅
- refresh_dashboard.py — per-PH generation integrated (build_ph_data/generate_ph_dashboards); per-PH validation + total-time log; end-to-end PASS 477.4s. ✅
- tech_team_outputs.ph_task — metadata row id 8 inserted (released, version 1); html_content load handed to TL with verification (PENDING external loader). ⏳

---

## 8. NEXT STEP

- TL runs the psycopg2 loader to populate ph_task id 8 html_content from leakage_dashboard.html, then read back and confirm 237665 bytes / md5 6d689e06.
- Schedule the first Monday cron run of refresh_dashboard.py (master + 24 PH dashboards) end to end.
- Optionally store explicit data_start/data_end in summary and add an atomic byte-for-byte non-data guard on the master shell.

---

## 9. EVIDENCE / IMPORT

- Files changed today: `dashboard/leakage_dashboard.html` (theme default + renderPhRail guard + CSS compat), `dashboard/index.html` (CSS compat), `dashboard/refresh_dashboard.py` (per-PH generation + validation + timing), `dashboard/portfolio_holders/*_leakage.html` (24 regenerated).
- Work log: `daily_work_logs/2026_06_30_wlsp_work_log.csv` (7 rows, D07-A45..A51, 24 columns each).
- Activity memory: `daily_task.tbl_wlsp_sarujanan` rows D07-A45..D07-A51 (INSERT ON CONFLICT DO NOTHING, activity_date 2026-06-30) — table now 51 rows.
- Database publication: `tech_team_outputs.ph_task` row id 8 (wlsp / WLSP_Bietrick_Leakage_Dashboard-V1; released; html_content pending external load).
- Supporting evidence: refresh.log `RESULT: PASS` 2026-06-30 11:57:50; counts 147/270/45/40/10; window 2026-06-22 → 2026-06-28; source sha256 d07f8d54fda0d03066b8570868966732d389dd009413c2d96ff3ea81dec08d21.
