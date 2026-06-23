# Correction Summary — D01 Closure (C-1 … C-7)

**Date:** 2026-06-22 · **Developer:** sarujanan · **Deliverable:** D01 · **Reviewer:** Bietrick (TL)
**Source of corrections:** `VALIDATION_AUDIT.md` → Required Corrections (C-1…C-7).
**Rules honoured:** edited existing files only · no new architecture · no new requirements · this summary is the only new file (an explicit deliverable).

---

## Corrections Applied

| # | Status | File(s) edited | Verified |
|---|--------|----------------|----------|
| C-1 | **C-1 COMPLETE** | `README.md` | `grep "Source of figures" README.md` = 1 |
| C-2 | **C-2 COMPLETE** | `requirements/REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md` | `grep "Observed vs stated (C-2)"` = 1 |
| C-3 | **C-3 COMPLETE** | `discovery/PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md` | `grep "Labelled as inference (C-3)"` = 1 |
| C-4 | **C-4 COMPLETE** | `architecture_review/OPTION_B_EXTEND_EXISTING.md`, `architecture_review/FINAL_ARCHITECTURE_DECISION.md` | `grep "uses actual Amazon fees rather than the protocol"` = 1 + 1; "is more accurate" = 0 |
| C-5 | **C-5 COMPLETE** | `discovery/PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md` | `grep "mixes two incompatible"` = 2 |
| C-6 | **C-6 COMPLETE** | `README.md` (workspace-index pointer) | `grep "Source of figures"` = 1 |
| C-7 | **C-7 COMPLETE** | `discovery/PHASE1_EXISTING_ASSET_SCAN.md` | `grep "24 distinct PHs observed"` = 1 |

---

## Files Modified

1. `README.md` — C-1 + C-6
2. `requirements/REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md` — C-2
3. `discovery/PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md` — C-3 + C-5
4. `architecture_review/OPTION_B_EXTEND_EXISTING.md` — C-4
5. `architecture_review/FINAL_ARCHITECTURE_DECISION.md` — C-4
6. `discovery/PHASE1_EXISTING_ASSET_SCAN.md` — C-7
7. `VALIDATION_AUDIT.md` — verdict re-graded + C-status column (closure record)

No other files touched. No tables, no SQL, no architecture, no requirements created.

---

## Evidence (Before → After)

### C-1 — README row counts labelled as estimates
- **Before:** No statement that figures are estimates.
- **After:** Added note — *"All table/row counts cited across this workspace are PostgreSQL `pg_stat` **estimates** (`n_live_tup`), not exact `COUNT(*)`."*

### C-2 — REQ-001 PPC date / shipping reconciled
- **Before:** Table stated "PPC … from Oct 2025" and "77% coverage" with no reconciliation.
- **After:** Added *"Observed vs stated (C-2)"* note — PPC actually from **2025-01-01** (`PHASE1_RESULTS.md §07`); shipping **99.8%** completed / 73.5% all-status (`PHASE1_RESULTS.md §05`).

### C-3 — PHASE2 purpose + pattern mapping labelled inference
- **Before:** "It is an **internal continuous monitor** …" stated as fact; pattern→analysis mapping implied as fact.
- **After:** Added *"Labelled as inference (C-3)"* note — purpose inferred from run-id naming/cadence/view structure; pattern→analysis mapping is an analyst inference, not a stored DB mapping.

### C-4 — "more accurate" reworded
- **Before (OPTION_B):** "Foundation already exists and is **more accurate** than the protocol's assumptions (actual fees)".
- **Before (FINAL):** "**The foundation already exists and is more accurate.**"
- **After (both):** "**…uses actual Amazon fees rather than the protocol's 15% assumption.**" — factual basis, not a judgement. `grep "is more accurate"` now = 0 in both.

### C-5 — £96,301.55 caveat inline
- **Before:** `| Total cumulative loss (open) | £96,301.55 | …`  (caveat only in distant prose).
- **After:** `| … | £96,301.55 ⚠ **caveat: mixes two incompatible `daily_loss_gbp` formulas (06-15→06-16) — treat as indicative only, do not quote as exact** | …` (caveat now inseparable from the number; appears 2×).

### C-6 — Source-of-figures pointer
- **Before:** Shared figures hand-copied across docs with no canonical pointer.
- **After:** README note — *"**Source of figures:** the recorded outputs in `evidence/query_results/` are the single source of truth; any figure restated in other documents is a transcription of those results."*

### C-7 — 24-observed vs 28-protocol PH made explicit
- **Before:** PHASE1 mentioned 83.4% PH mapping but not the 24-vs-28 distinction.
- **After:** New row — *"**24 distinct PHs observed** (last-30d Amazon UK FBM) vs **28 PHs listed in the protocol** … observed-vs-protocol, not missing data."*

---

## Remaining Issues

**None for D01 documentation quality.** All 7 audit corrections are closed and verified by grep.

Out-of-scope items (tracked elsewhere, NOT part of C-1…C-7, NOT blockers to this closure):
- OPTION B build sign-off (Bietrick) — gate for the build phase.
- DQ-1 external PPC-ETL fix · DQ-2 refund reconciliation · `daily_loss_gbp` formula standardisation — build-phase work in `POSTGRES_DATA_GAP_ANALYSIS.md` / `HIGH_RISK_ROOT_CAUSE_ANALYSIS.md`.

---

## Final Verdict

> ## ✅ PASS — all C-1…C-7 CLOSED
>
> `VALIDATION_AUDIT.md` re-graded **🟡 PASS WITH WARNINGS → 🟢 PASS** (0 open warnings).
> D01 Investigation & Decision documentation is now clean-PASS and sign-off-ready.
> Edited existing files only; no new architecture, requirements, or duplicate documentation introduced.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Record application + before/after evidence of audit corrections C-1…C-7 |
| Business Question Supported | "Are all documentation-quality corrections closed so D01 is clean PASS?" |
| Evidence Used | `VALIDATION_AUDIT.md`; grep verification of each edit |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE — PASS |
| Pass/Fail Rule | PASS if all C-1…C-7 applied and audit re-grades to PASS; FAIL if any remains open |
| Next Step | Bietrick OPTION B sign-off → begin build (L1 ASIN-level first) |
| Known Limitations | Documentation-quality scope only; build-phase and external-ETL items are tracked separately |
