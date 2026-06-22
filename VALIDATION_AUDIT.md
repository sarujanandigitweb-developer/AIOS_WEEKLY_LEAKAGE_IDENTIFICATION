# VALIDATION AUDIT — Documentation Quality

**Audit date:** 2026-06-22 · **Auditor:** AIOS Worker (documentation audit role) · **Reviewer:** Bietrick (TL)
**Scope:** every markdown file in `AIOS_Weekly_Leakage_Identification/`
**Rules honoured:** no existing file changed · no implementation logic · no new SQL · documentation quality only.
**Method:** each statement cross-checked against the two recorded result files
(`evidence/query_results/PHASE1_RESULTS.md`, `PHASE2_RESULTS.md`) and the SQL in `evidence/postgres_queries/`.

**Overall result: 🟡 PASS WITH WARNINGS**

The documentation is well-evidenced and traceable. No fabricated facts were found. Warnings arise because
(a) several headline numbers are `pg_stat` **estimates** stated in places as if exact, and (b) a set of
**interpretive/inferred** statements (framework purpose, pattern→analysis mapping, "more accurate", risk
ratings, architecture choice) are reasonable and evidence-anchored but are **judgements, not direct query
output**, and are not always labelled as such.

---

## Evidence Verified

Statements below trace directly to recorded PostgreSQL output.

| Statement | Where used | Evidence (query → result) | Source object |
|-----------|-----------|---------------------------|---------------|
| 3 leakage tables exist with counts 404 / 343 / 7 | README, Phase1, Phase2 | `08` → PHASE2_RESULTS §08 (`COUNT(*)`) | `development.leakage_*` |
| Detection status = **404 OPEN / 0 CLOSED** | README, Phase2, Coverage, Closure | `08` → PHASE2_RESULTS §08 | `leakage_detection` |
| Every `pattern_id` is NULL; patterns never triggered | Phase2 | `09` → PHASE2_RESULTS §09 | `leakage_detection`, `leakage_pattern_registry` |
| Root-cause mix: PRICE_TOO_LOW 178, SHIPPING_HIGH 148, FEE_ANOMALY 15, PAID_MEDIA_BLEED 2, RETURNS_ISSUE 0 | Phase2, Coverage | `10` → PHASE2_RESULTS §10 | `leakage_classification` |
| SHIPPING_HIGH uses 25% threshold (e.g. "78.3% > 25.0%") | Phase2, Coverage, DupTruth | `12` → PHASE2_RESULTS §12 | `leakage_classification` |
| PAID_MEDIA_BLEED is ACOS-based ("PPC 643.3% > 30.0%"), 2 rows / 1 SKU | Phase2, Coverage, OptionA | `11` → PHASE2_RESULTS §11 | `leakage_classification`/`leakage_detection` |
| `daily_loss_gbp` formula changes 06-15→06-16 (0.18→11.58→50.08) | Phase2, FinalDecision, Validation | `13` → PHASE2_RESULTS §13 | `leakage_detection` |
| Detected-SKU vs active-7d-PPC overlap = 2 of 94 | Phase2, Coverage, DupTruth | `14` → PHASE2_RESULTS §14 | `leakage_detection` × `ppc_performance` |
| Shipping join coverage = 73.5% (last 30d) | all coverage refs | `05` → PHASE1_RESULTS §05 | `order_transaction`×`order_shipping_billing_detail` |
| PH mapping = 83.4%, 24 distinct PHs | Phase1, Queryability | `04b` → PHASE1_RESULTS §04 | `order_transaction` |
| `shipping_template_price` only 3.7% populated | Phase1, Queryability, Coverage | `05` → PHASE1_RESULTS §05 | `order_shipping_billing_detail` |
| `ppc_performance.ref_id` = ASIN; `record_type='ad'` grain | SourceInventory, Phase1 | `04` → PHASE1_RESULTS §04 | `ppc_performance` |
| `ss_name` has 8 account spellings | SourceInventory, Queryability | `04` → PHASE1_RESULTS §04 | `ppc_performance` |
| NNR snapshot has only 1 date (2026-06-17) | Phase1, DupTruth | `06` → PHASE1_RESULTS §06 | `fbm_sku_daily_nnr_snapshot` |
| L1 / L4 / L5 return real rows from live data | Queryability, Validation | Phase 1 live probes → PHASE1_RESULTS "Live feasibility probes" | `ppc_performance`, `order_transaction` |
| 3 `development` views exist with stated definitions (actual fees, 20% COGS, 120d/30d) | SourceInventory, Phase2, OptionB | `pg_views` capture → PHASE2_RESULTS "Supporting views" | `vw_fbm_uk_*`, `vw_top_10_leakage` |
| Leakage/report asset search hit list (3 dev tables + 3 staging) | Phase1 | `01` → PHASE1_RESULTS §01 | `information_schema.tables` |

---

## Evidence Missing

