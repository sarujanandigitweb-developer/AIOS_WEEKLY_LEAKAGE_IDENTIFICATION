# WLSP Dashboard Refresh — Headless Prompt

You are running non-interactively (`claude -p`). Refresh the WLSP leakage dashboard
by querying live PostgreSQL through MCP and rewriting ONLY the data block of the
self-contained dashboard file. Work autonomously; do not ask questions.

## Absolute rules
- **DB is READ-ONLY.** Only `SELECT`. Never INSERT/UPDATE/DELETE/ALTER/CREATE. Do not modify PostgreSQL.
- **Source tables ONLY:** `public.ppc_performance`, `public.order_transaction`,
  `public.order_shipping_billing_detail`, `public.amazon_returns`.
- **NEVER read:** `development.leakage_detection`, `development.leakage_classification`,
  `ph_action_board.*`, `ph_daily_actions`. (They must not appear in any query.)
- **Only one file may change:** `leakage_dashboard.html`. Do not create `data.js`.
  Do not create new files. Do not touch `index.html`, `data.js`, or `refresh_dashboard.py`.
- Replace ONLY the text between `<!-- WLSP_DATA_START -->` and `<!-- WLSP_DATA_END -->`.
  Leave every other byte of HTML/CSS/JS unchanged.
- Run all SQL via the tool `mcp__claude_ai_postgres__execute_sql`.

## Assumptions baked into the approved WLSP formulas
COGS 20% (gross factor 0.45 after platform fee), platform fee 15%, VAT 20%.
Account normalisation (apply wherever `ss_name` is selected):
```
CASE WHEN ss_name ILIKE '%dcvoltage%' THEN 'DCVoltage UK'
     WHEN ss_name ILIKE '%ledsone%' OR ss_name ILIKE '%led_sone%'
       OR ss_name ILIKE '%electricalsone%' OR ss_name ILIKE '%ledsonede%'
       OR ss_name ILIKE '%srm%' THEN 'LEDSone UK'
     ELSE ss_name END
```

---

## STEP 1 — Run these exact queries (in order) via `mcp__claude_ai_postgres__execute_sql`

### Q_L1 — zero-conversion PPC (spend>£3 AND conversions=0, 7d)
```sql
SELECT COALESCE(NULLIF(pp.user_name,''),'UNATTRIBUTED') AS ph, pp.ref_id AS asin, pp.sku AS sku,
       CASE WHEN pp.ss_name ILIKE '%dcvoltage%' THEN 'DCVoltage UK'
            WHEN pp.ss_name ILIKE '%ledsone%' OR pp.ss_name ILIKE '%led_sone%'
              OR pp.ss_name ILIKE '%electricalsone%' OR pp.ss_name ILIKE '%ledsonede%'
              OR pp.ss_name ILIKE '%srm%' THEN 'LEDSone UK' ELSE pp.ss_name END AS account,
       ROUND(SUM(pp.spend)::numeric,2) AS spend, SUM(pp.clicks)::int AS clicks,
       SUM(pp.impressions)::int AS impressions, SUM(pp.orders)::int AS conversions
FROM public.ppc_performance pp
WHERE (pp.ss_name ILIKE '%UK%' OR pp.marketplace ILIKE '%UK%')
  AND pp.date >= CURRENT_DATE - INTERVAL '7 days' AND pp.record_type='ad'
  AND pp.ref_id IS NOT NULL AND pp.ref_id NOT IN ('','0')
GROUP BY pp.ref_id, pp.sku, ph, account
HAVING SUM(pp.spend) > 3 AND SUM(pp.orders) = 0
ORDER BY spend DESC;
```

