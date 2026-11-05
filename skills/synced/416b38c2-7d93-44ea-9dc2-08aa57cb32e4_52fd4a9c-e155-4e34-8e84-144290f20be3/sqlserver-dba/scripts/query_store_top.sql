/*==============================================================================
  query_store_top.sql   -- READ ONLY, safe on production
  Find the queries actually worth tuning.

  Run in the context of the target database (Query Store is per database).
  Section 4 is the fallback for databases where Query Store is off.

  Rank by TOTAL resource consumption, not average: a 20 ms query executed
  5 million times an hour outranks a 30 second report run once a day.
==============================================================================*/
SET NOCOUNT ON;

DECLARE @hours int = 24;   -- lookback window

-------------------------------------------------------------------------------
-- 0. Is Query Store even on and healthy?
-------------------------------------------------------------------------------
SELECT DB_NAME()                    AS database_name,
       actual_state_desc,           -- ERROR or READ_ONLY means you are losing data
       desired_state_desc,
       readonly_reason,             -- non-zero explains a forced READ_ONLY (often size)
       current_storage_size_mb,
       max_storage_size_mb,
       query_capture_mode_desc,
       interval_length_minutes,
       wait_stats_capture_mode_desc
FROM sys.database_query_store_options;
-- If actual_state_desc = 'READ_ONLY' with readonly_reason = 65536, Query Store
-- is full: raise MAX_STORAGE_SIZE_MB or clear it, otherwise it is blind.

-------------------------------------------------------------------------------
-- 1. Top consumers by total duration, CPU and logical reads
-------------------------------------------------------------------------------
SELECT TOP (25)
       q.query_id,
       p.plan_id,
       OBJECT_NAME(q.object_id)                                    AS object_name,
       SUM(rs.count_executions)                                    AS executions,
       CAST(SUM(rs.avg_duration * rs.count_executions)/1000000.0 AS decimal(18,2)) AS total_duration_sec,
       CAST(AVG(rs.avg_duration)/1000.0 AS decimal(18,2))          AS avg_duration_ms,
       CAST(SUM(rs.avg_cpu_time * rs.count_executions)/1000000.0 AS decimal(18,2)) AS total_cpu_sec,
       CAST(AVG(rs.avg_logical_io_reads) AS bigint)                AS avg_logical_reads,
       CAST(AVG(rs.avg_query_max_used_memory) * 8 / 1024.0 AS decimal(18,2)) AS avg_grant_mb,
       CAST(AVG(rs.avg_rowcount) AS bigint)                        AS avg_rows,
       COUNT(DISTINCT p.plan_id)                                   AS distinct_plans,
       MAX(rs.last_execution_time)                                 AS last_execution,
       LEFT(qt.query_sql_text, 300)                                AS query_text
FROM sys.query_store_query q
JOIN sys.query_store_query_text qt  ON qt.query_text_id = q.query_text_id
JOIN sys.query_store_plan p         ON p.query_id       = q.query_id
JOIN sys.query_store_runtime_stats rs ON rs.plan_id     = p.plan_id
JOIN sys.query_store_runtime_stats_interval i ON i.runtime_stats_interval_id = rs.runtime_stats_interval_id
WHERE i.start_time > DATEADD(hour, -@hours, SYSUTCDATETIME())
GROUP BY q.query_id, p.plan_id, q.object_id, qt.query_sql_text
ORDER BY total_duration_sec DESC;
-- distinct_plans > 1 on a hot query is the parameter-sensitivity signal.

