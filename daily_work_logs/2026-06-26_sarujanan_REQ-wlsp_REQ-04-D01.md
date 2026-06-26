# DAILY REQUIREMENT DOCUMENT

---

# 1. Metadata Block

| Field                            | Value                                                                                          |
| -------------------------------- | ---------------------------------------------------------------------------------------------- |
| daily_requirement_submitted_date | 2026-06-26                                                                                     |
| expected_deadline_date           | 2026-06-26                                                                                     |
| end_user                         | Bietrick / WLSP Project Team                                                                   |
| expected_roi                     | Permanent dashboard accuracy, automated refresh reliability, reduced manual validation effort  |
| developer                        | Sarujanan                                                                                      |
| project                          | AIOS Weekly Leakage Identification                                                             |
| project_code                     | WLSP                                                                                           |
| phase                            | Phase-01 – Dashboard Hardening & Refresh Automation                                            |
| requirement_id                   | REQ-01                                                                                         |
| deliverable_id                   | REQ-04                                                                                    |
| blos_keys                        | Amazon Only, COUNT(DISTINCT ASIN), No UNATTRIBUTED, Single-Pass Refresh, Regression Validation |
| domain                           | Business Intelligence – Weekly Leakage Dashboard                                               |

---

# 2. Today Requirement Block

## 2.1 Task Name

Dashboard Refresh Validation and Production Readiness

---

## Business Purpose

Complete the remaining work required to make the Weekly Leakage Dashboard production-ready.

Ensure every scheduled refresh always produces the same verified dashboard without introducing marketplace contamination, incorrect counts, or stale data.

---

## Source Information

### Source System

AIOS PostgreSQL (via Claude MCP)

### Tables

* public.ppc_performance
* public.order_transaction
* public.order_shipping_billing_detail
* public.amazon_returns
* daily_task.tbl_wlsp_sarujanan

---

## Filter Conditions

Marketplace:
Amazon UK Only

PPC Source:

source_name ILIKE '%amazon%'

Date Range:

* L1–L3 → Last 7 Days
* L4 → Last 30 Days
* L5 → Last 3 Months

---

## Required Data Output

| Field            | Purpose                |
| ---------------- | ---------------------- |
| ASIN             | Product identification |
| SKU              | Product identification |
| Portfolio Holder | Owner mapping          |
| Account          | Amazon account         |
| Revenue          | Business KPI           |
| Shipping Cost    | Leakage detection      |
| PPC Cost         | Leakage detection      |
| Refund Rate      | Leakage analysis       |
| Margin           | Margin trend           |
| L1–L5 Counts     | Dashboard KPI          |

---

# 3. Business Logic Block

## Purpose

Validate that the dashboard refresh permanently preserves all approved D04 business rules.

---

### Rule 1

All PPC calculations must use

source_name ILIKE '%amazon%'

---

### Rule 2

Exclude

* EBAY
* SHOPIFY
* so_926407

from every dashboard calculation.

---

### Rule 3

Exclude

UNATTRIBUTED

from

* PH Summary
* PH Cards
* Sidebar
* Rankings
* Dropdown

L1 investigation rows may still retain UNATTRIBUTED.

---

### Rule 4

L1 KPI must always equal

COUNT(DISTINCT ASIN)

---

### Rule 5

Dashboard refresh must regenerate

* summary.counts
* account_summary
* ph_summary
* l1
* l2
* l3
* l4
* l5

using one execution pass.

---

### Rule 6

Refresh validation must fail automatically if

* EBAY detected
* SHOPIFY detected
* so_926407 detected
* UNATTRIBUTED detected in ph_summary
* L1 count differs from COUNT(DISTINCT ASIN)

---

# 4. Data Enrichment Block

## Purpose

Collect supporting validation evidence proving that the regenerated dashboard matches the PostgreSQL source.

---

## Sources

* dashboard_refresh_prompt.md
* refresh_dashboard.py
* leakage_dashboard.html
* PostgreSQL MCP queries

---

## Required Evidence

| Field               | Reason                  |
| ------------------- | ----------------------- |
| Dashboard Counts    | KPI validation          |
| L1 Detail           | Verify distinct ASIN    |
| Account Summary     | Count reconciliation    |
| PH Summary          | Assigned PH validation  |
| Refresh Log         | Automation verification |
| Validation Report   | Production readiness    |
| CSV Output          | Daily evidence          |
| Skill File          | Knowledge capture       |
| PostgreSQL Activity | Daily tracking          |

---

# 5. Expected Deliverables

Today's work is complete only when the following exist:

* Updated dashboard_refresh_prompt.md
* Updated refresh_dashboard.py
* Validated leakage_dashboard.html
* Refresh validation report
* Daily CSV
* Daily Skill file
* PostgreSQL activity update
* Supporting evidence
* PASS/FAIL report

---

# 6. Success Criteria

The dashboard is considered production-ready only if all checks pass.

| Validation          | Expected Result |
| ------------------- | --------------- |
| L1                  | 125             |
| L2                  | 212             |
| L3                  | 17              |
| L4                  | 33              |
| L5                  | 9               |
| Amazon Only         | PASS            |
| No EBAY             | PASS            |
| No SHOPIFY          | PASS            |
| No so_926407        | PASS            |
| No UNATTRIBUTED     | PASS            |
| Distinct ASIN KPI   | PASS            |
| Single-Pass Refresh | PASS            |
| Regression Guards   | PASS            |

---

# 7. Final Output Required

Produce:

1. Validation Report
2. Evidence Report
3. Updated CSV
4. Updated Skill File
5. PostgreSQL Activity Record
6. Production Readiness Summary
7. PASS / FAIL Status
