# AIOS Weekly Leakage Identification (WLSP) - Handover

| Field | Value |
|---|---|
| Project name | `aios_weekly_leakage_identification` - "Weekly Leakage Identification & Stop-Loss Protocol", project code `WLSP` |
| Project folder | `/home/led-247/AIOS_WEEKLY_LEAKAGE_IDENTIFICATION/` (workspace = `AIOS_Weekly_Leakage_Identification/`, its own git repo, branch history 2026-06-22 to 2026-08-03) |
| Developer / author | Sarujanan (git author `sarujanandigitweb-developer`; daily logs `*__sarujanan__wlsp__*`; activity table `daily_task.tbl_wlsp_sarujanan`). Authorship confirmed from commits, file headers and daily logs. |
| Protocol owner / reviewer | Bietrick (TL) - documented in README, REQ-001 and the daily logs |
| Handover written | 2026-10-05, from the current code, git history, logs and crontab |

## 1. Project Overview

**Purpose.** A weekly report that finds money leaking from UK Amazon FBM (own-fulfilled) trading for LEDSone UK and DCVoltage UK and gives every Portfolio Holder (PH) an action list. Source requirement: `Bietrick_Weekly_Leakage_Protocol_v2.pdf` (summarised in `requirements/REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md`).

**The five analyses (final, as implemented in `dashboard/dashboard_refresh_prompt.md`):**

| ID | Analysis | Window | Rule |
|---|---|---|---|
| L1 | Zero-conversion PPC | previous Mon-Sun week | ASIN+SKU spend > GBP 3 AND orders = 0 |
| L2 | Shipping > 25% of revenue | previous Mon-Sun week | shipping / revenue > 25%, ASIN grain |
| L3 | Net-negative ASIN still on PPC | previous Mon-Sun week | (revenue x 0.45) - shipping - PPC < 0 AND PPC > GBP 5, ASIN grain |
| L4 | High refund rate | 30 days ending the previous Sunday | distinct refunded orders / distinct orders > 10%, min 2 orders, SKU grain |
| L5 | PH net-margin decline | last 3 complete calendar months | margin % falls two consecutive months, per PH and per account (plus an `ALL` slice) |

**Deliverables:** one master dashboard (`dashboard/leakage_dashboard.html`, for Bietrick) and one standalone dashboard per Portfolio Holder (`dashboard/portfolio_holders/<name>_leakage.html`, 30 files), published weekly into `tech_team_outputs.ph_task` (the Varman/PH task feed).

## 2. Final Status

| Item | Status |
|---|---|
| Discovery, architecture decision (OPTION B), calculation design, validation | Complete (June 2026) |
| L1-L5 dashboard, per-PH dashboards, weekly publish to `ph_task` | Built and in production use |
| Last fully successful weekly run | Monday **2026-09-14** (data week ending 2026-09-13, V8 rows inserted for 31 dashboards) |
| Weekly automation today | **BROKEN since 2026-09-21** - see section 10. Overall: **Known Limitation / External Dependency** (needs the `claude` CLI path fixed in cron). |

Cron-run history (`logs/wlsp_refresh.log`): PASS 07-06, 07-13 (second attempt), 07-20 (second attempt), 07-27, 08-03 (second attempt), 08-12 (manual), 08-17, 08-31, 09-07, 09-14. FAIL: 07-13 (L1 count mismatch, later fixed), 07-20 and 08-03 and 08-24 ("dashboard unchanged after run" - headless run wrote nothing), 09-21 and 10-05 ("Claude CLI not found"). No log entry exists for 08-10 or 09-28 (cron did not run or logged nothing - not verified).

## 3. Latest Updates

Git history (all by the developer; 22 commits). Key dated changes:

