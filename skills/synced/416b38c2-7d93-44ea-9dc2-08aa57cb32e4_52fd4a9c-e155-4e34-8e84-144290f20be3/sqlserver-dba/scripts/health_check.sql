/*==============================================================================
  health_check.sql   -- READ ONLY, safe on production
  One pass over the things that are wrong on most instances.
  Start here when you inherit an unfamiliar server.
==============================================================================*/
SET NOCOUNT ON;

-------------------------------------------------------------------------------
-- 1. What am I connected to?
-------------------------------------------------------------------------------
SELECT SERVERPROPERTY('MachineName')                    AS machine_name,
       SERVERPROPERTY('ServerName')                     AS server_name,
       SERVERPROPERTY('ProductVersion')                 AS product_version,
       SERVERPROPERTY('ProductLevel')                   AS product_level,
       SERVERPROPERTY('ProductUpdateLevel')             AS cu_level,
       SERVERPROPERTY('Edition')                        AS edition,
       SERVERPROPERTY('IsHadrEnabled')                  AS hadr_enabled,
       SERVERPROPERTY('IsClustered')                    AS clustered,
       si.cpu_count                                     AS logical_cores,
       si.physical_memory_kb / 1024 / 1024              AS server_ram_gb,
       si.sqlserver_start_time,
       DATEDIFF(day, si.sqlserver_start_time, SYSDATETIME()) AS uptime_days
FROM sys.dm_os_sys_info si;
-- Uptime under ~7 days means the cumulative DMVs below have little history.

-------------------------------------------------------------------------------
-- 2. Configuration values that are commonly wrong
-------------------------------------------------------------------------------
SELECT c.name,
       c.value_in_use,
       CASE c.name
            WHEN 'max server memory (MB)' THEN
                 CASE WHEN c.value_in_use > 2000000
                      THEN 'UNSET -- SQL Server will starve the OS' ELSE 'set' END
            WHEN 'cost threshold for parallelism' THEN
                 CASE WHEN c.value_in_use <= 5
                      THEN 'DEFAULT 5 is far too low -- consider 50' ELSE 'raised' END
            WHEN 'max degree of parallelism' THEN
                 CASE WHEN c.value_in_use = 0
                      THEN 'unlimited -- cap at <= 8 and <= cores per NUMA node'
                      WHEN c.value_in_use = 1
                      THEN 'serial only -- correct for some vendor apps, otherwise suspicious'
                      ELSE 'set' END
            WHEN 'optimize for ad hoc workloads' THEN
                 CASE WHEN c.value_in_use = 0
                      THEN 'OFF -- turn ON to stop single-use plan cache bloat' ELSE 'on' END
            WHEN 'backup compression default' THEN
                 CASE WHEN c.value_in_use = 0 THEN 'OFF -- usually worth turning on' ELSE 'on' END
            WHEN 'remote admin connections' THEN
                 CASE WHEN c.value_in_use = 0
                      THEN 'OFF -- no remote DAC when the instance is unresponsive' ELSE 'on' END
            WHEN 'xp_cmdshell' THEN
                 CASE WHEN c.value_in_use = 1 THEN 'ENABLED -- confirm it is required' ELSE 'disabled' END
            ELSE '' END AS assessment
FROM sys.configurations c
WHERE c.name IN ('max server memory (MB)', 'min server memory (MB)',
                 'cost threshold for parallelism', 'max degree of parallelism',
                 'optimize for ad hoc workloads', 'backup compression default',
                 'remote admin connections', 'xp_cmdshell', 'nested triggers',
                 'max worker threads', 'fill factor (%)')
ORDER BY c.name;

