# ETL Trace — DQ-1: What populates `public.ppc_performance.user_name`

**Date:** 2026-06-22 · **Mode:** READ-ONLY · **Auditor:** AIOS Worker · **Reviewer:** Bietrick (TL)
**Objective:** locate the **actual** code/SQL/procedure/trigger/script that writes `ppc_performance.user_name`.
**Discipline:** *no inference.* Only actual code or actual SQL is reported. Where code cannot be found, the
result is reported as **NOT FOUND** with the evidence of the search, not guessed.

---

## ⚠️ Headline result

> **The transformation that populates `public.ppc_performance.user_name` is NOT present in this PostgreSQL
> database and NOT present in the accessible filesystem.**
> - No trigger writes it. (evidence E-1)
> - No SQL/PL-pgSQL function references `ppc_performance` at all. (evidence E-2, E-3)
> - No ETL script exists in the repo/home filesystem. (evidence E-4)
>
> Population is therefore performed by an **external ETL process** (an application/service or remote loader)
> that lives **outside** this database instance and **outside** this workspace. **Its actual code could not be
> retrieved in this environment**, so — per the no-inference rule — the exact transformation logic, lookup
> table, and join cannot be shown from real code. What *can* be shown is the in-database lineage evidence
> below, which constrains what that external process does.

This also **corrects an earlier inference**: `HIGH_RISK_ROOT_CAUSE_ANALYSIS.md` stated PH is populated "by a
SKU-keyed lookup during ETL." That was an inference from column structure, **not** observed code. This trace
could not confirm it against actual code because the code is not accessible here. Treat that statement as
**unproven**.

---

## 1. Flow as far as it can be evidenced

```
[EXTERNAL PPC SOURCE FEED]            -- Amazon/eBay/Google ads APIs (not in DB)
        │   (no user_name in feed)
        ▼
public.ppc_etl_performance_data       -- RAW landing table. Has NO user_name column. (E-5)
        │
        ▼   ??? EXTERNAL ETL TRANSFORM — CODE NOT FOUND IN DB OR FILESYSTEM (E-1..E-4)
        │       (adds user_name, ss_name, category_name, source_name, marketplace)
        ▼
public.ppc_performance                -- ENRICHED table. user_name present but 40.6% NULL on UK ad-rows
```

The two ends of the flow are **actual** (E-5 schema facts). The middle arrow — the populating transform — is a
black box from this environment's perspective: no DB object and no repo file implements it.

---

## 2. Evidence — every place searched, with result

### E-1 · Triggers on the PPC tables → NONE
- **Object searched:** `information_schema.triggers` where `event_object_table IN ('ppc_performance','ppc_etl_performance_data')`
- **SQL:**
  ```sql
  SELECT event_object_schema, event_object_table, trigger_name, action_timing,
         event_manipulation, action_statement
  FROM information_schema.triggers
  WHERE event_object_table IN ('ppc_performance','ppc_etl_performance_data');
  ```
- **Result:** `[]` (empty) — **no trigger** populates `user_name`.
- **Impact:** rules out a trigger-based populator.

### E-2 · Functions whose body references the PPC tables → NONE
- **Object searched:** `pg_proc.prosrc` for all 18 PL/pgSQL functions (prosrc used because
  `pg_get_functiondef()` throws on aggregates).
- **SQL:**
  ```sql
  SELECT n.nspname, p.proname, l.lanname
  FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  JOIN pg_language l ON l.oid=p.prolang
  WHERE n.nspname NOT IN ('pg_catalog','information_schema')
    AND p.prokind='f' AND l.lanname IN ('sql','plpgsql')
    AND (p.prosrc ILIKE '%ppc_performance%' OR p.prosrc ILIKE '%ppc_etl_performance%');
  ```
- **Result:** `[]` (empty) — **no function references either PPC table**.

