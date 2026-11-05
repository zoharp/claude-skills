/*==============================================================================
  tempdb_and_memory.sql   -- READ ONLY, safe on production
  1. tempdb file layout and sizing
  2. tempdb space consumers by session
  3. Version store (relevant when RCSI / snapshot isolation is on)
  4. Memory grants: who has memory, who is waiting for it
  5. Buffer pool distribution by database
  6. Plan cache health
==============================================================================*/
SET NOCOUNT ON;

-------------------------------------------------------------------------------
-- 1. tempdb files: should be equally sized with equal fixed-MB autogrowth
-------------------------------------------------------------------------------
SELECT f.file_id,
       f.name                                        AS logical_name,
       f.type_desc,
       f.physical_name,
       CAST(f.size * 8.0 / 1024 AS decimal(18,1))    AS size_mb,
       CASE WHEN f.is_percent_growth = 1
            THEN CAST(f.growth AS varchar(10)) + ' %  <-- CHANGE TO FIXED MB'
            ELSE CAST(f.growth * 8 / 1024 AS varchar(10)) + ' MB' END AS autogrowth,
       CAST(f.max_size * 8.0 / 1024 AS decimal(18,1)) AS max_size_mb,
       CAST(FILEPROPERTY(f.name,'SpaceUsed') * 8.0 / 1024 AS decimal(18,1)) AS used_mb
FROM tempdb.sys.database_files f
ORDER BY f.type_desc, f.file_id;

SELECT (SELECT COUNT(*) FROM tempdb.sys.database_files WHERE type_desc = 'ROWS') AS tempdb_data_files,
       (SELECT cpu_count FROM sys.dm_os_sys_info)                               AS logical_cores,
       (SELECT COUNT(DISTINCT size) FROM tempdb.sys.database_files WHERE type_desc = 'ROWS')
                                                                                AS distinct_file_sizes;
-- Target: min(cores, 8) equally-sized data files. Unequal sizes defeat
-- proportional fill, so allocation concentrates on one file and contends.

-- Allocation contention right now (2:x:x = tempdb)
SELECT r.session_id, r.wait_type, r.wait_time, r.wait_resource, r.command
FROM sys.dm_exec_requests r
WHERE r.wait_type LIKE 'PAGELATCH%'
  AND r.wait_resource LIKE '2:%';
-- Sustained PAGELATCH_UP/EX on 2:1:1 (PFS), 2:1:2 (GAM) or 2:1:3 (SGAM) means
-- allocation contention: add equally sized files. On metadata pages instead,
-- consider memory-optimized tempdb metadata (2019+, requires restart).

-------------------------------------------------------------------------------
-- 2. Who is using tempdb space
-------------------------------------------------------------------------------
SELECT s.session_id,
       s.login_name,
       s.host_name,
       s.program_name,
       (su.user_objects_alloc_page_count - su.user_objects_dealloc_page_count) * 8 / 1024.0
                                                          AS user_objects_mb,   -- #temp tables
       (su.internal_objects_alloc_page_count - su.internal_objects_dealloc_page_count) * 8 / 1024.0
                                                          AS internal_objects_mb, -- sorts, spools, spills
       r.command,
       t.text AS current_batch
FROM tempdb.sys.dm_db_session_space_usage su
JOIN sys.dm_exec_sessions s ON s.session_id = su.session_id
LEFT JOIN sys.dm_exec_requests r ON r.session_id = su.session_id
OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE su.user_objects_alloc_page_count + su.internal_objects_alloc_page_count > 0
ORDER BY internal_objects_mb DESC;
-- Large internal_objects_mb means spills: the query got a memory grant smaller
-- than it needed. Fix the cardinality estimate rather than adding memory.

-------------------------------------------------------------------------------
-- 3. Version store (RCSI / snapshot isolation)
-------------------------------------------------------------------------------
SELECT SUM(version_store_reserved_page_count) * 8 / 1024.0 AS version_store_mb,
       SUM(user_object_reserved_page_count)   * 8 / 1024.0 AS user_objects_mb,
       SUM(internal_object_reserved_page_count) * 8 / 1024.0 AS internal_objects_mb,
       SUM(unallocated_extent_page_count)     * 8 / 1024.0 AS free_mb