-------------------------------------------------------------------------------
-- 3. Database settings that cause trouble
-------------------------------------------------------------------------------
SELECT d.name,
       d.state_desc,
       d.recovery_model_desc,
       d.compatibility_level,
       d.is_auto_close_on,
       d.is_auto_shrink_on,
       d.is_auto_create_stats_on,
       d.is_auto_update_stats_on,
       d.is_read_committed_snapshot_on,
       d.snapshot_isolation_state_desc,
       d.is_query_store_on,
       d.page_verify_option_desc,
       SUSER_SNAME(d.owner_sid)                          AS db_owner,
       CASE WHEN d.is_auto_close_on = 1  THEN 'AUTO_CLOSE ON -- turn OFF; '  ELSE '' END
     + CASE WHEN d.is_auto_shrink_on = 1 THEN 'AUTO_SHRINK ON -- turn OFF; ' ELSE '' END
     + CASE WHEN d.is_auto_create_stats_on = 0 THEN 'auto-create stats OFF; ' ELSE '' END
     + CASE WHEN d.is_auto_update_stats_on = 0 THEN 'auto-update stats OFF; ' ELSE '' END
     + CASE WHEN d.page_verify_option_desc <> 'CHECKSUM' THEN 'page verify not CHECKSUM; ' ELSE '' END
     + CASE WHEN d.compatibility_level < 160 AND d.database_id > 4
            THEN 'compat < 160: no 2022 optimizer features; ' ELSE '' END
                                                         AS findings
FROM sys.databases d
ORDER BY d.database_id;

-------------------------------------------------------------------------------
-- 4. File layout, free space and percent autogrowth
-------------------------------------------------------------------------------
SELECT DB_NAME(f.database_id)                            AS database_name,
       f.name                                            AS logical_name,
       f.type_desc,
       f.physical_name,
       CAST(f.size * 8.0 / 1024 AS decimal(18,1))        AS size_mb,
       CASE WHEN f.is_percent_growth = 1
            THEN CAST(f.growth AS varchar(10)) + ' %  <-- use fixed MB instead'
            ELSE CAST(f.growth * 8 / 1024 AS varchar(10)) + ' MB' END AS autogrowth,
       CASE WHEN f.max_size = -1 THEN 'unlimited'
            WHEN f.max_size = 268435456 THEN 'log max 2TB'
            ELSE CAST(f.max_size * 8 / 1024 AS varchar(20)) + ' MB' END AS max_size
FROM sys.master_files f
ORDER BY database_name, f.type_desc, f.file_id;

-- IO latency per file: read/write stall in ms. Over ~20 ms on data files or
-- ~5 ms on log files points at storage (or at a query doing too much IO).
SELECT DB_NAME(vfs.database_id)                          AS database_name,
       mf.name                                           AS logical_name,
       mf.type_desc,
       vfs.num_of_reads,
       vfs.io_stall_read_ms / NULLIF(vfs.num_of_reads,0)   AS avg_read_stall_ms,
       vfs.num_of_writes,
       vfs.io_stall_write_ms / NULLIF(vfs.num_of_writes,0) AS avg_write_stall_ms,
       CAST(vfs.size_on_disk_bytes / 1024.0 / 1024 AS decimal(18,1)) AS size_mb
FROM sys.dm_io_virtual_file_stats(NULL, NULL) vfs
JOIN sys.master_files mf ON mf.database_id = vfs.database_id AND mf.file_id = vfs.file_id
ORDER BY (vfs.io_stall_read_ms + vfs.io_stall_write_ms) DESC;

-------------------------------------------------------------------------------
-- 5. Backups -- the check people skip until they need it
-------------------------------------------------------------------------------
SELECT d.name                                            AS database_name,
       d.recovery_model_desc,
       MAX(CASE WHEN b.type = 'D' THEN b.backup_finish_date END) AS last_full,
       MAX(CASE WHEN b.type = 'I' THEN b.backup_finish_date END) AS last_differential,
       MAX(CASE WHEN b.type = 'L' THEN b.backup_finish_date END) AS last_log,
       DATEDIFF(hour, MAX(CASE WHEN b.type = 'D' THEN b.backup_finish_date END),
                SYSDATETIME())                           AS hours_since_full,
       CASE WHEN d.recovery_model_desc = 'FULL'
             AND MAX(CASE WHEN b.type = 'L' THEN b.backup_finish_date END) IS NULL
            THEN 'FULL recovery with NO log backups -- the log will grow forever'
            WHEN MAX(CASE WHEN b.type = 'D' THEN b.backup_finish_date END) IS NULL
            THEN 'NEVER BACKED UP'
            ELSE '' END                                  AS finding