### Shared CTE for L2 / L3 (7-day completed order lines, shipping de-duped per order, allocated by revenue share)
Prepend this `WITH` block to Q_L2 and Q_L3:
```sql
WITH lines AS (
  SELECT ot.order_id, ot.asin, ot.sku, MAX(ot.user_name) AS user_name, MAX(ot.ss_name) AS ss_name,
         SUM(ot.item_price*ot.quantity) AS line_rev
  FROM public.order_transaction ot
  WHERE ot.source_name ILIKE '%amazon%' AND ot.market_place ILIKE '%UK%' AND ot.fba_sales=false
    AND ot.order_status='Completed' AND ot.order_date >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY ot.order_id, ot.asin, ot.sku),
orev AS (SELECT order_id, SUM(line_rev) ord_rev FROM lines GROUP BY order_id),
ship AS (SELECT order_id, MAX(carrier_charge) cc FROM public.order_shipping_billing_detail
         WHERE carrier_charge_currency='GBP' AND carrier_charge>0 GROUP BY order_id),
ppc AS (SELECT sku, SUM(spend) ppc FROM public.ppc_performance
        WHERE (ss_name ILIKE '%UK%' OR marketplace ILIKE '%UK%') AND date>=CURRENT_DATE-INTERVAL '7 days' GROUP BY sku)
```

### Q_L2 — shipping > 25% of revenue (7d, ASIN grain)
```sql
SELECT l.asin, COALESCE(NULLIF(MAX(l.user_name),''),'UNATTRIBUTED') AS ph,
       CASE WHEN MAX(l.ss_name) ILIKE '%dcvoltage%' THEN 'DCVoltage UK'
            WHEN MAX(l.ss_name) ILIKE '%ledsone%' OR MAX(l.ss_name) ILIKE '%led_sone%'
              OR MAX(l.ss_name) ILIKE '%srm%' THEN 'LEDSone UK' ELSE MAX(l.ss_name) END AS account,
       ROUND(SUM(l.line_rev)::numeric,2) AS revenue,
       ROUND(SUM(COALESCE(s.cc,0)*l.line_rev/NULLIF(o.ord_rev,0))::numeric,2) AS shipping,
       COUNT(DISTINCT l.order_id)::int AS orders,
       ROUND(100.0*SUM(COALESCE(s.cc,0)*l.line_rev/NULLIF(o.ord_rev,0))/NULLIF(SUM(l.line_rev),0),1) AS shipping_pct
FROM lines l JOIN orev o ON l.order_id=o.order_id LEFT JOIN ship s ON l.order_id=s.order_id
WHERE l.asin IS NOT NULL AND l.asin<>''
GROUP BY l.asin
HAVING SUM(l.line_rev)>0 AND 100.0*SUM(COALESCE(s.cc,0)*l.line_rev/NULLIF(o.ord_rev,0))/SUM(l.line_rev) > 25
ORDER BY shipping_pct DESC;
```

### Q_L3 — net-negative + PPC ((rev×0.45) − shipping − PPC < £0 AND PPC > £5, 7d, SKU grain)
```sql
SELECT l.sku, MAX(l.asin) AS asin, COALESCE(NULLIF(MAX(l.user_name),''),'UNATTRIBUTED') AS ph,
       CASE WHEN MAX(l.ss_name) ILIKE '%dcvoltage%' THEN 'DCVoltage UK'
            WHEN MAX(l.ss_name) ILIKE '%ledsone%' OR MAX(l.ss_name) ILIKE '%led_sone%'
              OR MAX(l.ss_name) ILIKE '%srm%' THEN 'LEDSone UK' ELSE MAX(l.ss_name) END AS account,
       ROUND(SUM(l.line_rev)::numeric,2) AS revenue,
       ROUND(SUM(COALESCE(s.cc,0)*l.line_rev/NULLIF(o.ord_rev,0))::numeric,2) AS shipping,
       ROUND(MAX(COALESCE(p.ppc,0))::numeric,2) AS ppc,
       ROUND((SUM(l.line_rev)*0.45 - SUM(COALESCE(s.cc,0)*l.line_rev/NULLIF(o.ord_rev,0)) - MAX(COALESCE(p.ppc,0)))::numeric,2) AS net
FROM lines l JOIN orev o ON l.order_id=o.order_id LEFT JOIN ship s ON l.order_id=s.order_id
LEFT JOIN ppc p ON l.sku=p.sku WHERE l.sku IS NOT NULL AND l.sku<>''
GROUP BY l.sku
HAVING (SUM(l.line_rev)*0.45 - SUM(COALESCE(s.cc,0)*l.line_rev/NULLIF(o.ord_rev,0)) - MAX(COALESCE(p.ppc,0)))<0
   AND MAX(COALESCE(p.ppc,0))>5
ORDER BY net ASC;
```