FROM tempdb.sys.dm_db_file_space_usage;

-- The oldest open transaction pins the version store: one long-running
-- transaction can grow tempdb without limit under RCSI.
SELECT TOP (10)
       tat.transaction_id,
       tat.transaction_begin_time,
       DATEDIFF(minute, tat.transaction_begin_time, SYSDATETIME()) AS open_minutes,
       s.session_id, s.login_name, s.host_name, s.program_name, s.status
FROM sys.dm_tran_active_snapshot_database_transactions tas
JOIN sys.dm_tran_active_transactions tat ON tat.transaction_id = tas.transaction_id
JOIN sys.dm_exec_sessions s              ON s.session_id       = tas.session_id
ORDER BY tat.transaction_begin_time;

-------------------------------------------------------------------------------
-- 4. Memory grants
-------------------------------------------------------------------------------
SELECT mg.session_id,
       mg.request_time,
       mg.grant_time,                      -- NULL = still waiting (RESOURCE_SEMAPHORE)
       DATEDIFF(second, mg.request_time, ISNULL(mg.grant_time, SYSDATETIME())) AS wait_sec,
       mg.requested_memory_kb / 1024.0 AS requested_mb,
       mg.granted_memory_kb   / 1024.0 AS granted_mb,
       mg.used_memory_kb      / 1024.0 AS used_mb,
       mg.max_used_memory_kb  / 1024.0 AS max_used_mb,
       mg.dop,
       mg.queue_id,
       t.text AS batch_text
FROM sys.dm_exec_query_memory_grants mg
OUTER APPLY sys.dm_exec_sql_text(mg.sql_handle) t
ORDER BY mg.requested_memory_kb DESC;
-- granted_mb far above max_used_mb = over-estimation hoarding memory from
-- everyone else. 2019+ memory grant feedback corrects repeat offenders;
-- 2022 persists that feedback across restarts via Query Store.

-------------------------------------------------------------------------------
-- 5. Buffer pool by database
-------------------------------------------------------------------------------
SELECT CASE database_id WHEN 32767 THEN 'ResourceDb' ELSE DB_NAME(database_id) END AS database_name,
       COUNT(*) * 8 / 1024.0 AS buffer_mb,
       CAST(100.0 * COUNT(*) / SUM(COUNT(*)) OVER () AS decimal(5,2)) AS pct_of_pool
FROM sys.dm_os_buffer_descriptors
GROUP BY database_id
ORDER BY buffer_mb DESC;

SELECT (SELECT cntr_value / 1024 FROM sys.dm_os_performance_counters
        WHERE counter_name = 'Total Server Memory (KB)')  AS total_server_memory_mb,
       (SELECT cntr_value / 1024 FROM sys.dm_os_performance_counters
        WHERE counter_name = 'Target Server Memory (KB)') AS target_server_memory_mb,
       (SELECT cntr_value FROM sys.dm_os_performance_counters
        WHERE counter_name = 'Page life expectancy'
          AND object_name LIKE '%Buffer Manager%')        AS page_life_expectancy,
       (SELECT value_in_use FROM sys.configurations
        WHERE name = 'max server memory (MB)')            AS max_server_memory_mb;
-- Page life expectancy is only meaningful as a trend. A sudden drop matters;
-- an absolute number does not.

-------------------------------------------------------------------------------
-- 6. Plan cache health
-------------------------------------------------------------------------------
SELECT objtype,
       COUNT(*)                            AS plan_count,
       SUM(CASE WHEN usecounts = 1 THEN 1 ELSE 0 END) AS single_use_plans,
       SUM(CAST(size_in_bytes AS bigint)) / 1024 / 1024 AS cache_mb,
       SUM(CASE WHEN usecounts = 1 THEN CAST(size_in_bytes AS bigint) ELSE 0 END) / 1024 / 1024
                                           AS single_use_mb
FROM sys.dm_exec_cached_plans
GROUP BY objtype
ORDER BY cache_mb DESC;
-- A large single_use_mb under objtype 'Adhoc' means unparameterized SQL is
-- bloating the cache. Turn on 'optimize for ad hoc workloads' and fix the
-- application to parameterize.
