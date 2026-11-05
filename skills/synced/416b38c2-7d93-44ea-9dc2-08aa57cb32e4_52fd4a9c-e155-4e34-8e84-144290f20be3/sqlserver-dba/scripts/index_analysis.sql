/*==============================================================================
  index_analysis.sql   -- READ ONLY, safe on production
  Run in the context of the target database.

  1. Index inventory with usage (reads vs. writes)
  2. Unused / write-only indexes -- removal candidates
  3. Missing index suggestions, ranked by estimated impact
  4. Duplicate and overlapping indexes -- consolidation candidates
  5. Fragmentation (LIMITED mode; safe, but see note before running DETAILED)

  Nothing here is a decision. sys.dm_db_index_usage_stats resets on service
  restart, so judge over a full business cycle including month-end reporting.
==============================================================================*/
SET NOCOUNT ON;

PRINT 'Usage stats accumulated since: '
    + CONVERT(varchar(30), (SELECT sqlserver_start_time FROM sys.dm_os_sys_info), 120);

-------------------------------------------------------------------------------
-- 1. Inventory with usage
-------------------------------------------------------------------------------
SELECT OBJECT_SCHEMA_NAME(i.object_id)      AS schema_name,
       OBJECT_NAME(i.object_id)             AS table_name,
       i.name                               AS index_name,
       i.type_desc,
       i.is_unique,
       i.is_primary_key,
       i.filter_definition,
       p.rows                               AS row_count,
       CAST(SUM(a.total_pages) * 8.0 / 1024 AS decimal(18,1)) AS size_mb,
       ISNULL(us.user_seeks,0)              AS seeks,
       ISNULL(us.user_scans,0)              AS scans,
       ISNULL(us.user_lookups,0)            AS lookups,
       ISNULL(us.user_updates,0)            AS writes,
       ISNULL(us.user_seeks,0) + ISNULL(us.user_scans,0) + ISNULL(us.user_lookups,0) AS total_reads,
       us.last_user_seek,
       us.last_user_scan,
       STUFF((SELECT ', ' + c.name + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE '' END
              FROM sys.index_columns ic
              JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
              WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
                AND ic.is_included_column = 0
              ORDER BY ic.key_ordinal
              FOR XML PATH(''), TYPE).value('.','nvarchar(max)'), 1, 2, '') AS key_columns,
       STUFF((SELECT ', ' + c.name
              FROM sys.index_columns ic
              JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
              WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
                AND ic.is_included_column = 1
              ORDER BY ic.index_column_id
              FOR XML PATH(''), TYPE).value('.','nvarchar(max)'), 1, 2, '') AS included_columns
FROM sys.indexes i
JOIN sys.partitions p  ON p.object_id = i.object_id AND p.index_id = i.index_id
JOIN sys.allocation_units a ON a.container_id = p.partition_id
LEFT JOIN sys.dm_db_index_usage_stats us
       ON us.object_id = i.object_id AND us.index_id = i.index_id
      AND us.database_id = DB_ID()
WHERE OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
GROUP BY i.object_id, i.index_id, i.name, i.type_desc, i.is_unique, i.is_primary_key,
         i.filter_definition, p.rows, us.user_seeks, us.user_scans, us.user_lookups,
         us.user_updates, us.last_user_seek, us.last_user_scan
ORDER BY size_mb DESC;

-------------------------------------------------------------------------------
-- 2. Removal candidates: cost you writes, gives you nothing
-------------------------------------------------------------------------------
SELECT OBJECT_SCHEMA_NAME(i.object_id) AS schema_name,
       OBJECT_NAME(i.object_id)        AS table_name,
       i.name                          AS index_name,
       ISNULL(us.user_updates,0)       AS writes,
       ISNULL(us.user_seeks,0) + ISNULL(us.user_scans,0) + ISNULL(us.user_lookups,0) AS reads,
       CAST(SUM(a.total_pages) * 8.0 / 1024 AS decimal(18,1)) AS size_mb,
       'ALTER INDEX ' + QUOTENAME(i.name) + ' ON '
         + QUOTENAME(OBJECT_SCHEMA_NAME(i.object_id)) + '.'
         + QUOTENAME(OBJECT_NAME(i.object_id)) + ' DISABLE;  -- observe, then DROP'
                                       AS suggested_first_step
FROM sys.indexes i
JOIN sys.partitions p ON p.object_id = i.object_id AND p.index_id = i.index_id
JOIN sys.allocation_units a ON a.container_id = p.partition_id
LEFT JOIN sys.dm_db_index_usage_stats us
       ON us.object_id = i.object_id AND us.index_id = i.index_id AND us.database_id = DB_ID()
WHERE i.type_desc = 'NONCLUSTERED'
  AND i.is_primary_key = 0
  AND i.is_unique_constraint = 0
  AND i.is_unique = 0                      -- a unique index may be enforcing a rule
  AND OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
  AND ISNULL(us.user_seeks,0) + ISNULL(us.user_scans,0) + ISNULL(us.user_lookups,0) = 0
GROUP BY i.object_id, i.index_id, i.name, us.user_updates, us.user_seeks, us.user_scans, us.user_lookups
HAVING SUM(a.total_pages) * 8.0 / 1024 > 10
ORDER BY writes DESC;
-- Before dropping: confirm the index is not supporting a foreign key check and
-- that the usage window covered month-end and quarter-end reporting.

