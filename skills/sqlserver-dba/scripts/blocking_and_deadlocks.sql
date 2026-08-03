/*==============================================================================
  blocking_and_deadlocks.sql   -- READ ONLY, safe on production
  Section 1: live blocking chain with the head blocker identified
  Section 2: open transactions, including idle ones holding locks
  Section 3: lock detail for a specific session
  Section 4: recent deadlock graphs from the system_health XE session
             (already running by default -- no setup needed)
==============================================================================*/
SET NOCOUNT ON;

-------------------------------------------------------------------------------
-- 1. Who is blocking whom, right now
-------------------------------------------------------------------------------
WITH chain AS (
    SELECT r.session_id,
           r.blocking_session_id,
           r.wait_type,
           r.wait_time,
           r.wait_resource,
           r.command,
           r.status,
           DB_NAME(r.database_id) AS database_name,
           r.sql_handle,
           r.statement_start_offset,
           r.statement_end_offset
    FROM sys.dm_exec_requests r
    WHERE r.blocking_session_id <> 0
       OR r.session_id IN (SELECT blocking_session_id
                           FROM sys.dm_exec_requests
                           WHERE blocking_session_id <> 0)
)
SELECT c.session_id,
       c.blocking_session_id,
       CASE WHEN c.blocking_session_id = 0 THEN 'HEAD BLOCKER' ELSE 'blocked' END AS role,
       c.wait_type,
       c.wait_time / 1000.0 AS wait_sec,
       c.wait_resource,
       c.database_name,
       c.status,
       s.login_name,
       s.host_name,
       s.program_name,
       s.last_request_start_time,
       t.text                AS batch_text,
       SUBSTRING(t.text, (c.statement_start_offset/2)+1,
                 ((CASE c.statement_end_offset WHEN -1 THEN DATALENGTH(t.text)
                        ELSE c.statement_end_offset END - c.statement_start_offset)/2)+1
       ) AS current_statement
FROM chain c
JOIN sys.dm_exec_sessions s ON s.session_id = c.session_id
OUTER APPLY sys.dm_exec_sql_text(c.sql_handle) t
ORDER BY c.blocking_session_id, c.wait_time DESC;

-------------------------------------------------------------------------------
-- 2. Open transactions -- including sessions that are sleeping while holding locks
--    (the classic "application opened a transaction then went to lunch" case)
-------------------------------------------------------------------------------
SELECT s.session_id,
       s.login_name,
       s.host_name,
       s.program_name,
       s.status                      AS session_status,
       DB_NAME(tst.database_id)      AS database_name,
       tat.transaction_begin_time,
       DATEDIFF(second, tat.transaction_begin_time, SYSDATETIME()) AS open_seconds,
       CASE tat.transaction_state
            WHEN 0 THEN 'not initialized' WHEN 1 THEN 'not started'
            WHEN 2 THEN 'ACTIVE'          WHEN 3 THEN 'ended (read-only)'
            WHEN 4 THEN 'commit initiated' WHEN 5 THEN 'PREPARED'
            WHEN 6 THEN 'committed'       WHEN 7 THEN 'rolling back'
            WHEN 8 THEN 'rolled back'     END AS transaction_state,
       tdt.database_transaction_log_bytes_used / 1024.0 / 1024.0 AS log_mb_used,
       t.text AS last_statement
FROM sys.dm_tran_session_transactions tst
JOIN sys.dm_tran_active_transactions  tat ON tat.transaction_id = tst.transaction_id
JOIN sys.dm_exec_sessions             s   ON s.session_id       = tst.session_id
LEFT JOIN sys.dm_tran_database_transactions tdt
       ON tdt.transaction_id = tst.transaction_id
LEFT JOIN sys.dm_exec_connections c ON c.session_id = s.session_id
OUTER APPLY sys.dm_exec_sql_text(c.most_recent_sql_handle) t
ORDER BY tat.transaction_begin_time;
-- A session_status of 'sleeping' with an ACTIVE transaction means the
-- application is holding locks while doing nothing. That is an application bug.

-------------------------------------------------------------------------------
-- 3. Lock detail for one session (set @spid first)
-------------------------------------------------------------------------------
DECLARE @spid int = NULL;   -- e.g. 57

IF @spid IS NOT NULL
    SELECT l.request_session_id,
           l.resource_type,
           l.resource_subtype,
           DB_NAME(l.resource_database_id) AS database_name,
           CASE l.resource_type
                WHEN 'OBJECT' THEN OBJECT_NAME(l.resource_associated_entity_id, l.resource_database_id)
                WHEN 'KEY'    THEN (SELECT OBJECT_NAME(p.object_id)
                                    FROM sys.partitions p
                                    WHERE p.hobt_id = l.resource_associated_entity_id)
                WHEN 'PAGE'   THEN (SELECT OBJECT_NAME(p.object_id)
                                    FROM sys.partitions p
                                    WHERE p.hobt_id = l.resource_associated_entity_id)
                ELSE NULL END              AS object_name,
           l.request_mode,                 -- S, X, U, IS, IX, SCH-M ...
           l.request_status,               -- GRANT, WAIT, CONVERT
           l.resource_description,
           COUNT(*) OVER (PARTITION BY l.request_mode, l.request_status) AS locks_of_this_kind
    FROM sys.dm_tran_locks l
    WHERE l.request_session_id = @spid
    ORDER BY l.request_status DESC, l.resource_type;
-- Thousands of KEY locks on one object means escalation to a table lock is
-- imminent (the threshold is around 5,000 locks on a single object).

-------------------------------------------------------------------------------
-- 4. Deadlock graphs already captured by system_health
-------------------------------------------------------------------------------
WITH xe AS (
    SELECT CAST(target_data AS xml) AS target_data
    FROM sys.dm_xe_session_targets st
    JOIN sys.dm_xe_sessions s ON s.address = st.event_session_address
    WHERE s.name = 'system_health'
      AND st.target_name = 'ring_buffer'
),
deadlocks AS (
    SELECT x.value('(@timestamp)[1]', 'datetime2')      AS event_time_utc,
           x.query('(data/value/deadlock)[1]')          AS deadlock_graph
    FROM xe
    CROSS APPLY target_data.nodes('//RingBufferTarget/event[@name="xml_deadlock_report"]') AS n(x)
)
SELECT TOP (25)
       event_time_utc,
       deadlock_graph,     -- click to open; save as .xdl to view graphically in SSMS
       deadlock_graph.value('(deadlock/victim-list/victimProcess/@id)[1]', 'varchar(50)') AS victim_process
FROM deadlocks
ORDER BY event_time_utc DESC;

/* Reading a deadlock graph:
     - find the two processes and the resource each held vs. wanted
     - read the inputbuf of each: those are the two statements that collided
     - the usual cause is inconsistent table access order between code paths
     - the usual fix is consistent ordering, shorter transactions, or an index
       that stops a modification from scanning
   Regardless of the fix, the application must retry error 1205. */
