# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-07-01 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | PUBLICATION (per-PH dashboard upload to ph_task + metadata normalization) |
| requirement_id | REQ-01 |
| deliverable_id | D08 |
| status | COMPLETE (master html_content upload PENDING external loader) |
| evidence_location | daily_task.tbl_wlsp_sarujanan (D08-A52) + daily_work_logs/2026_07_01_wlsp_work_log.csv |
| blos_keys_used | L1 spend>£3 & conv=0 (7d); L2 shipping>25% rev (7d); L3 (rev×0.45)−shipping−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 orders (30d); L5 net margin declining ≥2 consecutive months (3 mo); reporting window = previous Mon–Sun via `date_trunc('week',CURRENT_DATE)` |
| hardcoded_thresholds | YES — publish target row id 8 / WLSP_Bietrick_Leakage_Dashboard-V1; master md5 6d689e06 / 237665 bytes; dashboard template byte-identical across master + 24 PH files (only the WLSP_DATA marker block differs) |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| BUSINESS_INTELLIGENCE \| LEAKAGE_ANALYSIS \| DASHBOARD \| PUBLICATION |

## File path (fill after saving):
# 2026-07-01__sarujanan__wlsp__REQ-01-D08.md

---

## TODAY'S PLANNED END-USER BENEFIT

**Date:** 2026-07-01 · **Requested by (User):** Bietrick

Planned Daily Benefits:

1. **Portfolio Holder Dashboard Availability** — Upload all Portfolio Holder HTML dashboards into PostgreSQL as plain text so the Team Leader can retrieve each dashboard directly through Claude without accessing project files.
2. **Reliable Dashboard Storage** — Ensure every Portfolio Holder dashboard is stored with the correct project metadata, task information, version details, and upload verification for future retrieval.
3. **Large HTML Upload Investigation** — Identify and validate the correct approach for uploading the large `leakage_dashboard.html` file through the Claude → MCP → PostgreSQL workflow without altering the HTML content.
4. **Production Readiness** — Validate the dashboard storage workflow so it can be reused consistently for future weekly dashboard uploads and Team Leader handovers.

---

## 1. SYSTEM STATE

- Start of day: D07 COMPLETE (activity table 51 rows, D01-A01..D07-A51). The automated refresh (PostgreSQL → master leakage_dashboard.html → 24 PH dashboards → validate → PASS) was proven end-to-end; deploy-safe CSS and Light default were in place. `tech_team_outputs.ph_task` held only the metadata row id 8 (wlsp / WLSP_Bietrick_Leakage_Dashboard-V1) with no renderable HTML; the 24 per-PH dashboards existed on disk but were NOT yet published into ph_task.
- What was working: byte-identical master+PH template (only the `WLSP_DATA_START/END` block differs); the Mon–Sun reporting window; the Amazon-only / UNATTRIBUTED-exclusion logic.
- What was broken / unclear: how to publish 24 per-PH dashboards into ph_task through the MCP (SQL-only, no direct DB route from the build box); whether the 237 KB master html_content could go in via MCP; `id=8.project_code` was lowercase `wlsp` while the PH rows use `WLSP`; the reusable `upload_html_content.py` still hard-coded `PROJECT="wlsp"`; Edge Tools flagged CSS browser-compat warnings.
- Starting point: publish every Portfolio Holder dashboard into ph_task byte-exactly, normalize WLSP metadata, and pin down exactly what can/can't be uploaded via MCP.

---

## 2. WHAT CHANGED TODAY