### Q_L4 — refund rate > 10%, min 2 orders (30d, ASIN grain)
```sql
SELECT ot.asin, COALESCE(NULLIF(MAX(ot.user_name),''),'UNATTRIBUTED') AS ph,
       CASE WHEN MAX(ot.ss_name) ILIKE '%dcvoltage%' THEN 'DCVoltage UK'
            WHEN MAX(ot.ss_name) ILIKE '%ledsone%' OR MAX(ot.ss_name) ILIKE '%led_sone%'
              OR MAX(ot.ss_name) ILIKE '%srm%' THEN 'LEDSone UK' ELSE MAX(ot.ss_name) END AS account,
       MAX(ot.sku) AS sku, COUNT(*)::int AS total_orders,
       COUNT(*) FILTER (WHERE ot.order_status='Refunded')::int AS refunded_orders,
       ROUND(100.0*COUNT(*) FILTER (WHERE ot.order_status='Refunded')/COUNT(*),1) AS refund_rate,
       ROUND(SUM(ot.item_price*ot.quantity) FILTER (WHERE ot.order_status='Refunded')::numeric,2) AS revenue_at_risk
FROM public.order_transaction ot
WHERE ot.source_name ILIKE '%amazon%' AND ot.market_place ILIKE '%UK%' AND ot.fba_sales=false
  AND ot.order_date >= CURRENT_DATE - INTERVAL '30 days' AND ot.asin IS NOT NULL AND ot.asin<>''
GROUP BY ot.asin
HAVING COUNT(*)>=2 AND 100.0*COUNT(*) FILTER (WHERE ot.order_status='Refunded')/COUNT(*) > 10
ORDER BY refund_rate DESC, revenue_at_risk DESC;
```

### Q_L5 — net margin declining ≥2 consecutive months (3 full months, per PH)
```sql
WITH ship AS (SELECT order_id, MAX(carrier_charge) cc FROM public.order_shipping_billing_detail
              WHERE carrier_charge_currency='GBP' AND carrier_charge>0 GROUP BY order_id),
rev AS (SELECT ot.user_name ph, DATE_TRUNC('month',ot.order_date)::date mth,
               SUM(ot.item_price*ot.quantity) revenue,
               SUM(COALESCE((SELECT cc FROM ship s WHERE s.order_id=ot.order_id),0)) shipping
        FROM public.order_transaction ot
        WHERE ot.source_name ILIKE '%amazon%' AND ot.market_place ILIKE '%UK%' AND ot.fba_sales=false
          AND ot.order_status IN ('Completed','Refunded')
          AND ot.order_date >= (DATE_TRUNC('month',CURRENT_DATE)-INTERVAL '3 months')
          AND ot.order_date <  DATE_TRUNC('month',CURRENT_DATE)
          AND ot.user_name IS NOT NULL AND ot.user_name<>'' GROUP BY 1,2),
ppc AS (SELECT user_name ph, DATE_TRUNC('month',date)::date mth, SUM(spend) ppc
        FROM public.ppc_performance
        WHERE (ss_name ILIKE '%UK%' OR marketplace ILIKE '%UK%')
          AND date >= (DATE_TRUNC('month',CURRENT_DATE)-INTERVAL '3 months')
          AND date <  DATE_TRUNC('month',CURRENT_DATE)
          AND user_name IS NOT NULL AND user_name<>'' GROUP BY 1,2),
marg AS (SELECT r.ph, to_char(r.mth,'YYYY-MM') month, r.mth,
                ROUND(r.revenue::numeric,2) revenue, ROUND(r.shipping::numeric,2) shipping,
                ROUND(COALESCE(p.ppc,0)::numeric,2) ppc,
                ROUND((r.revenue - r.revenue*0.55 - r.shipping - COALESCE(p.ppc,0))::numeric,2) net,
                CASE WHEN r.revenue>0 THEN ROUND((100.0*(r.revenue - r.revenue*0.55 - r.shipping - COALESCE(p.ppc,0))/r.revenue)::numeric,1) END margin_pct
         FROM rev r LEFT JOIN ppc p ON r.ph=p.ph AND r.mth=p.mth),
seq AS (SELECT ph, month, revenue, shipping, ppc, net, margin_pct,
               LAG(margin_pct) OVER (PARTITION BY ph ORDER BY mth) pm,
               LAG(margin_pct,2) OVER (PARTITION BY ph ORDER BY mth) pm2 FROM marg)
SELECT ph, month, revenue, shipping, ppc, net, margin_pct,
       (margin_pct < pm AND pm < pm2) AS declining
FROM seq ORDER BY ph, month;
```

