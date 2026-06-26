# SKILL FILE — DAILY KNOWLEDGE EXTRACTION
# DIGITWEB LK LTD · Daily Skill Increment System · v3.0

---

## MANDATORY METADATA BLOCK

| Field | Value |
|-------|-------|
| date | 2026-06-25 |
| developer | sarujanan |
| project | AIOS Weekly Leakage Identification |
| project_code | WLSP |
| phase | BUILD / HARDENING |
| requirement_id | REQ-01 |
| deliverable_id | D04 |
| status | COMPLETE |
| evidence_location | daily_task.tbl_wlsp_sarujanan (D04-A28..D04-A34) + daily_work_logs/2026_06_25_wlsp_work_log.csv |
| blos_keys_used | L1 spend>£3 & conv=0 (7d); L2 shipping>25% rev (7d); L3 (rev×0.45)−shipping−PPC<£0 & PPC>£5 (7d); L4 refund>10% min 2 orders (30d); L5 net margin declining ≥2 consecutive months (3 mo); assumed COGS 20%, Platform fee 15%, VAT 20% |
| hardcoded_thresholds | YES — £3 PPC floor; 25% shipping ratio; 0.45 gross-margin factor; £5 PPC floor; 10% refund rate; min 2 orders; 2 consecutive months; COGS 20%/fee 15%/VAT 20%; CSV must have exactly 24 columns per row; L1 KPI = COUNT(DISTINCT ASIN); ppc_performance must be source_name ILIKE '%amazon%' |
| three_am_standard | PASS |
| llm_queryable | YES |
| company_knowledge_candidate | YES |
| domain | DATABASE \| BUSINESS_INTELLIGENCE \| LEAKAGE_ANALYSIS \| DASHBOARD \| AUTOMATION |

## File path (fill after saving):
# 2026-06-25__sarujanan__wlsp__REQ-01-D04.md

---

## 1. SYSTEM STATE

- Start of day: D03 COMPLETE — the executive dashboard existed (index.html + data.js) and the activity table held 27 rows (D01-A01..D03-A27). No day-wise context system, no refresh automation, and the dashboard had latent data-quality issues not yet found.
- What was working: the two-file dashboard rendered; L1-L5 calculation logic was correct.
- What was broken / missing: no automated refresh; no per-day context; the dashboard silently mixed **eBay PPC** into L1 (no Amazon filter on `ppc_performance`); the High-Shipping (L2) section showed blank SKUs; sidebar counts came from three different generations and did not reconcile.
- Starting point: build the context system + refresh automation, then audit and remediate the dashboard data quality.

---

## 2. WHAT CHANGED TODAY

- Created the **day-wise context memory system** (`context/2026-06-22..2026-06-25_context.md`) — no new DB column required.
- Built a **self-contained** `leakage_dashboard.html` (data embedded between HTML markers) plus a **refresh orchestrator** (`refresh_dashboard.py`) and **prompt** (`dashboard_refresh_prompt.md`); 4-hourly cron designed.
- Proved **MCP headless execution** (claude -p loads the MCP, `execute_sql` works, full read→SQL→write loop GREEN).
- **Amazon-only remediation**: added `source_name ILIKE '%amazon%'` to L1 + the L2/L3 + L5 PPC CTEs; removed 19 eBay rows from L1; eliminated the eBay account `so_926407`; excluded UNATTRIBUTED from `ph_summary`.
- **L2 SKU fix**: added `MAX(l.sku)` so the High-Shipping SKU column renders (40/40).
- **Single-pass count reconciliation**: regenerated all of `dashboardData` in one pass → L1=125 (distinct ASIN), L2=212, L3=17, L4=33, L5=9, zero diff vs source.
- **D04 preservation**: folded every fix into `dashboard_refresh_prompt.md` and added **regression guards** to `refresh_dashboard.py`.

Evidence: `AIOS_Weekly_Leakage_Identification/` (context/, dashboard/) + `daily_work_logs/2026_06_25_wlsp_work_log.csv` + PostgreSQL `daily_task.tbl_wlsp_sarujanan` (D04-A28..A34). No git commits this session — deliverables are documents + DB rows.

---

## 3. POSTGRESQL / MCP / DATABASE FINDING

Table(s): `public.ppc_performance`, `public.order_transaction`, `public.order_shipping_billing_detail`, `public.amazon_returns`; `daily_task.tbl_wlsp_sarujanan`.

