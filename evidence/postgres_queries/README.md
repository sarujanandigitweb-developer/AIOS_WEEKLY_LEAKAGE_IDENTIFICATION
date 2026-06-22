# Evidence — Postgres Queries

Every SQL statement run during Phase 1 + Phase 2 discovery is recorded here as a `.sql` file. The recorded
output of each is in the sibling folder `../query_results/` under the same numeric prefix.

**Read-only guarantee:** all queries are `SELECT` / metadata reads only. No DDL, no DML. The discovery phase
created no objects and modified no data.

| # | File | What it answers |
|---|------|-----------------|
| 01 | `01_schema_object_scan.sql` | Which schemas and objects exist |
| 02 | `02_core_table_details.sql` | Columns/indexes + row counts of the 6 core tables |
| 03 | `03_returns_profile.sql` | `amazon_returns` range + UK coverage |
| 04 | `04_ppc_refid_is_asin.sql` | Confirm `ppc_performance.ref_id` = ASIN; PH + account profile |
| 05 | `05_shipping_coverage.sql` | Shipping join coverage + template-price emptiness |
| 06 | `06_nnr_snapshot.sql` | `fbm_sku_daily_nnr_snapshot` freshness |
| 07 | `07_relationships.sql` | Join feasibility across tables |
| 08 | `08_leakage_row_counts.sql` | Row counts + status of the 3 leakage tables |
| 09 | `09_detection_by_pattern.sql` | pattern_id population + loss totals |
| 10 | `10_root_cause_summary.sql` | Classification root-cause frequency/severity |
| 11 | `11_paid_media_detail.sql` | PAID_MEDIA_BLEED records in full |
| 12 | `12_shipping_high_detail.sql` | SHIPPING_HIGH records vs L2 |
| 13 | `13_daily_loss_anomaly.sql` | daily_loss formula-change detection |
| 14 | `14_detected_skus_vs_ppc.sql` | Overlap of detected SKUs with active 7-day PPC (L3) |