### Q_ACCOUNT_SUMMARY — full per-account counts across L1–L4 (uncapped)
Run the L1 set, L2 set, L3 set, L4 set (same predicates as above) grouped by the normalised
`account`, and combine into `{account,l1,l2,l3,l4,total}`. (Use the same `HAVING` logic as
Q_L1/Q_L2/Q_L3/Q_L4; count flagged rows per analysis per account.)

### Q_PH_SUMMARY — full per-PH counts across L1–L4 + L5-declining (uncapped)
Same flagged sets grouped by `ph` (PPC `user_name` for L1; order `user_name` for L2–L4;
the set of PHs flagged `declining=true` in Q_L5 contributes `l5`), combined into
`{ph,l1,l2,l3,l4,l5,total}`.

### Q_SKU_PH_MAP — for `ph_status` (recoverability of UNATTRIBUTED rows)
```sql
SELECT sku, MAX(user_name) ph FROM public.order_transaction
WHERE source_name ILIKE '%amazon%' AND user_name IS NOT NULL AND user_name<>'' GROUP BY sku;
```

---

## STEP 2 — Assemble the `dashboardData` JSON
Build one object with EXACTLY these keys:
- `summary`: `{report_title:"PH Weekly Leakage Action Lists", report_date:<today ISO>, generated_at:<today ISO>,`
  `scope:"UK Amazon FBM", accounts:"LEDSone + DCVoltage", deadline:"Wednesday EOD",`
  `ph_count:<#PHs in ph_summary excluding UNATTRIBUTED>, analyses_count:5,`
  `counts:{l1,l2,l3,l4,l5}, displayed:{l1,l2,l3,l4,l5}}`
  - `counts` = **true full-set totals** (L1=row count of Q_L1, L2=Q_L2, L3=Q_L3, L4=Q_L4,
    L5=number of PHs with any `declining=true`).
- `l1`,`l2`: the Q_L1 / Q_L2 rows, **capped to the top 60 by severity** (L1 by `spend` desc,
  L2 by `shipping_pct` desc). `l3`,`l4`: all rows. `l5`: all Q_L5 monthly rows.
- `account_summary`: from Q_ACCOUNT_SUMMARY (full). `ph_summary`: from Q_PH_SUMMARY (full).
- For every embedded `l1/l2/l3/l4` row whose `ph` is `UNATTRIBUTED`, add
  `ph_status:"RECOVERABLE"` if its `sku` exists in Q_SKU_PH_MAP, else `"MISSING_SOURCE"`.
  Do NOT overwrite `ph`.
- `verification_summary`: an array of `{metric,value}` rows recording: generated date, source
  tables used, tables excluded from calc, and the L1/L2 display cap note.

`counts` MUST equal the true full-set totals; `displayed` MUST equal the embedded array lengths.

---

## STEP 3 — Update `leakage_dashboard.html`
In `leakage_dashboard.html`, replace EVERYTHING between `<!-- WLSP_DATA_START -->` and
`<!-- WLSP_DATA_END -->` (exclusive of the marker lines) with exactly:
```
<script>
const dashboardData = <the JSON, pretty-printed>;
window.dashboardData = dashboardData;
</script>
```
Do not change the marker lines or any other part of the file. Do not create `data.js`.

## STEP 4 — Confirm
Report: the row count of each of L1–L5, the account_summary totals, the ph_summary row count,
that `counts` matches the full totals, and that the file write succeeded.