Statements with **no recorded query proof** in `evidence/`. None are fabricated, but they are not provable from
the captured results and should be labelled or down-scoped.

| # | Statement | File(s) | Why it lacks proof | Severity |
|---|-----------|---------|--------------------|----------|
| EM-1 | "£96,301.55 cumulative loss" | Phase2 (§3) | The SUM was observed (PHASE2_RESULTS §09) **but** the doc itself states the underlying formula is inconsistent — so the number is recorded yet **not trustworthy**. Cited correctly with caveat, but the figure should never be reused without the caveat. | LOW |
| EM-2 | "`ppc_performance` PPC from Oct 2025" (REQ-001 §4) | requirements | Transcribed from the protocol PDF; the actual query (PHASE1_RESULTS §07) shows UK data from **2025-01-01**. The two disagree and the doc does not reconcile them. | MEDIUM |
| EM-3 | "amazon_returns … 6 months of history" implied by protocol | (not asserted in docs, but adjacent) | Observed range is 2026-01-01→2026-06-17 only (PHASE1_RESULTS §03). No doc over-claims this, but a reader comparing to the protocol PDF may assume more. | LOW |
| EM-4 | "404 detections span 14 PHs" / "distinct PHs flagged 14" | Phase2 (§3) | Verified by `08` summary (distinct count) — **actually present**; listed here only to flag that the *named* PH lists elsewhere are samples, not full enumerations. | LOW |
| EM-5 | Expected frequencies (50–120 / 80–200 / 30–80 / 20–50 ASINs) | REQ-001 | Come from the protocol PDF, **not** from any query. Correctly attributed to the protocol, but they are predictions, not measured counts. | LOW (attributed) |

---

## Assumptions

Assumptions and inferences carried in the documentation. All are reasonable; the warning is that several are
**not labelled as inference** at point of use.

| # | Assumption / inference | File(s) | Basis | Labelled as inference? |
|---|------------------------|--------|-------|------------------------|
| A-1 | Row counts are facts | README, Phase1, SourceInventory | They are `pg_stat_user_tables.n_live_tup` **estimates** (`02`), not `COUNT(*)` | Partially — labelled "Est. rows" in tables, but README prose reads as exact |
| A-2 | "Why the framework exists" — a daily internal monitor | Phase2 (§1) | Inferred from run-id naming, cadence, and view structure; no DB comment states purpose | No |
| A-3 | Pattern classes map to analyses (PAID_MEDIA_RUNAWAY→L1/L3, SHIPPING_HIGH→L2, RETURNS_ISSUE→L4) | Phase2, OptionB, FinalDecision | Inferred from names + thresholds; no stored mapping exists | No |
| A-4 | `vw_fbm_uk_order_profitability` is "more accurate" than protocol's 15% | OptionB, FinalDecision | True that it uses actual fees (view def); "more accurate" is a judgement | No |
| A-5 | Duplicate-truth risk ratings (MEDIUM / LOW) | DupTruth | Analyst judgement over overlap evidence; not a measured metric | Partially (method described) |
| A-6 | "No closure feedback loop" | README, Phase2, FinalDecision | Inferred from 0 CLOSED (verified) — strong inference, not a stated DB fact | No |
| A-7 | OPTION B recommendation | FinalDecision, OptionB | Reasoned conclusion over all evidence; inherently a judgement | Yes (framed as decision) |
| A-8 | COGS 20% / fee 15% / VAT 20% | REQ-001, Queryability, Validation | Stated assumptions inherited from the protocol PDF | Yes |
| A-9 | "24 PHs (observed) vs 28 PHs (protocol)" | Phase1 prose / discovery summary | 24 is measured (`04b`); 28 is from PDF — must not be conflated | Partially |

---

## Duplicate Truth Risk

Does any **document** create a *new* truth source instead of referencing evidence?

| Document | Creates new truth? | Assessment |
|----------|--------------------|------------|
| `evidence/query_results/PHASE1_RESULTS.md`, `PHASE2_RESULTS.md` | **These ARE the truth source of record** | Correct — they are the captured outputs; everything else must reference them. ✅ |
| Discovery docs (Phase1/Phase2/SourceInventory/DupTruth) | No | They cite evidence file numbers and restate results. ✅ |
| `COVERAGE_MATRIX.md`, `QUERYABILITY_CHECK.md` | No | Reference evidence + probes. ✅ |
| `VALIDATION_RESULT.md` | No | Aggregates other docs. ✅ |
| Architecture docs | No | Reason over cited evidence; no new facts. ✅ |
| **Numbers restated in multiple docs** (e.g. 404/0, 73.5%, 3.7%) | **Mild risk** | The same figures are hand-copied into README, Phase docs, Coverage, Validation. If one source figure is later corrected, the copies will drift. This is *transcription duplication*, not contradictory truth — but it is the one place the workspace could develop inconsistency. ⚠️ |

