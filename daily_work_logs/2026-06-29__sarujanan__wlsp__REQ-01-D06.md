# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-06-29 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | REMEDIATION / VERIFICATION |
| requirement_id | REQ-01 |
| deliverable_id | D06 |
| status | COMPLETE |
| evidence_location | daily_task.tbl_wlsp_sarujanan (D06-A38..D06-A44) + daily_work_logs/2026_06_29_wlsp_work_log.csv |
| blos_keys_used | L1 spend>£3 & conv=0 (7d); L2 shipping>25% rev (7d); L3 (rev×0.45)−shipping−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 orders (30d); L5 net margin declining ≥2 consecutive months (3 mo); assumed COGS 20%, Platform fee 15%, VAT 20% |
| hardcoded_thresholds | YES — £3/25%/0.45/£5/10%/2 orders/2 months; COGS 20% / fee 15% / VAT 20%; **reporting window = previous Mon–Sun via `date_trunc('week',CURRENT_DATE)`**; L4 = 30d ending Sunday; L5 = last 3 complete months; **report_date = previous Sunday** (header derives Start=report_date−6, End=report_date); shipping = carrier_charge + shipping_template_price; **L5 now per PH × account + an `ALL` rollup**; CSV 24 columns/row |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| BUSINESS_INTELLIGENCE \| LEAKAGE_ANALYSIS \| DASHBOARD |

## File path (fill after saving):
# 2026-06-29__sarujanan__wlsp__REQ-01-D06.md

---

## 1. SYSTEM STATE

- Start of day: D05 COMPLETE (table 37 rows, D01-A01..D05-A37). The dashboard still held VS Code mock data; the refresh prompt used a plain `last 7 days` window, carrier-only shipping, SKU-grain L3 / ASIN-grain L4, and an L5 that had no account dimension.
- What was working: the orchestrator launch+validate+log flow; the Amazon-only / UNATTRIBUTED-exclusion business logic.
- What was broken / unclear: dashboard showed mock figures; the header Start/End dates were derived from the run date (not the data); Margin Trend ignored the account filter; the automated refresh could not complete a valid write.
- Starting point: replace mock data with correct live data, make the automation actually produce a validation-passing write, fix the reporting window/dates, and fix the Margin Trend account bug.

---

## 2. WHAT CHANGED TODAY

- **Regenerated the dashboard** from live PostgreSQL (one consolidated query → JSON → Python marker-splice). Corrected methodology: template-inclusive shipping (carrier + `shipping_template_price`) for L2/L3/L5, **ASIN-grain L3** (PPC via `ref_id`), **SKU-grain L4** (distinct-order refund rate), and **all flagged rows embedded** so live KPI counts equal true totals.
- **Hardened `refresh_dashboard.py`**: forbidden-table scan limited to data sections (so `verification_summary` can name excluded tables); L1 guard compares distinct-ASIN not row length; **added `Bash` to allowedTools**; raised timeout 1500→5400s. First automated run then passed (`RESULT: PASS`, 2026-06-29 15:21).
- **Implemented the Monday-run Mon–Sun window**: bounded L1/L2/L3 to `date_trunc('week',CURRENT_DATE)`; L4 = 30d ending Sunday; set `report_date` = previous Sunday so the header shows **2026-06-22 → 2026-06-28** (the real data range).
- **Fixed Margin Trend (L5) account split**: rewrote `Q_L5` with `GROUPING SETS` to emit per-(PH, account, month) trends + a combined `account='ALL'` slice; updated `renderL5`/`countFor` to filter L5 by the selected account.
- **Investigations/verification**: proved the HTML matches the DB to the penny (the reported "inflation" was OCR misreads + a 1-day boundary, not contamination); content-verified the full L1 dataset; diffed manual vs automated output (detail identical).

Evidence reference: refresh.log RESULT PASS (2026-06-29 15:21); counts 149/240/42/33/10; L5 = 213 rows carrying account ∈ {ALL, LEDSone UK, DCVoltage UK}.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

Table(s): `daily_task.tbl_wlsp_sarujanan`; source `public.ppc_performance`, `public.order_transaction`, `public.order_shipping_billing_detail`, `public.amazon_returns`.

Finding: read-only review confirmed the activity table at 37 rows (max D05-A37) → today is deliverable **D06** (D06-A38..A44, idempotent UPSERT). Live-data checks: today is **Monday 2026-06-29**; `date_trunc('week',CURRENT_DATE)` gives previous Mon 2026-06-22 / Sun 2026-06-28; the L1 set = 149 records over Jun 22–28. The old `>= CURRENT_DATE-7` predicate spanned 8 calendar days (it happened to equal Mon–Sun only because today is Monday with no same-day data).

SQL/architecture pattern: **`GROUPING SETS`** produce per-account rows + an `ALL` rollup in one pass (used for account-aware L5); **counts and arrays must come from the same query** or they desync under live data (the automated counts.l1 once read 148 while the detail held 149 distinct ASINs — a grain effect from ASIN-rollup vs ASIN+SKU detail).