FROM sys.databases d
LEFT JOIN msdb.dbo.backupset b ON b.database_name = d.name
WHERE d.database_id <> 2                                  -- tempdb is not backed up
GROUP BY d.name, d.recovery_model_desc
ORDER BY hours_since_full DESC;

-------------------------------------------------------------------------------
-- 6. Last known-good CHECKDB per database
-------------------------------------------------------------------------------
DECLARE @dbccResults TABLE (ParentObject varchar(255), [Object] varchar(255),
                            Field varchar(255), [Value] varchar(255));
DECLARE @db sysname, @sql nvarchar(500);
DECLARE db_cursor CURSOR LOCAL FAST_FORWARD FOR
    SELECT name FROM sys.databases WHERE state_desc = 'ONLINE' AND database_id <> 2;
OPEN db_cursor;
FETCH NEXT FROM db_cursor INTO @db;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = N'DBCC DBINFO(' + QUOTENAME(@db, '''') + N') WITH TABLERESULTS, NO_INFOMSGS';
    INSERT INTO @dbccResults EXEC sp_executesql @sql;
    FETCH NEXT FROM db_cursor INTO @db;
END
CLOSE db_cursor; DEALLOCATE db_cursor;

SELECT [Value] AS last_known_good_checkdb_utc,
       DATEDIFF(day, TRY_CONVERT(datetime, [Value]), SYSUTCDATETIME()) AS days_ago
FROM @dbccResults
WHERE Field = 'dbi_dbccLastKnownGood'
ORDER BY [Value];
-- A date of 1900-01-01 means CHECKDB has never completed successfully.
-- Weekly at minimum; on very large databases, PHYSICAL_ONLY more often plus a
-- full check against a restored copy.

-------------------------------------------------------------------------------
-- 7. Failed Agent jobs in the last week
-------------------------------------------------------------------------------
SELECT j.name AS job_name,
       h.run_date, h.run_time, h.run_duration,
       h.message
FROM msdb.dbo.sysjobhistory h
JOIN msdb.dbo.sysjobs j ON j.job_id = h.job_id
WHERE h.step_id = 0
  AND h.run_status <> 1
  AND h.run_date >= CONVERT(int, CONVERT(varchar(8), DATEADD(day,-7,GETDATE()), 112))
ORDER BY h.run_date DESC, h.run_time DESC;

-------------------------------------------------------------------------------
-- 8. Top waits (see wait_stats.sql for the full analysis)
-------------------------------------------------------------------------------
SELECT TOP (10)
       wait_type,
       CAST(wait_time_ms / 1000.0 AS decimal(18,1)) AS wait_sec,
       waiting_tasks_count
FROM sys.dm_os_wait_stats
WHERE waiting_tasks_count > 0
  AND wait_type NOT LIKE 'SLEEP%'
  AND wait_type NOT LIKE 'XE%'
  AND wait_type NOT LIKE 'BROKER%'
  AND wait_type NOT LIKE 'HADR%'
  AND wait_type NOT LIKE 'QDS%'
  AND wait_type NOT IN ('WAITFOR','LAZYWRITER_SLEEP','DIRTY_PAGE_POLL','CXCONSUMER',
                        'REQUEST_FOR_DEADLOCK_SEARCH','CHECKPOINT_QUEUE','LOGMGR_QUEUE',
                        'SQLTRACE_INCREMENTAL_FLUSH_SLEEP','SP_SERVER_DIAGNOSTICS_SLEEP',
                        'DISPATCHER_QUEUE_SEMAPHORE','SOS_WORK_DISPATCHER')
ORDER BY wait_time_ms DESC;