-------------------------------------------------------------------------------
-- 3. Missing index suggestions -- EVIDENCE, NOT A SCRIPT TO RUN
-------------------------------------------------------------------------------
SELECT TOP (25)
       CAST(migs.avg_total_user_cost * migs.avg_user_impact
            * (migs.user_seeks + migs.user_scans) / 100.0 AS decimal(18,2)) AS estimated_impact,
       migs.user_seeks + migs.user_scans   AS times_wanted,
       CAST(migs.avg_user_impact AS decimal(5,1)) AS avg_pct_improvement,
       OBJECT_SCHEMA_NAME(mid.object_id, mid.database_id) AS schema_name,
       OBJECT_NAME(mid.object_id, mid.database_id)        AS table_name,
       mid.equality_columns,
       mid.inequality_columns,
       mid.included_columns,
       'CREATE NONCLUSTERED INDEX IX_' + OBJECT_NAME(mid.object_id, mid.database_id) + '_TODO ON '
          + mid.statement + ' ('
          + ISNULL(mid.equality_columns, '')
          + CASE WHEN mid.equality_columns IS NOT NULL AND mid.inequality_columns IS NOT NULL
                 THEN ', ' ELSE '' END
          + ISNULL(mid.inequality_columns, '') + ')'
          + ISNULL(' INCLUDE (' + mid.included_columns + ')', '')
          + ' WITH (ONLINE = ON);'         AS draft_only_do_not_run_verbatim
FROM sys.dm_db_missing_index_group_stats migs
JOIN sys.dm_db_missing_index_groups   mig ON mig.index_group_handle = migs.group_handle
JOIN sys.dm_db_missing_index_details  mid ON mid.index_handle       = mig.index_handle
WHERE mid.database_id = DB_ID()
ORDER BY estimated_impact DESC;
/* These suggestions ignore existing indexes, ignore write cost, and never
   consolidate. Check section 1 first: extending an existing index usually beats
   creating a new one. Then verify with an actual execution plan before/after. */

-------------------------------------------------------------------------------
-- 4. Duplicate / overlapping indexes
-------------------------------------------------------------------------------
WITH idx AS (
    SELECT i.object_id, i.index_id, i.name, i.is_unique, i.is_primary_key,
           STUFF((SELECT ',' + CAST(ic.column_id AS varchar(10))
                  FROM sys.index_columns ic
                  WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id
                    AND ic.is_included_column = 0
                  ORDER BY ic.key_ordinal
                  FOR XML PATH(''), TYPE).value('.','nvarchar(max)'),1,1,'') AS key_cols
    FROM sys.indexes i
    WHERE i.type_desc IN ('CLUSTERED','NONCLUSTERED')
      AND OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
)
SELECT OBJECT_SCHEMA_NAME(a.object_id) AS schema_name,
       OBJECT_NAME(a.object_id)        AS table_name,
       a.name                          AS narrower_index,
       a.key_cols                      AS narrower_keys,
       b.name                          AS wider_index,
       b.key_cols                      AS wider_keys,
       CASE WHEN a.key_cols = b.key_cols THEN 'EXACT DUPLICATE'
            ELSE 'PREFIX -- narrower is redundant unless it is unique' END AS relationship,
       a.is_unique                     AS narrower_is_unique
FROM idx a
JOIN idx b ON b.object_id = a.object_id
          AND b.index_id  <> a.index_id
          AND b.key_cols LIKE a.key_cols + '%'
          AND LEN(b.key_cols) >= LEN(a.key_cols)
          AND NOT (a.key_cols = b.key_cols AND a.index_id > b.index_id)
WHERE a.is_primary_key = 0
ORDER BY schema_name, table_name;

-------------------------------------------------------------------------------
-- 5. Fragmentation (LIMITED mode -- reads only the parent level, cheap)
--    'DETAILED' reads every page: do not run it on a large busy database.
-------------------------------------------------------------------------------
SELECT OBJECT_SCHEMA_NAME(ips.object_id) AS schema_name,
       OBJECT_NAME(ips.object_id)        AS table_name,
       i.name                            AS index_name,
       ips.partition_number,
       ips.page_count,
       CAST(ips.page_count * 8.0 / 1024 AS decimal(18,1)) AS size_mb,
       CAST(ips.avg_fragmentation_in_percent AS decimal(5,1)) AS frag_pct,
       CAST(ips.avg_page_space_used_in_percent AS decimal(5,1)) AS page_fullness_pct,
       CASE WHEN ips.avg_fragmentation_in_percent > 30 THEN 'REBUILD'
            WHEN ips.avg_fragmentation_in_percent > 10 THEN 'REORGANIZE'
            ELSE 'leave alone' END       AS suggested_action,
       STATS_DATE(i.object_id, i.index_id) AS stats_last_updated
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i ON i.object_id = ips.object_id AND i.index_id = ips.index_id
WHERE ips.page_count > 1000              -- below this, fragmentation is meaningless
  AND ips.index_id > 0
ORDER BY ips.avg_fragmentation_in_percent DESC;
/* REORGANIZE does NOT update statistics; REBUILD does, with fullscan. If your
   maintenance job only reorganizes, add an explicit statistics update step --
   stale statistics cause far more regressions than fragmentation does. */