- **Per-PH dashboard publication to ph_task (24 rows, byte-perfect)**: published Abinayaa (id 18) and all 23 remaining Portfolio Holder dashboards (ids 22–54) into `tech_team_outputs.ph_task` via MCP only. Each row stored the complete HTML as plain text and was verified byte-for-byte: `md5(html_content) == md5(source file)` AND `octet_length == file size` — 24/24 exact matches. Method: reuse the byte-identical template (head+tail) from an already-verified row (id 18) via `substring(... strpos(marker) ...)`, and transcribe only the per-PH data block inside a dollar-quoted literal, so the emoji/BOM/CSS template is never re-typed.
- **WLSP metadata normalization**: changed `id=8.project_code` from `wlsp` → `WLSP`; then propagated `id=8`'s `description` to all rows where `project_code='WLSP'` (25/25 rows now match) in one atomic transaction. No other columns/rows touched.
- **Fixed the reusable uploader** `dashboard/upload_html_content.py`: set `PROJECT="WLSP"`, simplified the `WHERE` to `id=8 AND task_id=…` (id+task_id are unique → `project_code` dropped), kept the single bound-parameter `UPDATE`, and upgraded verification from byte-count-only to **byte-count + md5** against the source.
- **CSS browser-compat warnings** resolved via config: added `dashboard/.hintrc` scoping the `compat-api/css` hint to ignore the intentional progressive-enhancement features (`color-mix`, `scrollbar-width`, `scrollbar-color`) across all 26 dashboard HTML files, and darkened the master card-body tokens (`--soft`/`--muted`) and weights (`.sku`/`.ph`/`.ml`/`.eq`) for readability.
- **Reporting window re-verified**: confirmed the auto window resolves to **Mon 2026-06-22 → Sun 2026-06-28** via ISO-week truncation (`date_trunc('week',CURRENT_DATE)`), weekday-robust even when run off-Monday.
- **Master upload limit confirmed**: investigated publishing the 237 KB master into ph_task id 8 via MCP (chunked template-splice). Proved the MCP-by-hand limit: the ~180 KB unique data block cannot be faithfully transcribed at scale (tool output truncates chunks >~28–34 KB). Prepared the Team-Leader strategy: run the fixed `upload_html_content.py` (bound parameter) from a DB-reachable host, then verify md5 6d689e06 / 237665 bytes.

Evidence reference: ph_task WLSP set = 25 rows (id 8 + 24 published), each PH row md5==source; master target md5 6d689e065a9f347f4c18e3d904f63e45, 237665 bytes.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

Table(s): `daily_task.tbl_wlsp_sarujanan` (activity memory, now +1 = D08-A52); `tech_team_outputs.ph_task` (hosted-tool task feed — 25 WLSP rows published today); source `public.ppc_performance`, `public.order_transaction`, `public.order_shipping_billing_detail`, `public.amazon_returns`.

Finding: the MCP `execute_sql` channel is the ONLY route to the DB from the build box (`pg.severdigitweb.uk` = NXDOMAIN here; `psycopg2` cannot connect). **Small/medium HTML (≤ ~64 KB) publishes fine via MCP** using the template-splice + data-block pattern; **large HTML (the 237 KB master) does not**, because the client (a human/LLM) must inline the bytes as SQL text and the ~180 KB unique data block exceeds faithful transcription / tool-output limits. Postgres `TEXT` + `||` concatenation is byte-exact and never corrupts what is sent — the constraint is purely on the client side.

SQL/architecture pattern: **template-splice publish** — `SET html_content = substring(head FROM a verified row) || $tag$<entity data block>$tag$ || substring(tail FROM a verified row)`; verify each row with `md5(html_content)` vs the source file. Reuse the shared shell from the DB instead of re-emitting it. For large artifacts, load via a **bound parameter** from a DB-reachable host.

Operational meaning: publish per-entity dashboards through MCP by reusing a stored byte-identical template and md5-gating every write; escalate only the oversize master to an external bound-parameter loader.

---

## 4. GAP FOUND

Gap description: (1) **24 PH dashboards unpublished** — they existed on disk but had no ph_task rows. (2) **project_code casing drift** — `id=8` was `wlsp` while all PH rows are `WLSP`, so `WHERE project_code='WLSP'` excluded it. (3) **Stale uploader constant** — `upload_html_content.py` hard-coded `PROJECT="wlsp"`, which would match 0 rows after normalization. (4) **Large-HTML MCP limit** — the 237 KB master html_content cannot be written via MCP by hand.

Impact if unresolved: PH dashboards not queryable in the task feed; the WLSP row set inconsistent by casing; the reusable uploader silently updates 0 rows; the master publication row has no renderable HTML.

Recommended action: (1) publish all 24 via the template-splice + md5 pattern (DONE). (2) normalize `id=8` to `WLSP` and propagate the shared description (DONE, 25/25). (3) fix `PROJECT="WLSP"` + simplify WHERE + md5 verify (DONE). (4) hand the master upload to the TL via the bound-parameter loader, verify md5 6d689e06 + 237665 bytes (PREPARED).