| Date | Change |
|---|---|
| 2026-06-22/23 | Discovery of existing leakage engine in `development` schema, validation audit, ETL trace, `CALCULATION_DESIGN.md` (L1-L5 source-query design). Decision: OPTION B (extend). |
| 2026-06-24/25 | First dashboard (`index.html` reading `data.js`), then `refresh_dashboard.py` automation; Amazon-only filters and regression guards (D04). |
| 2026-06-29 | Real live data; Mon-Sun reporting window via `date_trunc('week',CURRENT_DATE)`; `report_date` = previous Sunday; L5 account split with `GROUPING SETS`; `Bash` added to the headless allowed tools; timeout raised to 5400 s. |
| 2026-06-30 | Per-Portfolio-Holder dashboards generated from the one master `dashboardData`. |
| 2026-07-01/02 | `INCIDENT.md`: large HTML cannot go through MCP `execute_sql` (truncation). Fixed by a direct psycopg2 uploader with a bound parameter. One unified uploader `refresh_ph_dashboards.py` (master + all PHs). Weekly cron installed (D09). |
| 2026-07-21 | Added `skills/` (TABLE_*.md / SKILL_*.md table definitions) and moved the uploader to **append-versioned** weekly rows. |
| 2026-08-03 (last commit `809cd36`) | PH dashboards and `refresh_ph_dashboards.py` updated; prompt/allowed-tools changed because the Postgres connector is now `mcp__claude_ai_postgres_2` (renumbered connectors had caused the 08-03 "blocked at permission layer" failure). |
| after 2026-08-03 (UNCOMMITTED) | Weekly runs through 2026-09-14 rewrote `dashboard/leakage_dashboard.html`, all 30 PH dashboards, `dashboard/refresh.log`, `logs/wlsp_refresh.log`; `refresh_dashboard.py` and `dashboard_refresh_prompt.md` have uncommitted edits (the connector-renumbering fix above). These are the **latest working implementation**; they are not in git. |

**Latest working implementation (what to continue from):**
1. `dashboard/refresh_dashboard.py` launches headless `claude -p` with `dashboard_refresh_prompt.md`. Claude runs the approved SQL through a Postgres MCP connector, builds `dashboardData` JSON and replaces only the text between `<!-- WLSP_DATA_START -->` and `<!-- WLSP_DATA_END -->` in `leakage_dashboard.html`.
2. The script validates the master (markers, JSON keys, count reconciliation, forbidden tables, Amazon-only guard), then regenerates the 30 PH files by filtering that same data (no extra SQL) and validates shell byte-identity and PH isolation.
3. `dashboard/refresh_ph_dashboards.py` publishes master + PH files to `tech_team_outputs.ph_task` using direct psycopg2.

## 4. Project Structure / Important Files

```
/home/led-247/AIOS_WEEKLY_LEAKAGE_IDENTIFICATION/
  WLSP_Theepana_Leakage_Dashboard.html   stale single-PH copy (week 2026-06-28, saved 2026-07-01); not used by code
  scratchpad/ph_task_all_103.csv         one-off export of ph_task (2026-07-06); reference only
  AIOS_Weekly_Leakage_Identification/    the git repo
    README.md, START_HERE.md             discovery-phase entry points (dated 2026-06-22/23; status line "Implementation NOT STARTED" is OUTDATED)
    CALCULATION_DESIGN.md                L1-L5 source-query design (2026-06-23)
    INCIDENT.md                          why MCP cannot upload big HTML (resolved by direct DB upload)
    POSTGRES_DATA_GAP_ANALYSIS.md, ETL_TRACE_DQ1.md, HIGH_RISK_ROOT_CAUSE_ANALYSIS.md, VALIDATION_AUDIT.md, CORRECTION_SUMMARY.md
    requirements/ discovery/ architecture_review/ validation/ closure/ evidence/   June 2026 discovery record
    skills/                              TABLE_*.md and SKILL_*.md reference for source tables (added 2026-07-21)
    context/                             day contexts 2026-06-22 to 06-29
    daily_work_logs/                     D01-D09 skill files + 25-column CSVs (2026-06-22 to 2026-07-02)
    prompt_output/                       CSV outputs of 2026-06-29 manual runs
    logs/wlsp_refresh.log                cron output (append)
    dashboard/
      dashboard_refresh_prompt.md        THE SQL + assembly rules (source of truth for business logic)
      refresh_dashboard.py               orchestrator + validator + PH generator
      refresh_ph_dashboards.py           uploader to tech_team_outputs.ph_task
      leakage_dashboard.html             master dashboard (self-contained, data between markers)
      portfolio_holders/*_leakage.html   30 per-PH dashboards (regenerated every run; stale ones deleted)
      refresh.log                        orchestrator log
      index.html + data.js               OLD June prototype reading data.js; not used by the pipeline
      _wlsp_build.py, _wlsp_l2.py, _wlsp_l345.py, _wlsp_inject.js   June one-off helper scripts with embedded sample data (legacy)
      *.bak, __pycache__                 backups/caches (leakage_dashboard.html.bak, .prefix-20260713-090120.bak)
    handover/                            this handover
```

