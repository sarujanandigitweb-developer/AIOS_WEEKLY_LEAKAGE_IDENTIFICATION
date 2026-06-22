-- 02 — Core table details + row counts (Phase 1). Read-only.

-- 2a. Column/index detail (MCP get_object_details) for:
--     public.order_transaction, public.ppc_performance, public.ppc_etl_performance_data,
--     public.amazon_returns, public.amz_fbm_performance_data, public.amz_order_expenses,
--     public.order_shipping_billing_detail, staging_ai.fbm_sku_daily_nnr_snapshot

-- 2b. Row-count estimates
SELECT relname AS table_name, n_live_tup AS estimated_row_count
FROM pg_stat_user_tables
WHERE relname IN (
  'order_transaction','ppc_etl_performance_data','ppc_performance',
  'amazon_returns','amz_fbm_performance_data','amz_order_expenses',
  'order_shipping_billing_detail','fbm_sku_daily_nnr_snapshot'
)
ORDER BY n_live_tup DESC;

-- 2c. Physical sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_tables
WHERE schemaname IN ('public','staging_ai')
  AND tablename IN (
    'order_transaction','ppc_etl_performance_data','ppc_performance',
    'amazon_returns','amz_fbm_performance_data','amz_order_expenses',
    'order_shipping_billing_detail','fbm_sku_daily_nnr_snapshot',
    'fbm_sku_daily_nnr_snapshot_runs'
  )
ORDER BY schemaname, tablename;

-- 2d. Order status distribution (UK Amazon)
SELECT order_status, COUNT(*) AS cnt
FROM public.order_transaction
WHERE source_name ILIKE '%amazon%'
GROUP BY order_status ORDER BY cnt DESC;
