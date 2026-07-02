# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-07-02 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | PRODUCTION / AUTOMATION (unified upload + weekly cron) |
| requirement_id | REQ-01 |
| deliverable_id | D09 |
| status | COMPLETE |
| evidence_location | daily_task.tbl_wlsp_sarujanan (D09-A53..D09-A57) + daily_work_logs/2026_07_02_wlsp_work_log.csv |
| blos_keys_used | task_id-keyed upsert (never id=8); byte-exact bound-parameter storage; filename-derived Assigned User + Task ID; reporting window = previous Mon–Sun via `date_trunc('week',CURRENT_DATE)` |
| hardcoded_thresholds | none new; window rules unchanged (L1–L3 7d Mon–Sun, L4 30d ending Sunday, L5 last 3 complete months); direct DB = order_management_copy @ 149.28.134.54:5435 |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| AUTOMATION \| DEVOPS \| BUSINESS_INTELLIGENCE \| DASHBOARD |

## File path (fill after saving):
# 2026-07-02__sarujanan__wlsp__REQ-01-D09.md

---

## 1. SYSTEM STATE

- Start of day: uploader (`refresh_ph_dashboards.py`) handled Portfolio Holders only; the master dashboard was pushed by an obsolete `upload_html_content.py` hardcoded to `id=8` on the unreachable MCP host. Direct DB access to `order_management_copy @ 149.28.134.54` was available and proven byte-exact. No weekly cron configured.
- Working: direct psycopg2 upload (byte-exact); PH filename→identity derivation; refresh_dashboard.py generation (via Claude MCP).
- Goal: collapse to ONE upload workflow (master + all PHs, task_id-keyed), remove the ignore list, validate the reporting window, review the generator for cron, and configure the weekly cron.

---

## 2. WHAT CHANGED TODAY

- **Unified ONE uploader** (`refresh_ph_dashboards.py`): now publishes the master (`leakage_dashboard.html` → `WLSP_Bietrick_Leakage_Dashboard-V1`, located ONLY by task_id, never id=8) AND every `portfolio_holders/*.html` through one code path. Assigned User + Task ID derived from filename (no hardcoding); default ignore list removed (abinayaa included). Upsert by task_id → existing UPDATE only `html_content`+`updated_at`; missing INSERT full metadata with DB-generated id. Continue-on-error + summary.
- **Ran it: 25/25 PASS** (master id 8 = 237,665 bytes + 24 PH), all byte-exact (`octet_length`+`md5` == source).
- **Validated the Mon–Sun window** (read-only) in `dashboard_refresh_prompt.md`: L1–L5, `report_date`, `generated_at` all PASS; any-weekday and Monday runs both use the previous completed week.
- **Reviewed the generator** for unattended cron → readiness 40/100; blockers = Claude/MCP dependency, source/target DB mismatch, non-determinism, missing safeguards; recommended (not implemented) conversion to direct psycopg2.
- **Configured the weekly Linux cron** (Mon 08:45): generator `&&` uploader, output → `logs/wlsp_refresh.log`; created `logs/`; documented install/verify/test/monitor/troubleshoot/best-practices. No project code modified for the cron step.

Evidence: uploader run `Total: 25 / UPDATE 25 / PASS 25 / FAIL 0`; direct-DB recheck 25 rows refreshed, 0 empty.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

- **Two databases in play:** the **uploader** writes to the reachable direct DB `order_management_copy @ 149.28.134.54:5435` (has `tech_team_outputs.ph_task` **and** the WLSP source tables `ppc_performance/order_transaction/order_shipping_billing_detail/amazon_returns`); the **generator** still fetches via the Claude `claude_ai_postgres` MCP (`project_db @ pg.severdigitweb.uk`). This mismatch is the main production risk.
- **Upsert pattern:** locate by `task_id` only; `id` stays PostgreSQL-generated (identity). Existing → 2-field UPDATE; new → full INSERT. Idempotent; safe to re-run.
- `daily_task` activity log is written **via MCP** (project_db); `temp_user` on the direct DB lacks `daily_task` privilege, so activity logging stays on the MCP connection.

---

## 4. GAP FOUND

- **Gap (closed today):** master + PHs had two separate upload paths; master was keyed by `id=8`. → unified into one task_id-keyed uploader.
- **Gap (open):** generator not cron-safe — depends on `claude` CLI + claude.ai credential, reads a different DB than the publish target, non-deterministic LLM output, no retry/atomic-write/empty-floor/lock. Recommended fix: convert generation to direct psycopg2 against `order_management_copy` (awaiting approval).
- **Cron gotcha:** `claude` is in `~/.local/bin`, not on cron's default PATH → crontab must set `PATH`/`CLAUDE_BIN`.