## 5. Data Sources / Database Tables

All in the `order_management_copy` PostgreSQL database (read access for calculations; the same DB holds the output table).

| Table | Use |
|---|---|
| `public.ppc_performance` | L1, L3 (PPC by ASIN), L5. Columns: date, record_type (`'ad'`), ref_id (=ASIN), sku, ss_name, user_name, spend, orders, clicks, impressions, marketplace, source_name. Large (~24M rows): always window-scope. |
| `public.order_transaction` | L2, L3, L4, L5 and SKU-to-PH map. Filters: Amazon, market_place UK, `fba_sales=false`; `order_status='Completed'` (L2/L3), `'Refunded'` for L4 numerator, Completed+Refunded for L5. |
| `public.order_shipping_billing_detail` | Shipping per order = MAX GBP `carrier_charge` + MAX `shipping_template_price`, counted once per order, allocated to ASINs by revenue share. |
| `public.amazon_returns` | Named as an allowed source in the prompt; the current queries do not use it (refunds come from `order_transaction.order_status`). |
| `tech_team_outputs.ph_task` | OUTPUT. Weekly rows: `task_id = WLSP_<Name>_Leakage_Dashboard-V{n}`, `project_code='WLSP'`, `html_content`, `version_level`, `version_status` (`released` then reviewer sets `completed`), `assigned_user_team='ph_priors'`, `action_took_by` (reviewer). |
| `daily_task.tbl_wlsp_sarujanan` | Developer activity log (PK project_code + activity_id). Not used by the pipeline. |

**Forbidden in calculations** (validator fails if they appear in data): `development.leakage_detection`, `development.leakage_classification`, `ph_action_board.*`, `ph_daily_actions` (existing engine - OPTION B chose to build a separate weekly layer on top of the profitability data, not read these).

**Assumptions baked into formulas:** COGS 20%, platform fee 15% (gross factor 0.45), VAT 20%. Account normalisation from `ss_name`: contains `dcvoltage` = "DCVoltage UK"; contains `ledsone`/`led_sone`/`electricalsone`/`ledsonede`/`srm` = "LEDSone UK".

External services: claude.ai hosted Postgres MCP connector(s) (calculation step); direct network access to the old order_management_copy DB host (upload step). Connection settings are environment variables only (see section 7).

## 6. Current Workflow / Architecture

```
cron Mon 08:45 -> refresh_dashboard.py
   -> claude -p (headless) + Postgres MCP -> SQL L1..L5, summaries
   -> splice dashboardData into leakage_dashboard.html (markers only)
   -> validate master -> generate 30 PH files from same data -> validate
-> refresh_ph_dashboards.py
   -> psycopg2 INSERT/UPDATE into tech_team_outputs.ph_task, verify size + md5
```

**Business rules to preserve:**
- Reporting week = previous Monday-Sunday: `date >= date_trunc('week',CURRENT_DATE)-7d AND date < date_trunc('week',CURRENT_DATE)`. `summary.report_date` = previous Sunday (header shows report_date-6 to report_date). `generated_at` = run date.
- Amazon-only (D04 fix): `source_name ILIKE '%amazon%'` on PPC and orders (excludes eBay/Shopify/`so_926407`).
- `ph_summary` excludes `UNATTRIBUTED`; L1-L4 detail keeps UNATTRIBUTED rows tagged `ph_status` RECOVERABLE (SKU exists in the SKU-to-PH map) or MISSING_SOURCE.
- `counts.l1` = COUNT(DISTINCT asin) of the embedded L1 detail (never an ASIN-rollup HAVING; this caused the 2026-07-13 failure 124 vs 125). The orchestrator also re-derives counts from the embedded detail (`reconcile_counts`).
- A PH with no leakage still gets a dashboard (zeroed `ph_summary` synthesised).

**Publish versioning (`refresh_ph_dashboards.py`):** per PH, compare the file's `report_date` with the latest stored version: newer week = INSERT V(n+1); same week = idempotent UPDATE unless a reviewer has actioned it (then SKIP/frozen); older week = SKIP. Assigned User is the original PH name from the data; the task_id stem is derived from the filename. Master maps to `WLSP_Bietrick_Leakage_Dashboard`. A UniqueViolation on the identity column is handled by allocating `max(id)+1`.

