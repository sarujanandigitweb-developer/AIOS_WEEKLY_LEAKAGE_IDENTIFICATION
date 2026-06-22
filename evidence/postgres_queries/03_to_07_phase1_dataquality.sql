-- 03–07 — Phase 1 data-quality + relationship checks. Read-only.

-- 03 amazon_returns profile
SELECT MIN(request_date) AS earliest, MAX(request_date) AS latest, COUNT(*) AS total_rows,
       COUNT(DISTINCT asin) AS distinct_asins, COUNT(DISTINCT sku) AS distinct_skus,
       COUNT(CASE WHEN market_place ILIKE '%UK%' THEN 1 END) AS uk_rows
FROM public.amazon_returns;

-- 04 Confirm ppc_performance.ref_id = ASIN, and PH/account profile
SELECT DISTINCT pp.ref_id, pp.sku, pp.record_type, ot.asin, ot.sku AS ot_sku
FROM public.ppc_performance pp
JOIN public.order_transaction ot ON pp.sku = ot.sku
WHERE (pp.ss_name ILIKE '%UK%' OR pp.marketplace ILIKE '%UK%')
  AND pp.date >= NOW() - INTERVAL '7 days'
  AND ot.source_name ILIKE '%amazon%' AND ot.market_place ILIKE '%UK%'
LIMIT 5;

SELECT DISTINCT ss_name, marketplace FROM public.ppc_performance
WHERE (ss_name ILIKE '%UK%' OR marketplace ILIKE '%UK%')
  AND date >= NOW() - INTERVAL '7 days' ORDER BY ss_name;

-- 04b PH mapping completeness (order_transaction, UK FBM, 30d)
SELECT COUNT(*) AS total_rows,
       COUNT(CASE WHEN user_name IS NOT NULL AND user_name<>'' THEN 1 END) AS rows_with_ph,
       ROUND(100.0*COUNT(CASE WHEN user_name IS NOT NULL AND user_name<>'' THEN 1 END)/COUNT(*),1) AS pct_mapped,
       COUNT(DISTINCT user_name) AS distinct_ph_owners
FROM public.order_transaction
WHERE source_name ILIKE '%amazon%' AND market_place ILIKE '%UK%'
  AND order_date >= NOW() - INTERVAL '30 days';

-- 05 Shipping coverage + template-price emptiness
SELECT COUNT(DISTINCT ot.order_id) AS total_amazon_orders,
       COUNT(DISTINCT CASE WHEN osbd.carrier_charge>0 THEN osbd.order_id END) AS orders_with_carrier_charge,
       ROUND(100.0*COUNT(DISTINCT CASE WHEN osbd.carrier_charge>0 THEN osbd.order_id END)
             /NULLIF(COUNT(DISTINCT ot.order_id),0),1) AS pct_with_shipping
FROM public.order_transaction ot
LEFT JOIN public.order_shipping_billing_detail osbd ON ot.order_id=osbd.order_id
WHERE ot.source_name ILIKE '%amazon%' AND ot.market_place ILIKE '%UK%'
  AND ot.order_status='Completed' AND ot.order_date >= NOW() - INTERVAL '30 days';

SELECT COUNT(*) AS total_rows,
       COUNT(CASE WHEN shipping_template_price>0 THEN 1 END) AS rows_with_template_price,
       AVG(carrier_charge) AS avg_carrier_charge, AVG(shipping_template_price) AS avg_template_price
FROM public.order_shipping_billing_detail
WHERE order_id IN (SELECT order_id FROM public.order_transaction
  WHERE source_name ILIKE '%amazon%' AND market_place ILIKE '%UK%' LIMIT 10000);

-- 06 NNR snapshot freshness
SELECT MAX(snapshot_date) AS latest, MIN(snapshot_date) AS earliest,
       COUNT(DISTINCT snapshot_date) AS snapshot_days, COUNT(*) AS rows,
       COUNT(DISTINCT sku) AS skus, COUNT(DISTINCT ph_owner) AS phs
FROM staging_ai.fbm_sku_daily_nnr_snapshot
WHERE marketplace ILIKE '%UK%' OR channel ILIKE '%amazon%';

-- 07 PPC UK range/grain
SELECT MIN(date) AS earliest, MAX(date) AS latest, COUNT(*) AS rows, COUNT(DISTINCT sku) AS skus
FROM public.ppc_performance WHERE ss_name ILIKE '%UK%' OR marketplace ILIKE '%UK%';