Owner: WLSP build (sarujanan). Reviewer/TL: Bietrick.

---

## 5. VALIDATION RULE ADDED OR CHANGED

- **WLSP-VAL-15** — a per-PH ph_task publish is PASS only when `md5(html_content) == md5(source file)` AND `octet_length == file bytes`; size-match alone is insufficient.
- **WLSP-VAL-16** — publish per-entity HTML by reusing a stored byte-identical template (splice from a verified row) and transcribing ONLY the entity data block; never re-emit the shared shell.
- **WLSP-VAL-17** — WLSP rows MUST use uppercase `project_code='WLSP'`; `id=8`'s `description` is the canonical shared description for the WLSP set.
- **WLSP-VAL-18** — html_content > ~64 KB MUST be loaded via a bound parameter from a DB-reachable host (never inlined into MCP SQL, never hand-chunked); verify by byte count + md5.

---

## 6. FAILURE MODE OR EDGE CASE

Failure scenario: attempting to publish the 237 KB master into ph_task id 8 through the MCP by chunked SQL.
How triggered: splicing the verified template + appending the ~180 KB data block as dollar-quoted chunks via `execute_sql`.
How detected: chunks >~28–34 KB are truncated from tool output (only a preview persists), so the unique data block cannot be read/re-emitted byte-safely; the per-chunk md5 gate flags any drift. The row was left partial (template head + 2 verified data chunks) rather than completed with corrupt content.
Recovery: complete the master via a bound-parameter loader on a host that resolves the DB (TL machine / MCP host); verify `octet_length=237665` and `md5=6d689e065a9f347f4c18e3d904f63e45` before reporting PASS.
Risk level: MEDIUM (master publication blocked until the external loader runs; id 8 currently partial; the 24 PH rows are complete and verified; no other data corruption).

---

## 7. REVIEW OUTCOME (publication)

- tech_team_outputs.ph_task — Abinayaa id 18 + 23 PH rows (ids 22–54) published; every row md5==source (24/24). ✅
- ph_task metadata — id 8 project_code normalized `wlsp`→`WLSP`; shared description propagated to all 25 WLSP rows (25/25 match). ✅
- dashboard/upload_html_content.py — PROJECT=WLSP; WHERE=id+task_id; bound-parameter kept; md5 verification added. ✅
- dashboard/.hintrc — CSS compat warnings scoped/silenced across 26 HTML files; card-body readability improved. ✅
- ph_task id 8 html_content (237 KB master) — MCP-by-hand limit confirmed; row currently partial; handed to TL bound-parameter loader with md5/byte verification. ⏳

---

## 8. NEXT STEP

- TL runs `dashboard/upload_html_content.py` (bound parameter) from a DB-reachable host to load leakage_dashboard.html into ph_task id 8, then read back and confirm 237665 bytes / md5 6d689e06.
- Confirm all 24 PH rows render correctly from the task feed.
- Optionally add an atomic byte-for-byte non-data guard on the master shell and store explicit data_start/data_end offsets in summary.

---

## 9. EVIDENCE / IMPORT

- Files created today: `dashboard/.hintrc` (CSS compat scope), `dashboard/load_html_into_ph_task.py` (parameterized loader), `daily_work_logs/2026-07-01__sarujanan__wlsp__REQ-01-D08.md`, `daily_work_logs/2026_07_01_wlsp_work_log.csv`.
- Files modified today: `dashboard/upload_html_content.py` (PROJECT=WLSP + WHERE simplify + md5 verify), `dashboard/leakage_dashboard.html` (card-body tokens/weights).
- Database work: `tech_team_outputs.ph_task` — published 24 PH dashboards (ids 18, 22–54) byte-perfect; normalized id 8 `project_code` → `WLSP`; propagated shared `description` to 25 WLSP rows; master html_content upload prepared for TL loader.
- Work log: `daily_work_logs/2026_07_01_wlsp_work_log.csv` (1 row, D08-A52, 24 columns).
- Activity memory: `daily_task.tbl_wlsp_sarujanan` row D08-A52 (activity_date 2026-07-01) — table now 52 rows.
- Supporting evidence: ph_task WLSP set = 25 rows; master target md5 6d689e065a9f347f4c18e3d904f63e45 / 237665 bytes; reporting window 2026-06-22 → 2026-06-28.