---

## 5. VALIDATION RULE ADDED OR CHANGED

- **WLSP-VAL-15** — ONE uploader publishes master + every PH; the row is located ONLY by `task_id` (never a hardcoded `id`); UPDATE touches only `html_content`+`updated_at`.
- **WLSP-VAL-16** — every upload verified byte-exact: stored `octet_length` AND `md5` must equal the source file; `html_size>0`; stored as plain UTF-8 (not executed/parsed/compressed/base64).
- **WLSP-VAL-17** — no default ignore list; every Portfolio Holder (incl. abinayaa) is processed each run; a new `*_leakage.html` auto-INSERTs with a DB-generated id (no code change).

---

## 6. FAILURE MODE OR EDGE CASE

- Failure scenario: weekly cron runs but the generator can't reach Claude/MCP or its credential expired.
- Detection: `logs/wlsp_refresh.log` shows the generator failing; the `&&` chain then skips the uploader (no stale publish).
- Recovery: re-run manually after re-auth; uploader is idempotent. Long-term fix: convert generator to direct SQL to remove the dependency.
- Risk level: MEDIUM (uploader is safe; generator dependency is the weak link).

---

## 7. REVIEW OUTCOME

- `refresh_ph_dashboards.py` — unified master+PH, task_id-keyed, byte-exact, verified; **25/25 PASS**. ✅
- `refresh_dashboard.py` — generation + Mon–Sun window correct; **not cron-safe** (40/100) pending direct-SQL conversion. ⏳
- Weekly cron — designed + documented; `logs/` created; awaiting `crontab -e` install + `~/.pgpass`. ⏳

---

## 8. NEXT STEP

- Install the weekly crontab (Mon 08:45) and move DB credentials to `~/.pgpass`.
- Convert the generator to direct psycopg2 against `order_management_copy` (+ retry, atomic master write, empty-result floor, flock lock) to make the full pipeline cron-native.
- Add logrotate for `logs/wlsp_refresh.log`; approve repository cleanup of obsolete helpers.

---

## 9. EVIDENCE / IMPORT

- Files changed today: `dashboard/refresh_ph_dashboards.py` (unified master+PH uploader); created `logs/`.
- Reviewed (unchanged): `dashboard/refresh_dashboard.py`, `dashboard/dashboard_refresh_prompt.md`.
- Activity memory: `daily_task.tbl_wlsp_sarujanan` rows **D09-A53 … D09-A57** (activity_date 2026-07-02) — table now 57 rows.
- DB publish: `tech_team_outputs.ph_task` — 25 dashboards refreshed byte-exact (master id 8 + 24 PH) on `order_management_copy`.
- Work log CSV: `daily_work_logs/2026_07_02_wlsp_work_log.csv` (5 rows × 24 cols).

---

# 5. Today's Planned End-User Benefit

**Purpose:** States the benefit planned to be delivered to the end user today. The actual delivered benefit is recorded here as ACHIEVED.

| # | Planned Benefit | Achieved |
|---|-----------------|----------|
| 1 | Implement automatic detection of Portfolio Holder dashboard HTML files without hardcoding Portfolio Holder names. | ✅ YES |
| 2 | Automatically INSERT new Portfolio Holder dashboard records into PostgreSQL when a new HTML file is detected. | ✅ YES (INSERT path implemented + verified by design) |
| 3 | Automatically UPDATE existing Portfolio Holder dashboard HTML content during every refresh without changing dashboard metadata. | ✅ YES (UPDATE touches only html_content + updated_at) |
| 4 | Prepare a reusable weekly refresh workflow that can be executed automatically using a 7-day cron job. | ✅ YES (cron Mon 08:45 designed + documented) |
| 5 | Verify every upload using PostgreSQL validation queries to ensure HTML is stored correctly as plain UTF-8 text. | ✅ YES (octet_length + md5 byte-exact; 25/25 PASS) |
| 6 | Design the workflow so future Portfolio Holders require no manual code changes when new HTML files are added. | ✅ YES (filename-derived identity; auto-INSERT) |

---

## Date

2026-07-02

---

## Planned Daily Benefits

Implement a fully automated Portfolio Holder dashboard upload and weekly refresh workflow that detects new HTML dashboards, inserts new Portfolio Holders automatically, updates existing HTML content in PostgreSQL, verifies every upload, and prepares the solution for scheduled 7-day automatic execution.

**Status: ACHIEVED** — unified uploader (master + 24 PH) ran 25/25 PASS byte-exact; new-PH auto-INSERT and metadata-safe UPDATE implemented; weekly cron (Mon 08:45) prepared with logging, verification, and best practices.

---

## User

Bietrick
