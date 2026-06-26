# Daily Requirement Document

## 1. Metadata Block

| Field                            | Value                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------- |
| daily_requirement_submitted_date | 2026-06-25                                                                            |
| expected_deadline_date           | 2026-06-25                                                                            |
| end_user                         | Bietrick / PH Team                                                                    |
| expected_roi                     | Automated weekly leakage identification and reporting; reduced manual analysis effort |
| developer                        | sarujanan                                                                             |
| project                          | AIOS Weekly Leakage Identification                                                    |
| project_code                     | WLSP                                                                                  |
| phase                            | Phase-04 - Dashboard Validation & Data Quality Investigation                          |
| requirement_id                   | DP-WLSP-REQ-01                                                                        |
| deliverable_id                   | D04                                                                                   |
| blos_keys                        | L1-L5 calculations must come directly from source tables; no leakage table dependency |
| domain                           | Amazon FBM - Leakage Detection - Portfolio Holder Management                          |

---

# 2. Today Requirement Block

## 2.1 Today Requirement

### Task Name

Dashboard Validation and Data Attribution Audit

### Business Purpose

Validate that the WLSP dashboard is displaying accurate business data and identify any data-quality or attribution issues before the dashboard is released to Portfolio Holders.

---

## Source Information

### Source System

PostgreSQL (via MCP)

### Tables

* public.ppc_performance
* public.order_transaction
* public.order_shipping_billing_detail
* public.amazon_returns

### Dashboard Sources

* dashboard/index.html
* dashboard/data.js

---

## Validation Scope

### Account Validation

Verify:

* LEDSone UK
* DCVoltage UK
* so_926407

Confirm:

* Actual source counts
* Dashboard counts
* Reconciliation differences

---

### Portfolio Holder Validation

Investigate:

* UNATTRIBUTED

Determine:

* Why it appears
* Which source records generate it
* Whether PH mapping exists
* Whether mapping can be recovered

---

### Dashboard Validation

Validate:

* Account sidebar counts
* Portfolio Holder counts
* L1 counts
* L2 counts
* L3 counts
* L4 counts
* L5 counts

Compare dashboard values against direct source-table calculations.

---

# 3. Business Logic Block

## Purpose

Confirm that dashboard values match source calculations.

### Rule 1

IF dashboard count = source calculation

THEN validation_status = PASS

ELSE

validation_status = FAIL

---

### Rule 2

IF PH value IS NULL

THEN classification = UNATTRIBUTED

---

### Rule 3

IF PH can be identified from another source

THEN classification = MAPPING_ERROR

ELSE

classification = MISSING_SOURCE_DATA

---

# 4. Data Enrichment Block

## Purpose

Collect additional information for UNATTRIBUTED records.

### Source Tables

* public.ppc_performance
* public.order_transaction

### Required Data

| Field       | Reason                 |
| ----------- | ---------------------- |
| ASIN        | Product identification |
| SKU         | Product identification |
| Account     | Ownership validation   |
| PH Name     | Attribution validation |
| Spend       | L1/L3 validation       |
| Revenue     | L2/L3 validation       |
| Shipping    | L2 validation          |
| Refund Rate | L4 validation          |

---

# 5. Required Deliverables

### D04-A

Account Validation Report

Contents:

* Account list
* Counts
* Reconciliation status
* PASS / FAIL

---

### D04-B

UNATTRIBUTED Investigation Report

Contents:

* Root cause
* Affected records
* Missing mappings
* Recommended fix

---

### D04-C

Dashboard Validation Report

Contents:

* Dashboard values
* Direct source values
* Variance analysis
* PASS / FAIL

---

# 6. Evidence Required

* MCP SQL queries
* Query results
* Dashboard screenshots
* Validation report
* Root-cause analysis

---

# 7. Current Status

D01 - Complete ✅

D02 - Complete ✅

D03 - Complete ✅

D04 - In Progress 🔄

---

# 8. Final Assessment

Today's objective is NOT to build new calculations.

Today's objective is to validate:

* Dashboard accuracy
* Account attribution
* Portfolio Holder attribution
* UNATTRIBUTED root cause

before the dashboard is considered business-ready.