Operational meaning: `counts.l1` should be `COUNT(DISTINCT asin)` of the L1 detail set, not a separate ASIN-rollup snippet, so the validator's distinct-ASIN guard always holds.

---

## 4. GAP FOUND

Gap description: (1) **Automation could not write** — the ~108 KB embed-all block cannot be Edited inline by the headless LLM, so it scripts a splice that needs `Bash`, which was not in allowedTools (every Bash call returned "requires approval" and was denied non-interactively). (2) **`counts.l1` grain desync** — the prompt computed it from an ASIN-rollup snippet (148) that can differ from the L1 detail distinct-ASIN (149), failing the validator. (3) **Header dates** were derived from the run date, showing Jun 23–29 instead of the data's Jun 22–28. (4) **Margin Trend** had no account dimension, so every account view was identical.

Impact if unresolved: the scheduled refresh never produces a valid file; intermittent validation failures; misleading header dates; account filter appears broken on the Margin Trend tab.

Recommended action: (1) add `Bash` to allowedTools + raise timeout (DONE). (2) define `counts.l1` from the detail set; correct the validator L1 guard (DONE). (3) set `report_date` = previous Sunday and bound windows to the week (DONE). (4) split L5 by account with a combined `ALL` slice (DONE).

Owner: WLSP build (sarujanan). Reviewer/TL: Bietrick.

---

## 5. VALIDATION RULE ADDED OR CHANGED

- **WLSP-VAL-08** — reporting window is the **previous Mon–Sun** week (`date >= date_trunc('week',CURRENT_DATE) - 7d AND date < date_trunc('week',CURRENT_DATE)`); the header Start/End must equal that range; never include the current partial week.
- **WLSP-VAL-09** — `counts.l1` MUST equal `COUNT(DISTINCT asin)` of the embedded L1 detail (no separate ASIN-rollup snippet); the validator's forbidden-table scan excludes `verification_summary`.
- **WLSP-VAL-10** — every L5 row carries an `account` field; `account='ALL'` = the combined cross-account trend and equals the sum of the per-account slices; the dashboard account filter segments L5.

---

## 6. FAILURE MODE OR EDGE CASE

Failure scenario: a verification reports the dashboard figures as "inflated" / cross-account contaminated.
How triggered: comparing the HTML against a DB query run over a different window (Jun 23–28 vs the dashboard's Jun 22–28) and reading the screenshot via OCR (6→8, 3→5; garbled ASINs).
How detected: per-date × account × record_type decomposition — every gap equalled the Jun 22 boundary day; `ledsone_spend = 0` for all flagged ASINs.
Recovery: confirm grain + window before assuming a bug; pin the window to Mon–Sun so verification and dashboard align.
Risk level: LOW (no data defect; reconciliation/communication issue).

---

## 7. REVIEW OUTCOME (refresh workflow)

- leakage_dashboard.html — regenerated data block; account-aware L5; header shows Mon–Sun; validator PASS. ✅
- dashboard_refresh_prompt.md — Mon–Sun window on L1/L2/L3, L4 30d-ending-Sunday, L5 GROUPING SETS, report_date = previous Sunday, reporting-window section added. ✅
- refresh_dashboard.py — Bash allowed, timeout 5400s, forbidden-scan scoped to data, L1 distinct-ASIN guard; first headless run PASSED. ✅ (open: optional single-query→Python-splice + byte-for-byte non-data guard.)

---

## 8. NEXT STEP

- Pin `counts.l1` in the prompt to `COUNT(DISTINCT asin)` of the L1 detail set (remove the residual ASIN-rollup snippet) so automated runs never desync.
- Optionally move to single-query → Python-splice so the orchestrator (not the LLM) writes the file deterministically, and add a byte-for-byte non-data guard + atomic write.
- Confirm with Bietrick that per-account `declining` flags are the desired action signal; schedule the first Monday cron run.

---

## 9. EVIDENCE / IMPORT

- Files changed today: `dashboard/leakage_dashboard.html` (data + renderL5/countFor account-aware + report_date), `dashboard/dashboard_refresh_prompt.md` (window, shipping, L3/L4 grain, L5 GROUPING SETS, reporting-window section), `dashboard/refresh_dashboard.py` (Bash, timeout, validator guards).
- Work log: `daily_work_logs/2026_06_29_wlsp_work_log.csv` (7 rows, D06-A38..A44, 24 columns each).
- Activity memory: `daily_task.tbl_wlsp_sarujanan` rows D06-A38..D06-A44 (idempotent UPSERT, activity_date 2026-06-29).
- Supporting evidence: `prompt_output/` CSVs (zero_conversion / shipping_over_25pct / net_negative / refund_rate / ph_margin_trend) dated 2026-06-29; refresh.log `RESULT: PASS` 2026-06-29 15:21.
