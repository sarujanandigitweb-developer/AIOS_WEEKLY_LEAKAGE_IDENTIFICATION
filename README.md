# AIOS Weekly Leakage Identification — Investigation Workspace

**Status:** Phase 1 + Phase 2 discovery COMPLETE · Architecture decision RECORDED · Implementation NOT STARTED
**Owner:** Bietrick (TL) — Protocol Owner & Executor
**Worker:** Sarujanan
**Scope:** UK Amazon FBM — All Portfolio Holders (PHs) under Bietrick
**Last updated evidence observed:** 2026-06-22 (live Postgres discovery)

---

## What this workspace is

This is the Mini-AIOS investigation record for the **Weekly Leakage Identification & Stop-Loss Protocol v2.0**.
It documents — with evidence — whether the existing PostgreSQL database can support the 5 weekly leakage
analyses defined in the protocol, what leakage assets already exist, and which architecture should be used to
deliver the weekly protocol **without creating duplicate truth**.

This workspace is **documentation and evidence only**. No tables were created, no data was modified, and no
leakage logic was built during this investigation. The four governing principles were followed throughout:

1. **Existing Asset First** — search and reuse before building.
2. **Evidence First** — every claim is backed by a recorded query result.
3. **Duplicate Truth Prevention** — do not produce a second competing source of the same fact.
4. **Queryability First** — confirm the data can actually be queried before designing on top of it.

---

## The 5 Leakage Analyses (from the protocol)

| ID | Name | Window | Threshold |
|----|------|--------|-----------|
| L1 | ASIN PPC Spend — Zero Conversions | 7 days | Spend > £3 AND conversions = 0 |
| L2 | Shipping Exceeds 25% of Revenue | 7 days | Shipping > 25% of revenue |
| L3 | Net-Negative ASINs Still Receiving PPC | 7 days | (Revenue × 0.45) − Shipping − PPC < £0 AND PPC > £5 |
| L4 | High Refund Rate ASINs | 30 days | Refund rate > 10%, min 2 orders |
| L5 | PH Net Margin Trend — Consecutive Decline | 3 months | Margin declining ≥ 2 consecutive months |

---

## Folder map

```
AIOS_Weekly_Leakage_Identification/
├── README.md                  ← you are here
├── START_HERE.md              ← read this first; reading order + 60-second summary
│
├── requirements/
│   └── REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md   ← what the protocol demands
│
├── discovery/
│   ├── PHASE1_EXISTING_ASSET_SCAN.md        ← what data assets exist
│   ├── SOURCE_OBJECT_INVENTORY.md           ← tables + views catalogue
│   ├── PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md   ← the existing leakage engine
│   └── DUPLICATE_TRUTH_ASSESSMENT.md        ← overlap + duplicate risk
│
├── evidence/
│   ├── postgres_queries/      ← exact SQL run during discovery
│   └── query_results/         ← recorded outputs of that SQL
│
├── architecture_review/
│   ├── OPTION_A_REUSE_EXISTING.md
│   ├── OPTION_B_EXTEND_EXISTING.md
│   ├── OPTION_C_SEPARATE_SYSTEM.md
│   └── FINAL_ARCHITECTURE_DECISION.md       ← decision: OPTION B
│
├── validation/
│   ├── COVERAGE_MATRIX.md      ← L1–L5 mapped to existing coverage
│   ├── QUERYABILITY_CHECK.md   ← can each analysis actually be queried?
│   └── VALIDATION_RESULT.md    ← overall PASS/FAIL
│
└── closure/
    └── DAILY_CLOSURE_REPORT.md ← what was done today, what is next
```

---

## Headline findings (evidence-backed)

- The database **GREEN / PASS** — all 5 analyses can be executed from existing tables and views.
- An existing **daily SKU-level leakage engine** already exists in `development` (3 tables + 3 views) but it is
  **30-day, SKU-level, internal** — it is not the weekly, 7-day, PH-facing protocol.
- The existing engine **partially covers L2 and L3**, and **does not cover L1, L4, L5** at all.
- The existing engine has **404 OPEN / 0 CLOSED** records — it has **no closure feedback loop**.
- Recommended architecture: **OPTION B — extend / build a weekly report layer on top of the existing
  framework** (reuse the profitability views, reuse the pattern taxonomy, add the 3 missing analyses and the
  weekly closure loop).

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Top-level navigation and summary for the investigation workspace |
| Business Question Supported | "Can the current PostgreSQL database support all 5 leakage analyses, and how should the weekly protocol be delivered without duplicate truth?" |
| Evidence Used | All Phase 1 + Phase 2 discovery queries (see `evidence/`) |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE (discovery + decision); implementation pending sign-off |
| Pass/Fail Rule | PASS if a new developer can navigate the workspace and locate every finding's evidence |
| Next Step | Bietrick reviews `FINAL_ARCHITECTURE_DECISION.md` and signs off OPTION B before any build |
| Known Limitations | Documents the state of the database as observed on 2026-06-22 only; live data changes daily |