### E-3 · Functions referencing both `ppc` and `user_name` → NONE
- **SQL:**
  ```sql
  SELECT n.nspname, p.proname FROM pg_proc p
  JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_language l ON l.oid=p.prolang
  WHERE n.nspname NOT IN ('pg_catalog','information_schema')
    AND p.prokind='f' AND l.lanname IN ('sql','plpgsql')
    AND p.prosrc ILIKE '%ppc%' AND p.prosrc ILIKE '%user_name%';
  ```
- **Result:** `[]` (empty).
- **Search space proof:** the database has exactly **18 PL/pgSQL functions + 41 C functions**. The 41 C
  functions are **all from the `dblink` extension** (compiled; symbol names only, not ETL). The 18 PL/pgSQL
  functions are named and inspected:
  `fn_pob_set_updated_at`, `fn_block_killed_reversal`, `fn_enforce_evidence_on_close`, `approve_retirement`,
  `block_protected_asset_drop`, `flag_retirement_review`, `prevent_duplicate_html_delivery_layer`,
  `audit_ddl_drop`, `audit_ddl_end`, `bi_gap_log_set_updated_at`, `refresh_sku_economics`,
  `fn_amazon_ppc_guardian_can_execute`, `fn_amazon_ppc_guardian_evaluate_candidate`,
  `fn_amazon_ppc_guardian_execution_guard`, `fn_ph_action_transition`, `fn_refresh_fbm_nnr_snapshot`,
  `gpe_submit_validation_decision`, `set_bi_gap_log_updated_at`.
  None load PPC rows or set `user_name`. The `fn_amazon_ppc_guardian_*` functions are the PPC **bidding
  automation** (they pair with `ppc_etl_automation_log`, see E-7), **not** a row-load/enrichment transform.
- **Impact:** the entire in-database function space is covered and contains no populator.

### E-4 · Filesystem / repository → NO ETL CODE
- **Path searched:** `/home/led-247/AIOS_WEEKLY_LEAKAGE_IDENTIFICATION` and `/home/led-247`
- **Command:** `grep -rln "ppc_performance" …` and a `find` for `*.sql|*.py|*.js|*.ts|*.sh|*.yaml`
- **Result:** the only hits are (a) the Markdown docs created by this investigation and (b) Claude/VSCode
  history logs. **No ETL script, DAG, dbt model, or loader file exists** in the accessible filesystem. The
  workspace contains only `AIOS_Weekly_Leakage_Identification/` docs + `.git`.
- **Impact:** the populating code is not version-controlled or stored in this environment.

### E-5 · Schema endpoints (ACTUAL lineage facts)
- **Object:** `get_object_details` / `information_schema.columns`
- **Result:**
  - `public.ppc_etl_performance_data` columns = `performance_data_id, source, sub_source_id, marketplace_id,
    date, record_type, ref_id, sku, record_id, child_id, parent_id, impressions, clicks, spend, sales, orders,
    created_at, updated_at` → **NO `user_name`, NO `ss_name`, NO `category_name`.**
  - `public.ppc_performance` adds `source_name, marketplace, ss_name, category_name, **user_name**`.
- **Impact:** proves `user_name` is **added between** the raw and enriched tables — i.e., during the external
  transform, not delivered by the source feed.

### E-6 · Column comments (ACTUAL documented lineage)
- **Object:** `pg_description` on `public.ppc_performance`
- **Result (verbatim):**
  | Column | Comment |
  |--------|---------|
  | `user_name` | "User / analyst account label" |
  | `sku` | "Product SKU — **populated for Amazon ad-level rows only**; '0' for eBay and Google" |
  | `ref_id` | "ASIN (Amazon) or item_id (eBay) — '0' for campaign-level rows or Google; always pair with source" |
  | `category_name` | "Category label for the advertised product" |
- **Impact:** the `sku` comment is the only documented constraint near the gap — it confirms SKU is sparse by
  design (Amazon ad-level only), consistent with the blank-SKU accounts seen in DQ-1. The `user_name` comment
  documents **meaning** ("analyst account label") but **not its source or join** — so the lineage of
  `user_name` is undocumented even in metadata.