**Finding:** No document fabricates a competing fact. The only duplicate-truth exposure is **figure
transcription** — key numbers live in 4–5 files by copy rather than by single-reference. Recommend that
`evidence/query_results/` remain the sole source and other docs point to it (already the stated intent in
README principle #2; just not enforced mechanically).

---

## Queryability Review

**Can a new developer trace every conclusion back to: SQL file · query result file · source object?**

| Conclusion class | SQL file | Result file | Source object | Traceable? |
|------------------|----------|-------------|---------------|-----------|
| Existence of assets | `01` | PHASE1_RESULTS §01 | `information_schema` | YES |
| Table shape + counts | `02` | PHASE1_RESULTS §02 | named tables | YES (counts = estimates) |
| Data-quality % (shipping/PH/template) | `03_to_07` | PHASE1_RESULTS §03–07 | named tables | YES |
| Leakage engine facts | `08_to_14` | PHASE2_RESULTS §08–14 | `development.leakage_*` | YES |
| View behaviour | `pg_views` capture | PHASE2_RESULTS "views" | `vw_fbm_uk_*` | YES |
| L1/L4/L5 feasibility | (inline probes) | PHASE1_RESULTS "Live probes" | `ppc_performance`,`order_transaction` | YES |
| **Interpretive conclusions** (purpose, pattern map, OPTION B) | — | — | reasoned over above | **PARTIAL** — trace to evidence *via reasoning*, not a single query |

**Answer: YES** for all measured facts (every one maps to SQL file + result file + source object).
**PARTIAL** for interpretive conclusions — they are correctly grounded in cited evidence but, by nature, do
not map to one query. This is expected for architecture judgements and is not a defect, provided they remain
labelled as judgements (see Required Corrections).

---

## Required Corrections

Listed for action; **not applied** (audit-only). All are clarity/labelling fixes — no factual errors found.

| # | File | Correction | Priority |
|---|------|-----------|----------|
| C-1 | `README.md` | State row counts as **estimates** (`pg_stat`), matching the "Est. rows" labelling used in the discovery tables. | MEDIUM |
| C-2 | `requirements/REQ-001_WEEKLY_LEAKAGE_PROTOCOL.md` | Add a note reconciling protocol "PPC from Oct 2025" with observed UK data from 2025-01-01 (EM-2). | MEDIUM |
| C-3 | `discovery/PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md` | Label §1 "Why the framework exists" explicitly as **inference** (A-2); same for the pattern→analysis mapping (A-3). | MEDIUM |
| C-4 | `architecture_review/OPTION_B_EXTEND_EXISTING.md`, `FINAL_ARCHITECTURE_DECISION.md` | Reword "more accurate" (A-4) to the factual basis: "uses actual Amazon fees rather than the protocol's 15% assumption." | LOW |
| C-5 | `discovery/PHASE2_LEAKAGE_FRAMEWORK_REVIEW.md` | Where £96,301.55 appears, keep the caveat inline every time the figure is cited (EM-1). Already caveated once; make it inseparable from the number. | LOW |
| C-6 | All docs restating shared figures | Add a one-line "Source of figures: `evidence/query_results/`" pointer to discourage transcription drift (Duplicate Truth finding). | LOW |
| C-7 | `discovery/PHASE1_EXISTING_ASSET_SCAN.md` | Ensure "24 PHs (observed) vs 28 (protocol)" distinction is explicit wherever PH counts appear (A-9). | LOW |

---

## Verdict

> ## 🟡 PASS WITH WARNINGS
>
> - **No fabricated facts.** Every measured claim traces to a recorded query result and a named source object.
> - **Warnings:** (1) estimate-vs-exact labelling on row counts; (2) interpretive statements (framework
>   purpose, pattern mapping, "more accurate", OPTION B) not always flagged as judgement; (3) one
>   protocol-vs-observed date discrepancy unreconciled (EM-2); (4) shared figures duplicated by transcription
>   across files.
> - **None are blocking.** All 7 required corrections are clarity/labelling, not factual fixes.
> - **Queryability: YES** for all measured facts; **PARTIAL** (by design) for architecture judgements.
>
> The investigation documentation is fit for Bietrick's review and sign-off. Apply C-1…C-7 before the build
> phase to reach a clean PASS.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Independent documentation-quality audit of the investigation workspace |
| Business Question Supported | "Is every documented conclusion evidence-backed and traceable?" |
| Evidence Used | All workspace markdown + `evidence/postgres_queries/` + `evidence/query_results/` |
| Reviewer | Bietrick (TL) |
| Status | COMPLETE — PASS WITH WARNINGS |
| Pass/Fail Rule | PASS if no fabricated facts and all measured claims are traceable; WARNINGS if labelling/clarity gaps remain; FAIL if any conclusion is unsupported by evidence |
| Next Step | Apply corrections C-1…C-7 (separate edit pass, on approval); then Bietrick sign-off on OPTION B |
| Known Limitations | Audit covers documentation only as of 2026-06-22; it re-runs no SQL and assumes the recorded result files faithfully capture the live outputs |