## 7. How to Run

Prerequisites: python3, `psycopg2-binary`, the `claude` CLI (currently `/usr/bin/claude`), a valid claude.ai login for the user (`~/.claude/.credentials.json`) so the hosted Postgres connector loads, and network access to the DB host.

```bash
cd /home/led-247/AIOS_WEEKLY_LEAKAGE_IDENTIFICATION/AIOS_Weekly_Leakage_Identification
# 1) calculate + refresh dashboards (takes about 5-20 min; WRITES the HTML files)
CLAUDE_BIN=/usr/bin/claude python3 dashboard/refresh_dashboard.py
# 2) publish to ph_task (WRITES to the database)
python3 dashboard/refresh_ph_dashboards.py
```

Environment variables (not stored in this document): `CLAUDE_BIN`, `WLSP_REFRESH_TIMEOUT` (default 5400 s), `WLSP_IGNORE` (comma list of PH files to skip), and for the uploader `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`. **No `.env` exists in the project**; the uploader falls back to defaults hardcoded in `refresh_ph_dashboards.py` (see section 10).

## 8. Refresh / Deployment Process

- **Schedule:** user crontab (user `led-247`), Mondays 08:45 server time (a later `CRON_TZ=Asia/Colombo` line exists in the same crontab; system timezone documented elsewhere as Asia/Colombo):
  `45 8 * * 1 cd <workspace> && /usr/bin/python3 dashboard/refresh_dashboard.py >> logs/wlsp_refresh.log 2>&1 && /usr/bin/python3 dashboard/refresh_ph_dashboards.py >> logs/wlsp_refresh.log 2>&1`
  with `PATH=/home/led-247/.local/bin:/usr/local/bin:/usr/bin:/bin` and `CLAUDE_BIN=/home/led-247/.local/bin/claude` set above it. The uploader runs only if the refresh succeeds (`&&`).
- **Deployment:** there is no separate deploy. "Published" = rows inserted in `tech_team_outputs.ph_task` with `version_status='released'`; reviewers (PHs) mark them completed. Nothing is pushed to the Varman hub through a different script for this project.
- The docstring in `refresh_dashboard.py` says "every 4 hours" and the uploader docstring says `0 6 * * 1`; both are outdated. The real schedule is the crontab line above.
- Re-running in the same week is safe (idempotent UPDATE unless actioned).

## 9. Validation Completed

- Discovery/design validation (June 2026): `validation/VALIDATION_RESULT.md` (GREEN/PASS), `COVERAGE_MATRIX.md`, `QUERYABILITY_CHECK.md`, `VALIDATION_AUDIT.md` and corrections C-1..C-7 (`CORRECTION_SUMMARY.md`).
- Data validation (daily logs D04-D06): HTML figures matched the DB to the penny; the L1 audit confirmed all 149 records satisfy every rule; Amazon-only contamination removed; L5 account split fixed.
- Automated on every run (`refresh_dashboard.py`): file changed, one marker pair, JSON keys, counts reconciled, L2 not capped, no forbidden tables, no eBay/Shopify tokens, no `UNATTRIBUTED` in `ph_summary`, L1 distinct-ASIN guard, per-PH shell byte-identity and PH isolation.
- Upload verification (`refresh_ph_dashboards.py`): stored `octet_length` and `md5` equal to the source file, team and status asserted. Last run 2026-09-14: 31 processed, 31 INSERT, 31 PASS, 0 FAIL.
- Latest counts (2026-09-14 run): L1=135, L2=318, L3=46, L4=33, L5=8.

## 10. Known Issues / Dependencies

