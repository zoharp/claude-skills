/*==============================================================================
  wait_stats.sql   -- READ ONLY, safe on production
  What is this instance waiting on?

  Section 1: cumulative waits since restart (or last manual clear)
  Section 2: a 60-second delta -- far more useful for a live problem
  Section 3: what each currently-running session is waiting on right now

  Cumulative numbers are dominated by whatever happened weeks ago. If you are
  chasing a problem happening NOW, run section 2.
==============================================================================*/
SET NOCOUNT ON;

-------------------------------------------------------------------------------
-- 1. Cumulative waits, benign background waits excluded
-------------------------------------------------------------------------------
PRINT '=== CUMULATIVE WAITS SINCE ' + CONVERT(varchar(30),
      (SELECT sqlserver_start_time FROM sys.dm_os_sys_info), 120) + ' ===';

WITH w AS (
    SELECT wait_type,
           wait_time_ms                     AS total_wait_ms,
           wait_time_ms - signal_wait_time_ms AS resource_wait_ms,
           signal_wait_time_ms,             -- time waiting for CPU after being signalled
           waiting_tasks_count
    FROM sys.dm_os_wait_stats
    WHERE waiting_tasks_count > 0
      AND wait_type NOT IN (
          N'BROKER_EVENTHANDLER', N'BROKER_RECEIVE_WAITFOR', N'BROKER_TASK_STOP',
          N'BROKER_TO_FLUSH', N'BROKER_TRANSMITTER', N'CHECKPOINT_QUEUE',
          N'CHKPT', N'CLR_AUTO_EVENT', N'CLR_MANUAL_EVENT', N'CLR_SEMAPHORE',
          N'DBMIRROR_DBM_EVENT', N'DBMIRROR_EVENTS_QUEUE', N'DBMIRROR_WORKER_QUEUE',
          N'DBMIRRORING_CMD', N'DIRTY_PAGE_POLL', N'DISPATCHER_QUEUE_SEMAPHORE',
          N'EXECSYNC', N'FSAGENT', N'FT_IFTS_SCHEDULER_IDLE_WAIT', N'FT_IFTSHC_MUTEX',
          N'HADR_CLUSAPI_CALL', N'HADR_FILESTREAM_IOMGR_IOCOMPLETION',
          N'HADR_LOGCAPTURE_WAIT', N'HADR_NOTIFICATION_DEQUEUE',
          N'HADR_TIMER_TASK', N'HADR_WORK_QUEUE', N'KSOURCE_WAKEUP',
          N'LAZYWRITER_SLEEP', N'LOGMGR_QUEUE', N'MEMORY_ALLOCATION_EXT',
          N'ONDEMAND_TASK_QUEUE', N'PARALLEL_REDO_DRAIN_WORKER',
          N'PARALLEL_REDO_LOG_CACHE', N'PARALLEL_REDO_WORKER_SYNC',
          N'PARALLEL_REDO_WORKER_WAIT_WORK', N'PREEMPTIVE_XE_GETTARGETSTATE',
          N'PVS_PREALLOC', N'QDS_ASYNC_QUEUE', N'QDS_PERSIST_TASK_MAIN_LOOP_SLEEP',
          N'QDS_SHUTDOWN_QUEUE', N'REDO_THREAD_PENDING_WORK', N'REQUEST_FOR_DEADLOCK_SEARCH',
          N'RESOURCE_QUEUE', N'SERVER_IDLE_CHECK', N'SLEEP_BPOOL_FLUSH', N'SLEEP_DBSTARTUP',
          N'SLEEP_DCOMSTARTUP', N'SLEEP_MASTERDBREADY', N'SLEEP_MASTERMDREADY',
          N'SLEEP_MASTERUPGRADED', N'SLEEP_SYSTEMTASK', N'SLEEP_TASK', N'SLEEP_TEMPDBSTARTUP',
          N'SNI_HTTP_ACCEPT', N'SOS_WORK_DISPATCHER', N'SP_SERVER_DIAGNOSTICS_SLEEP',
          N'SQLTRACE_BUFFER_FLUSH', N'SQLTRACE_INCREMENTAL_FLUSH_SLEEP',
          N'SQLTRACE_WAIT_ENTRIES', N'VDI_CLIENT_OTHER', N'WAIT_FOR_RESULTS',
          N'WAITFOR', N'WAITFOR_TASKSHUTDOWN', N'WAIT_XTP_HOST_WAIT',
          N'WAIT_XTP_OFFLINE_CKPT_NEW_LOG', N'WAIT_XTP_CKPT_CLOSE',
          N'XE_DISPATCHER_JOIN', N'XE_DISPATCHER_WAIT', N'XE_TIMER_EVENT',
          N'CXCONSUMER')
)
SELECT TOP (20)
       wait_type,
       CAST(total_wait_ms / 1000.0 AS decimal(18,1))                            AS wait_sec,
       CAST(resource_wait_ms / 1000.0 AS decimal(18,1))                         AS resource_sec,
       CAST(signal_wait_time_ms / 1000.0 AS decimal(18,1))                      AS signal_sec,
       waiting_tasks_count,
       CAST(total_wait_ms * 1.0 / NULLIF(waiting_tasks_count,0) AS decimal(18,1)) AS avg_wait_ms,
       CAST(100.0 * total_wait_ms / SUM(total_wait_ms) OVER () AS decimal(5,2))   AS pct_of_total
