# START HERE

**If you read nothing else, read this page.** It tells a brand-new developer what was investigated,
what was found, where the evidence lives, and what happens next.

---

## 60-second summary

We were asked: **"Can the live PostgreSQL database support the 5 weekly leakage analyses, and should the
Weekly Leakage Protocol reuse, extend, or replace what already exists?"**

We did **discovery only** — no tables created, no data changed, no logic built. We found:

1. The data exists. All 5 analyses (L1–L5) can be run today. Overall status: **GREEN / PASS**.
2. A leakage engine **already exists** in the `development` schema — 3 tables and 3 views — but it is a
   **daily, 30-day-window, SKU-level, internal monitoring engine**, not the **weekly, 7-day, PH-facing
   action protocol** Bietrick needs.
3. The existing engine **partially covers L2 (shipping) and L3 (net-negative)**; it **does not cover
   L1 (zero-conv PPC), L4 (refund rate), or L5 (PH margin trend)**.
4. The existing engine has **404 OPEN and 0 CLOSED** records — it detects but never closes. There is **no
   accountability/verification loop**.
5. Recommended architecture: **OPTION B** — build a weekly report layer **on top of** the existing
   framework. Reuse the profitability views and the pattern taxonomy; add the 3 missing analyses; add the
   weekly closure loop.

---

## Reading order

Read the documents in this sequence. Each one builds on the previous.

| # | Document | Answers the question |
|---|----------|----------------------|
| 1 | `requirements/REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md` | What does the protocol actually demand? |
| 2 | `discovery/PHASE1_EXISTING_ASSET_SCAN.md` | What data assets already exist? |
| 3 | `discovery/SOURCE_OBJECT_INVENTORY.md` | What are the exact tables and views, and how do they join? |
| 4 | `discovery/PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md` | What does the existing leakage engine actually do? |
| 5 | `discovery/DUPLICATE_TRUTH_ASSESSMENT.md` | Where would the weekly protocol collide with what exists? |
| 6 | `validation/COVERAGE_MATRIX.md` | Which of L1–L5 are already covered (FULL/PARTIAL/MISSING)? |
| 7 | `validation/QUERYABILITY_CHECK.md` | Can each analysis actually be queried from live data? |
| 8 | `validation/VALIDATION_RESULT.md` | Overall: does discovery PASS? |
| 9 | `architecture_review/OPTION_A_REUSE_EXISTING.md` | Could we just reuse what exists? |
| 10 | `architecture_review/OPTION_B_EXTEND_EXISTING.md` | Could we extend what exists? |
| 11 | `architecture_review/OPTION_C_SEPARATE_SYSTEM.md` | Could we build a separate system? |
| 12 | `architecture_review/FINAL_ARCHITECTURE_DECISION.md` | Which option was chosen and why? |
| 13 | `closure/DAILY_CLOSURE_REPORT.md` | What was completed today and what is the next action? |

Evidence for every claim lives in `evidence/postgres_queries/` (the SQL) and `evidence/query_results/`
(the recorded outputs). Each discovery document cites the evidence file it relies on.

---

## What you may and may not do next

**Permitted (this investigation's outputs):** read, review, and sign off the architecture decision.

**Not yet permitted (requires Bietrick sign-off on OPTION B first):**
- Creating any new table, view, or function
- Inserting or modifying any record
- Building the weekly HTML report generator
- Wiring the protocol into the existing `leakage_detection` / `leakage_classification` tables

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Onboarding entry point; defines reading order and current state |
| Business Question Supported | "Where do I start and what do I need to know?" |
| Evidence Used | Summarises all Phase 1 + Phase 2 evidence (see `evidence/`) |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE |
| Pass/Fail Rule | PASS if a new developer can, after this page, navigate the workspace unaided |
| Next Step | Proceed to `requirements/REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md` |
| Known Limitations | Reflects state as of 2026-06-22; does not track later data changes |