1. **Cron is broken (highest priority).** `CLAUDE_BIN=/home/led-247/.local/bin/claude` no longer exists (the CLI is `/usr/bin/claude`), so runs on 2026-09-21 and 2026-10-05 failed immediately. No data refresh/publish has occurred since 2026-09-14. Fix: change `CLAUDE_BIN` in the crontab to `/usr/bin/claude` (not changed by this handover). Also check why nothing was logged for 2026-09-28.
2. **Hardcoded DB credentials in code.** `dashboard/refresh_ph_dashboards.py` contains default host/user/password values for the order_management_copy DB (committed to git). Move to environment variables / a git-ignored `.env` and rotate the password. Value intentionally not reproduced here.
3. **Uncommitted work.** See section 3: regenerated dashboards, logs, and edits to `refresh_dashboard.py` and `dashboard_refresh_prompt.md` are not committed. Review and commit.
4. **Fragile LLM-in-the-loop.** The calculation is executed by a headless Claude session through a hosted MCP connector. Observed failures: connector renumbering (`mcp__claude_ai_postgres` vs `_postgres_2` vs `Ledsone_postgres`; the current allowed list covers all three), "unchanged after run" (07-20, 08-03, 08-24), and a count mismatch (07-13, since fixed). It requires a valid claude.ai login for the cron user. A deterministic Python/psycopg2 implementation of the prompt SQL (the uploader already reaches the same DB) would remove this dependency; the prompt itself already suggests a single-query design as the fallback.
5. **Documentation drift.** `README.md`/`START_HERE.md` still say implementation not started and recommend OPTION B pending sign-off; `refresh_dashboard.py`/uploader docstrings give wrong cron timing; INCIDENT.md describes a pre-fix state (id=8 upload) that is resolved.
6. **Legacy files:** `dashboard/index.html`, `data.js`, `_wlsp_*` helper scripts, `.bak` files and the root-level `WLSP_Theepana_Leakage_Dashboard.html` are not used by the pipeline.
7. **Data limits:** PPC `user_name` was ~40% null at discovery (rows become UNATTRIBUTED); PPC joined to orders at ASIN grain; L2/L3 rely on a fixed 0.45 margin factor.
8. `ph_task.id` identity sequence can fall behind; handled in code but the DB role cannot reset the sequence.
9. Whether Bietrick signed off OPTION B formally is "Not documented / could not verify" (work proceeded and was delivered regardless).

## 11. Backup Person / Owner

- Backup developer: **Not documented.**
- Documented owners: Bietrick (TL) - protocol owner, reviewer and recipient of the master dashboard; Sarujanan - developer/worker (leaving). Data/DB owner for `order_management_copy`: Not documented. Portfolio Holders (30, listed by file in `dashboard/portfolio_holders/`) consume their own dashboards and action the `ph_task` rows.

## 12. Troubleshooting

| Symptom | Check / action |
|---|---|
| "Claude CLI not found" | Fix `CLAUDE_BIN` (use `/usr/bin/claude`); confirm `claude -p "hi"` works as the cron user. |
| "unchanged after run", "blocked at permission layer" | Headless run could not query/write. Confirm the claude.ai Postgres connector for `order_management_copy` is authorised; read the tail of `logs/wlsp_refresh.log` and `dashboard/refresh.log`; check which `mcp__claude_ai_*postgres*` name resolves `public.ppc_performance` and put it in `ALLOWED` and the prompt. |
| "counts.l1 != distinct ASIN" | L1 must be counted at ASIN+SKU grain then distinct ASIN (prompt "D04 FIX D"). |
| "forbidden tables"/"marketplace contamination" | A query used a non-approved table or missed `source_name ILIKE '%amazon%'`. |
| Uploader SKIP "stale"/"already actioned" | Expected: file week older than stored, or reviewer already actioned that week. |
| Uploader FAIL md5/size | Re-run; ensure file is read as UTF-8 and the bound parameter path was not altered. |
| Cannot connect to DB | Verify network access and the `PG*` environment variables; credentials are not in this document. |
| New PH missing | PH appears only if present in L1-L5 data for the week; a new `*_leakage.html` is auto-inserted as V1. |

## 13. Final Handover Notes

- Authorship confirmed as Sarujanan's work (commits, `*__sarujanan__wlsp__*` logs, `daily_task.tbl_wlsp_sarujanan`).
- First actions for the backup: (1) fix `CLAUDE_BIN` in crontab and run the two commands in section 7 manually for the week ending the most recent Sunday, (2) move DB credentials out of the code, (3) commit the pending changes, (4) update README/START_HERE status.
- The prompt file `dashboard/dashboard_refresh_prompt.md` is the single source of truth for SQL and rules; the orchestrator and uploader are mechanical wrappers around it.
- Do not read the `development.leakage_*` tables or `ph_action_board.*` in calculations; keep DB access read-only except for the single `ph_task` upload.
- Status of this handover document: Newly Created (no prior handover existed in the project).