FROM w
ORDER BY total_wait_ms DESC;
-- High signal_sec relative to resource_sec means CPU pressure: tasks are ready
-- to run but queuing for a scheduler.

-------------------------------------------------------------------------------
-- 2. 60-second delta -- run this when the problem is happening
-------------------------------------------------------------------------------
IF OBJECT_ID('tempdb..#w1') IS NOT NULL DROP TABLE #w1;
SELECT wait_type, wait_time_ms, waiting_tasks_count
INTO #w1 FROM sys.dm_os_wait_stats;

WAITFOR DELAY '00:01:00';

SELECT TOP (15)
       w2.wait_type,
       CAST((w2.wait_time_ms - w1.wait_time_ms) / 1000.0 AS decimal(18,1)) AS wait_sec_in_window,
       w2.waiting_tasks_count - w1.waiting_tasks_count                     AS waits_in_window
FROM sys.dm_os_wait_stats w2
JOIN #w1 w1 ON w1.wait_type = w2.wait_type
WHERE w2.wait_time_ms - w1.wait_time_ms > 0
  AND w2.wait_type NOT LIKE N'SLEEP%'
  AND w2.wait_type NOT LIKE N'XE%'
  AND w2.wait_type NOT LIKE N'BROKER%'
  AND w2.wait_type NOT IN (N'WAITFOR', N'LAZYWRITER_SLEEP', N'DIRTY_PAGE_POLL',
                           N'REQUEST_FOR_DEADLOCK_SEARCH', N'CXCONSUMER',
                           N'QDS_PERSIST_TASK_MAIN_LOOP_SLEEP', N'HADR_WORK_QUEUE')
ORDER BY (w2.wait_time_ms - w1.wait_time_ms) DESC;

DROP TABLE #w1;

-------------------------------------------------------------------------------
-- 3. What is waiting right now, and on what
-------------------------------------------------------------------------------
SELECT r.session_id,
       r.blocking_session_id,
       r.status,
       r.wait_type,
       r.wait_time            AS wait_time_ms,
       r.last_wait_type,
       r.wait_resource,
       DB_NAME(r.database_id) AS database_name,
       r.command,
       r.cpu_time,
       r.logical_reads,
       r.granted_query_memory * 8 / 1024 AS granted_memory_mb,
       s.login_name,
       s.host_name,
       s.program_name,
       SUBSTRING(t.text,
                 (r.statement_start_offset/2) + 1,
                 ((CASE r.statement_end_offset WHEN -1 THEN DATALENGTH(t.text)
                        ELSE r.statement_end_offset END - r.statement_start_offset)/2) + 1
       ) AS running_statement
FROM sys.dm_exec_requests r
JOIN sys.dm_exec_sessions s ON s.session_id = r.session_id
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE r.session_id <> @@SPID
  AND s.is_user_process = 1
ORDER BY r.wait_time DESC;