-------------------------------------------------------------------------------
-- 2. Regressed queries: got slower after picking up a new plan
-------------------------------------------------------------------------------
WITH per_plan AS (
    SELECT q.query_id, p.plan_id,
           MIN(i.start_time)                              AS first_seen,
           SUM(rs.count_executions)                       AS executions,
           SUM(rs.avg_duration * rs.count_executions)
             / NULLIF(SUM(rs.count_executions),0) / 1000.0 AS avg_ms
    FROM sys.query_store_query q
    JOIN sys.query_store_plan p           ON p.query_id = q.query_id
    JOIN sys.query_store_runtime_stats rs ON rs.plan_id = p.plan_id
    JOIN sys.query_store_runtime_stats_interval i
         ON i.runtime_stats_interval_id = rs.runtime_stats_interval_id
    WHERE i.start_time > DATEADD(day, -7, SYSUTCDATETIME())
    GROUP BY q.query_id, p.plan_id
    HAVING SUM(rs.count_executions) > 10
)
SELECT TOP (20)
       a.query_id,
       a.plan_id                 AS slow_plan_id,
       CAST(a.avg_ms AS decimal(18,2)) AS slow_plan_avg_ms,
       b.plan_id                 AS fast_plan_id,
       CAST(b.avg_ms AS decimal(18,2)) AS fast_plan_avg_ms,
       CAST(a.avg_ms / NULLIF(b.avg_ms,0) AS decimal(18,1)) AS times_slower,
       a.executions              AS slow_plan_executions,
       LEFT(qt.query_sql_text, 300) AS query_text
FROM per_plan a
JOIN per_plan b ON b.query_id = a.query_id AND b.plan_id <> a.plan_id
JOIN sys.query_store_query q       ON q.query_id = a.query_id
JOIN sys.query_store_query_text qt ON qt.query_text_id = q.query_text_id
WHERE a.avg_ms > b.avg_ms * 2
  AND a.first_seen > b.first_seen        -- the newer plan is the slower one
  AND a.avg_ms > 50
ORDER BY (a.avg_ms - b.avg_ms) * a.executions DESC;

/* To pin the good plan temporarily while you fix the real cause:
       EXEC sys.sp_query_store_force_plan @query_id = <id>, @plan_id = <fast_plan_id>;
   To release it:
       EXEC sys.sp_query_store_unforce_plan @query_id = <id>, @plan_id = <fast_plan_id>;
   Track every forced plan -- forcing can silently stop working after schema changes.
   Check sys.query_store_plan.is_forced_plan and last_force_failure_reason_desc. */

-------------------------------------------------------------------------------
-- 3. Where is the time going? Wait categories per query
-------------------------------------------------------------------------------
SELECT TOP (20)
       q.query_id,
       ws.wait_category_desc,
       CAST(SUM(ws.total_query_wait_time_ms)/1000.0 AS decimal(18,1)) AS wait_sec,
       LEFT(qt.query_sql_text, 200) AS query_text
FROM sys.query_store_wait_stats ws
JOIN sys.query_store_plan p        ON p.plan_id = ws.plan_id
JOIN sys.query_store_query q       ON q.query_id = p.query_id
JOIN sys.query_store_query_text qt ON qt.query_text_id = q.query_text_id
JOIN sys.query_store_runtime_stats_interval i
     ON i.runtime_stats_interval_id = ws.runtime_stats_interval_id
WHERE i.start_time > DATEADD(hour, -@hours, SYSUTCDATETIME())
GROUP BY q.query_id, ws.wait_category_desc, qt.query_sql_text
ORDER BY wait_sec DESC;

-------------------------------------------------------------------------------
-- 4. Fallback when Query Store is off: plan cache
--    Note this only sees what is still cached -- restarts and memory pressure
--    lose history, which is exactly why Query Store is better.
-------------------------------------------------------------------------------
SELECT TOP (25)
       DB_NAME(t.dbid)                                        AS database_name,
       OBJECT_NAME(t.objectid, t.dbid)                        AS object_name,
       qs.execution_count,
       CAST(qs.total_elapsed_time/1000000.0 AS decimal(18,2)) AS total_elapsed_sec,
       CAST(qs.total_elapsed_time/1000.0/qs.execution_count AS decimal(18,2)) AS avg_elapsed_ms,
       CAST(qs.total_worker_time/1000000.0 AS decimal(18,2))  AS total_cpu_sec,
       qs.total_logical_reads,
       qs.total_logical_reads / qs.execution_count            AS avg_logical_reads,
       qs.total_spills,
       qs.creation_time,
       qs.last_execution_time,
       SUBSTRING(t.text, (qs.statement_start_offset/2)+1,
                 ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(t.text)
                        ELSE qs.statement_end_offset END - qs.statement_start_offset)/2)+1) AS statement_text,
       qp.query_plan
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) t
CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
WHERE t.dbid IS NULL OR t.dbid = DB_ID()
ORDER BY qs.total_elapsed_time DESC;