### E-7 · ETL log tables (what process *is* observable)
- **Objects:** `public.ppc_etl_automation_log`, `public.ppc_etl_change_log`, `public.etl_status`
- **Result:** `ppc_etl_automation_log` rows are **PPC bid/budget automation** events
  (`action_type='daily_budget_set_logs'`, `reason='Traffic present but no conversions'`, `record_type='campaign'`)
  — a different process from row-loading; it contains **no `user_name` assignment**. `etl_status` recent rows
  are index creation + column-comment operations (`comments_add`), **not** a row-load transform naming
  `user_name`. `ppc_etl_change_log` tracks field old/new values for bidding fields, not enrichment.
- **Impact:** even the operational logs do not name the user_name-populating step → it runs outside the logged
  DB automation.

### E-8 · `dblink` extension present
- **Object:** `pg_extension`
- **Result:** all 41 C functions belong to **`dblink`** (cross-database query extension).
- **Impact:** stated as fact only — the DB is *capable* of remote pulls; this does **not** prove the ETL uses
  it (no calling code found). Reported to avoid an unstated gap, not as a conclusion.

---

## 3. Where SKU is used / where PH is assigned / why PH becomes NULL

| Question | Answer from ACTUAL evidence | Evidence |
|----------|----------------------------|----------|
| Where is SKU used? | SKU exists on both raw and enriched tables; comment says "Amazon ad-level rows only", `'0'` otherwise | E-5, E-6 |
| Where is PH assigned? | **Cannot be shown** — no DB object or repo file assigns `user_name`; assignment occurs in an external transform not accessible here | E-1..E-4 |
| Why does PH become NULL? | **Not provable from code in this environment.** The DQ-1 *symptom* is measured (40.6% NULL, concentrated in SKU-less accounts) but the *mechanism* (e.g., a SKU→PH lookup miss) is an inference that **could not be confirmed against real code** | E-1..E-4; symptom in `HIGH_RISK_ROOT_CAUSE_ANALYSIS.md` |

---

## 4. Conclusion & recommended next action

**Root location of the populator:** EXTERNAL to this PostgreSQL instance and EXTERNAL to this workspace. No
trigger, function, view, or filesystem script in scope writes `ppc_performance.user_name`.

**Because the code is not accessible here, the trace cannot show its real source/transform/lookup.** To
complete DQ-1's ETL trace, the **actual external ETL artifact must be located** — recommended next steps
(all read-only / discovery):

1. Obtain the **PPC ETL service/repository** that loads `ppc_etl_performance_data` → `ppc_performance`
   (likely an application job or scheduler outside this DB). Ask the platform/ETL owner for its repo path.
2. Within that artifact, search for the write to `ppc_performance` and the assignment of `user_name` — that is
   where the SKU→PH (or sub_source→PH) mapping, if any, actually lives.
3. Until that artifact is in hand, **do not assert** the SKU-lookup mechanism as fact; the DQ-1 *impact*
   (22.8% of flagged L1 spend unattributed) stands on measured data and is unaffected by this code-location gap.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Locate the real code that populates `ppc_performance.user_name`; report honestly if absent |
| Business Question Supported | "What ETL writes the PPC PH owner, and why is it 40.6% NULL?" |
| Evidence Used | E-1…E-8 (read-only catalog + filesystem searches, this session) |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE — populator NOT FOUND in accessible DB/filesystem; external artifact required |
| Pass/Fail Rule | PASS if the populator is shown from real code, OR its absence is proven with evidence — **absence proven** |
| Next Step | Retrieve the external PPC ETL repo/service and re-run this trace against its real code |
| Known Limitations | Read-only; cannot see compiled/external code; the SKU→PH mechanism remains an inference, explicitly **not** confirmed here |
