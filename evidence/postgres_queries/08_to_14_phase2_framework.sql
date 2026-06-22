-- 08–14 — Phase 2 leakage framework inspection. Read-only.

-- 08 Row counts + detection status summary
SELECT 'leakage_detection' AS tbl, COUNT(*) FROM development.leakage_detection
UNION ALL SELECT 'leakage_classification', COUNT(*) FROM development.leakage_classification
UNION ALL SELECT 'leakage_pattern_registry', COUNT(*) FROM development.leakage_pattern_registry;

SELECT channel, marketplace, status, kill_recommended, COUNT(*) AS count,
       MIN(detected_at) AS earliest_detected, MAX(detected_at) AS latest_detected
FROM development.leakage_detection
GROUP BY channel, marketplace, status, kill_recommended;

-- 09 pattern_id population + loss totals (proves pattern_id always NULL)
SELECT ld.pattern_id, lpr.pattern_class, ld.status, COUNT(*) AS count,
       SUM(ld.daily_loss_gbp) AS total_daily_loss, SUM(ld.cumulative_loss_gbp) AS total_cumulative_loss
FROM development.leakage_detection ld
LEFT JOIN development.leakage_pattern_registry lpr ON ld.pattern_id = lpr.id
GROUP BY ld.pattern_id, lpr.pattern_class, ld.status;

-- 10 Classification root-cause frequency/severity
SELECT root_cause, COUNT(*) AS frequency, MIN(severity_tier) AS min_sev, MAX(severity_tier) AS max_sev,
       ROUND(AVG(severity_tier),1) AS avg_sev, COUNT(DISTINCT sku) AS skus, COUNT(DISTINCT ph_user_name) AS phs
FROM development.leakage_classification GROUP BY root_cause ORDER BY frequency DESC;

-- 11 PAID_MEDIA_BLEED detail (proves ACOS-based, not zero-conversion)
SELECT lc.sku, lc.ph_user_name, lc.root_cause_detail, lc.paid_media_pct, lc.recommended_action,
       ld.asin, ld.nnr_30d, ld.daily_loss_gbp, ld.detected_at
FROM development.leakage_classification lc
JOIN development.leakage_detection ld ON lc.leakage_detection_id = ld.id
WHERE lc.root_cause = 'PAID_MEDIA_BLEED';

-- 12 SHIPPING_HIGH detail (proves same 25% threshold as L2)
SELECT lc.sku, lc.ph_user_name, lc.root_cause_detail, lc.shipping_pct, lc.recommended_action,
       ld.asin, ld.nnr_30d, ld.detected_at
FROM development.leakage_classification lc
JOIN development.leakage_detection ld ON lc.leakage_detection_id = ld.id
WHERE lc.root_cause = 'SHIPPING_HIGH' ORDER BY lc.classified_at DESC LIMIT 10;

-- 13 daily_loss formula-change detection across runs
SELECT detection_run_id, COUNT(*) AS skus, MIN(daily_loss_gbp) AS min_loss, MAX(daily_loss_gbp) AS max_loss,
       SUM(daily_loss_gbp) AS sum_loss, MAX(days_red) AS max_days_red
FROM development.leakage_detection GROUP BY detection_run_id ORDER BY MIN(detected_at);

-- 14 Overlap: detected SKUs that also have active 7-day PPC > £3 (L3 duplicate-truth probe)
SELECT COUNT(DISTINCT ld.sku) AS total_detected_skus,
       COUNT(DISTINCT CASE WHEN pp.sku IS NOT NULL THEN ld.sku END) AS detected_with_active_ppc
FROM development.leakage_detection ld
LEFT JOIN (SELECT sku, SUM(spend) AS total_spend FROM public.ppc_performance
           WHERE (ss_name ILIKE '%UK%' OR marketplace ILIKE '%UK%') AND date >= NOW() - INTERVAL '7 days'
           GROUP BY sku HAVING SUM(spend) > 3) pp ON ld.sku = pp.sku
WHERE ld.status = 'OPEN';