Finding: **`ppc_performance` carries AMAZON + EBAY + SHOPIFY** (30d: 482k / 320k / 380k rows). The dashboard's PPC accesses (L1, L3/L5 PPC terms) lacked an Amazon filter, so **eBay contaminated L1** (19 flagged rows; eBay account `so_926407`). Order-side queries were already Amazon-clean. After `source_name ILIKE '%amazon%'`: L1 145→126 distinct-grain / **125 distinct ASIN**, L2=212, L3=17, L4=33, L5=9 declining PHs.

SQL pattern: every `ppc_performance` access MUST be `source_name ILIKE '%amazon%'`; L1 KPI = `COUNT(DISTINCT ref_id)`; `ph_summary` excludes UNATTRIBUTED; all counts + detail from a **single query pass**.

Operational meaning: the dashboard is Amazon-FBM only; PPC data is multi-marketplace, so the marketplace filter is mandatory on the ad table, not just the order table.

---

## 4. GAP FOUND

Gap: (1) L1/L3/L5 PPC accesses missing the Amazon filter → eBay/Shopify contamination. (2) L2 query ASIN-grain without `sku` → blank SKU column. (3) `summary.counts`, `account_summary`, `ph_summary`, L3/L4 detail generated at different times → counts did not reconcile (KPI 396 vs account rail 389) and L3/L4 were stale. (4) L1 counted at ASIN+SKU+PH grain (127) instead of the protocol's per-ASIN (125).

Impact: inflated/contaminated leakage lists, blank SKUs, and inconsistent sidebar numbers undermining trust.

Recommended action: Amazon filter on all PPC; `MAX(sku)` in L2; single-pass regeneration; `counts.l1 = COUNT(DISTINCT ASIN)`; exclude UNATTRIBUTED from `ph_summary`; add regression guards. **All applied today.**

Owner: WLSP build (sarujanan). Reviewer/TL: **Bietrick**.

---

## 5. VALIDATION RULE ADDED OR CHANGED

- **WLSP-VAL-03** — every `ppc_performance` access must filter `source_name ILIKE '%amazon%'` (marketplace purity).
- **WLSP-VAL-04** — sidebar KPI `counts.l1 = COUNT(DISTINCT ASIN)` (protocol per-ASIN grain).
- **WLSP-VAL-05** — `ph_summary` (PH cards/rankings/dropdown/sidebar) excludes `UNATTRIBUTED`.
- **WLSP-VAL-06** — all counts + `account_summary` + `ph_summary` + L1-L5 detail must be generated in one pass (no multi-vintage drift).
- **Refresh regression guards** — the orchestrator FAILS the run if eBay/Shopify/so_926407 appear in data or UNATTRIBUTED appears in `ph_summary`.
- Reaffirmed: WLSP-VAL-01 (idempotent `activity_id` PK upsert), WLSP-VAL-02 (CSV 24 columns/row).

---

## 6. FAILURE MODE OR EDGE CASE

Failure scenario: a scheduled refresh regenerates the dashboard from a prompt whose PPC queries lack the Amazon filter → eBay/Shopify silently re-enter L1/L3/L5 and the counts drift again.
Trigger: editing/regenerating subsets at different times (multi-vintage), or omitting the source filter on the ad table.
Detection: `refresh_dashboard.py` regression guards (marketplace tokens + UNATTRIBUTED in ph_summary); deterministic count check L1 125 / L2 212 / L3 17 / L4 33 / L5 9.
Recovery: re-run a single full pass via the corrected `dashboard_refresh_prompt.md`.
Risk level: MEDIUM (controlled by the guards).

---

## 7. REUSABLE ASSETS CREATED

- `dashboard/leakage_dashboard.html` — self-contained dashboard (marker data-block).
- `dashboard/refresh_dashboard.py` — refresh orchestrator with D04 regression guards.
- `dashboard/dashboard_refresh_prompt.md` — Amazon-only, single-pass, distinct-ASIN refresh spec.
- `context/<date>_context.md` — day-wise context memory pattern.

---

## 8. NEXT STEP

- Run the refresh on the cron host (with credentials) to produce the first automated `refresh.log` PASS.
- Backfill the context-file reference into `evidence_refs` for D01-D03 rows (on approval).
- Obtain **Bietrick** sign-off on OPTION B.

---

## 9. EVIDENCE / IMPORT

- Work log: `daily_work_logs/2026_06_25_wlsp_work_log.csv` (7 rows, D04-A28..A34, 24 columns each).
- Activity memory: `daily_task.tbl_wlsp_sarujanan` rows D04-A28..D04-A34 (idempotent UPSERT, activity_date 2026-06-25).
- Live proof: fixed-prompt SQL returned L1 125 / L2 212 / L3 17 / L4 33; guards FAIL on injected contamination.
