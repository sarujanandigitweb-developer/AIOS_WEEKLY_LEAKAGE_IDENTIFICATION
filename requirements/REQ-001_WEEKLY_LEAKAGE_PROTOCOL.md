# REQ-001 — Weekly Leakage Identification & Stop-Loss Protocol

**Source document:** `Bietrick_Weekly_Leakage_Protocol_v2.pdf` (Leakage Protocol v2.0, June 2026)
**Owner:** Bietrick (TL)
**Scope:** UK Amazon FBM — all PHs under Bietrick · LEDSone UK + DCVoltage UK accounts

---

## 1. Business intent

Give Bietrick an exact, repeatable **weekly** process to identify where money is leaking from UK Amazon FBM
portfolios and issue **same-day stop-loss instructions** to his PH team, at **ASIN / SKU / account / PH**
granularity, with **no dashboard dependency**. The protocol asserts £800–£1,500/week of identifiable leakage
continues unchecked each week it is not executed.

---

## 2. The 5 required analyses

| ID | Name | Window | Flag condition | Expected frequency | Action |
|----|------|--------|----------------|--------------------|--------|
| **L1** | ASIN PPC Spend — Zero Conversions | 7 days | `SUM(spend) > £3 AND SUM(conversions) = 0` | 50–120 ASINs | PAUSE PPC immediately |
| **L2** | Shipping Exceeds 25% of Revenue | 7 days | `shipping_cost > 25% of revenue` (+ additional shipping template) | 80–200 ASINs | Increase price / switch carrier / discontinue |
| **L3** | Net-Negative ASINs Still Receiving PPC | 7 days | `(revenue × 0.45) − shipping − PPC < £0 AND PPC > £5` | 30–80 ASINs | PAUSE PPC immediately |
| **L4** | High Refund Rate ASINs | 30 days | `refunded ÷ total > 10%`, min 2 orders | 20–50 ASINs | Investigate listing/quality/packaging |
| **L5** | PH Net Margin Trend — Consecutive Decline | 3 full months | margin declining ≥ 2 consecutive months; `Net = revenue − (revenue × 0.55) − shipping − PPC` | per-PH | 15-min review with PH |

---

## 3. Required output fields (per flagged ASIN)

ASIN code (with LEDSone UK / DCVoltage UK account tag) · SKU code · problem type · the numbers
(spend/loss/refund rate as applicable) · exact instruction (PAUSE PPC / INCREASE PRICE / INVESTIGATE /
DISCONTINUE) · deadline (Wednesday EOD). Grouped **by PH**. Delivered as an interactive **HTML report** with
sidebar, tabs, tick system, ASIN colour tags, equations shown; each PH sees only their own flagged ASINs.

---

## 4. Stated data reality (from protocol §5)

| Data point | Status | Note |
|------------|--------|------|
| Revenue (`item_price × quantity`) | ACTUAL | 95%+ populated |
| Shipping cost (`carrier_charge`) | ACTUAL | 77% coverage UK (stated) |
| PPC spend / conversions / impressions / clicks | ACTUAL | from Oct 2025 |
| Order status | ACTUAL | Completed / Cancelled / Refunded |
| PH owner (`user_name`) | ACTUAL | 80%+ mapped for Amazon UK |
| SKU / ASIN / Account (`ss_name`) / Order ID | ACTUAL | both accounts shown |
| COGS / Platform fee / VAT | **ASSUMED** | 20% / 15% / 20% — not in database |

Protocol explicitly accepts that absolute net carries a margin of error but **relative comparisons remain
directionally accurate**.

---

## 5. Explicit non-goals (protocol §9)

The protocol does **not** replace the BLOS system, the full HIPS 7-layer calculation, or the automated agent
pipeline. It does **not** automate PPC pausing (manual action), provide exact true net profit, or cover eBay /
Shopify / non-FBM channels.

---

## 6. Verification requirement (protocol §7)

Every weekly action list must be verified **the following Monday**: confirm PPC was paused, leakage stopped,
or escalate non-compliance. This implies a **closure/feedback loop** is part of the requirement.

---

## Document control

| Field | Value |
|-------|-------|
| Purpose | Capture, verbatim and structured, what the protocol requires so all downstream work traces to a requirement |
| Business Question Supported | "What exactly must the weekly leakage solution deliver?" |
| Evidence Used | `Bietrick_Weekly_Leakage_Protocol_v2.pdf` (primary requirement source) |
| Reviewer | Bietrick (TL) |
| Status | BASELINED |
| Pass/Fail Rule | PASS if every downstream analysis (L1–L5) and output requirement is traceable to this document |
| Next Step | Validate each requirement against discovered data in `validation/COVERAGE_MATRIX.md` |
| Known Limitations | Requirements are transcribed from the v2.0 PDF; any later protocol revision supersedes this file |
