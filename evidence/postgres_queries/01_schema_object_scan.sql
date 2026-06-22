-- 01 — Schema + object scan (Phase 1)
-- Read-only. Discovers schemas and the objects within the relevant ones.

-- 1a. All schemas
-- (MCP: list_schemas)

-- 1b. Objects per relevant schema
-- (MCP: list_objects for public, development, staging_ai, analytics, ph_action_board, ...)

-- 1c. Confirm no views exist in public (all reusable views live in development/staging_ai)
-- (MCP: list_objects schema_name=public, object_type=view  -> returned [])

-- 1d. Search for any leakage / report assets across all schemas
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND (
    table_name ILIKE '%leakage%'
    OR table_name ILIKE '%html_report%'
    OR table_name ILIKE '%weekly_report%'
    OR table_name ILIKE '%stop_loss%'
    OR table_name ILIKE '%ppc_pause%'
    OR table_name ILIKE '%action_report%'
  )
ORDER BY table_schema, table_name;
