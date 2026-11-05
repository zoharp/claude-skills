/*==============================================================================
  trigger_inventory.sql   -- READ ONLY, safe on production
  Run in the context of the target database.

  1. Every DML trigger with anti-pattern flags
  2. Runtime cost since last restart
  3. DDL and logon triggers
  4. Tables whose triggers can be bypassed (audit-completeness gaps)

  The text-search flags in section 1 are heuristics. They point at code worth
  reading, not at proven bugs -- and they can miss things (e.g. logic in a
  called procedure). Read the trigger body before concluding anything.
==============================================================================*/
SET NOCOUNT ON;

-------------------------------------------------------------------------------
-- 1. DML triggers with anti-pattern flags
-------------------------------------------------------------------------------
SELECT OBJECT_SCHEMA_NAME(t.parent_id) AS parent_schema,
       OBJECT_NAME(t.parent_id)        AS parent_table,
       t.name                          AS trigger_name,
       CASE WHEN t.is_instead_of_trigger = 1 THEN 'INSTEAD OF' ELSE 'AFTER' END AS trigger_type,
       STUFF((SELECT ', ' + te.type_desc
              FROM sys.trigger_events te
              WHERE te.object_id = t.object_id
              FOR XML PATH(''), TYPE).value('.','nvarchar(max)'),1,2,'') AS fires_on,
       t.is_disabled,
       t.create_date,
       t.modify_date,
       LEN(m.definition)               AS definition_length,

       /* --- anti-pattern heuristics ------------------------------------- */
       CASE WHEN m.definition NOT LIKE '%NOCOUNT%'
            THEN 'no SET NOCOUNT ON' END                        AS flag_nocount,

       CASE WHEN m.definition NOT LIKE '%ROWCOUNT%'
             AND m.definition NOT LIKE '%NOT EXISTS%inserted%'
             AND m.definition NOT LIKE '%NOT EXISTS%deleted%'
            THEN 'no zero-row early exit' END                   AS flag_no_early_exit,

       CASE WHEN m.definition LIKE '%CURSOR%'
             OR m.definition LIKE '%WHILE%'
            THEN 'ROW-BY-ROW LOOP -- high risk' END             AS flag_loop,

       /* scalar assignment from inserted/deleted: the multi-row bug */
       CASE WHEN m.definition LIKE '%SELECT @%FROM%inserted%'
             OR m.definition LIKE '%SELECT @%FROM%deleted%'
             OR m.definition LIKE '%SET @%(SELECT%inserted%'
            THEN 'SCALAR ASSIGNMENT FROM inserted/deleted -- breaks on multi-row DML'
       END                                                      AS flag_multirow_bug,

       CASE WHEN m.definition LIKE '%ROLLBACK%'
            THEN 'ROLLBACK inside trigger -- aborts caller batch; prefer THROW' END AS flag_rollback,

       CASE WHEN m.definition LIKE '%sp_send_dbmail%'
             OR m.definition LIKE '%xp_cmdshell%'
             OR m.definition LIKE '%OPENQUERY%'
             OR m.definition LIKE '%OPENROWSET%'
             OR m.definition LIKE '%[[]%[]].%[[]%[]].%[[]%[]].%'   -- 4-part linked server name
            THEN 'EXTERNAL CALL -- holds caller locks for its duration' END AS flag_external_call,

       CASE WHEN m.definition LIKE '%UPDATE(%'
            THEN 'uses UPDATE() -- true when column was referenced, not changed' END AS flag_update_function,

       CASE WHEN t.is_disabled = 1
            THEN 'DISABLED -- silent audit/logic gap' END        AS flag_disabled,

       m.definition
FROM sys.triggers t
JOIN sys.sql_modules m ON m.object_id = t.object_id
WHERE t.parent_class = 1                      -- object (table/view) triggers
ORDER BY parent_schema, parent_table, t.name;

-------------------------------------------------------------------------------
-- 2. What triggers actually cost (since last restart / plan cache eviction)
-------------------------------------------------------------------------------
SELECT OBJECT_SCHEMA_NAME(ts.object_id) AS schema_name,
       OBJECT_NAME(ts.object_id)        AS trigger_name,
       OBJECT_NAME(t.parent_id)         AS parent_table,
       ts.execution_count,
       CAST(ts.total_elapsed_time / 1000000.0 AS decimal(18,2))               AS total_elapsed_sec,
       CAST(ts.total_elapsed_time / 1000.0
            / NULLIF(ts.execution_count,0) AS decimal(18,3))                  AS avg_elapsed_ms,
       CAST(ts.total_worker_time / 1000000.0 AS decimal(18,2))                AS total_cpu_sec,
       ts.total_logical_reads,
       ts.total_logical_reads / NULLIF(ts.execution_count,0)                  AS avg_logical_reads,
       ts.last_execution_time
FROM sys.dm_exec_trigger_stats ts
LEFT JOIN sys.triggers t ON t.object_id = ts.object_id
WHERE ts.database_id = DB_ID()
ORDER BY ts.total_elapsed_time DESC;
-- avg_elapsed_ms is added to every DML statement on the parent table, inside
-- the caller's transaction. Anything above a few milliseconds on a hot table
-- is worth investigating.

-------------------------------------------------------------------------------
-- 3. DDL and logon triggers
-------------------------------------------------------------------------------
SELECT 'DATABASE' AS scope, t.name, t.is_disabled, t.create_date, t.modify_date,
       STUFF((SELECT ', ' + te.type_desc FROM sys.trigger_events te
              WHERE te.object_id = t.object_id
              FOR XML PATH(''), TYPE).value('.','nvarchar(max)'),1,2,'') AS fires_on,
       m.definition
FROM sys.triggers t
JOIN sys.sql_modules m ON m.object_id = t.object_id
WHERE t.parent_class = 0
UNION ALL
SELECT 'SERVER', t.name, t.is_disabled, t.create_date, t.modify_date,
       STUFF((SELECT ', ' + te.type_desc FROM sys.server_trigger_events te
              WHERE te.object_id = t.object_id
              FOR XML PATH(''), TYPE).value('.','nvarchar(max)'),1,2,''),
       m.definition
FROM sys.server_triggers t
JOIN sys.server_sql_modules m ON m.object_id = t.object_id;
-- A slow or failing LOGON trigger can lock every user out of the instance.
-- Recovery is starting SQL Server with the -f minimal configuration flag.

-------------------------------------------------------------------------------
-- 4. Audit-completeness: where can a trigger be bypassed?
-------------------------------------------------------------------------------
SELECT OBJECT_SCHEMA_NAME(tr.parent_id) AS schema_name,
       OBJECT_NAME(tr.parent_id)        AS table_name,
       COUNT(*)                         AS trigger_count,
       SUM(CAST(tr.is_disabled AS int))  AS disabled_count,
       CASE WHEN t.temporal_type_desc = 'SYSTEM_VERSIONED_TEMPORAL_TABLE'
            THEN 'temporal history exists' ELSE 'no temporal history' END AS temporal_status,
       'TRUNCATE TABLE and bulk load without FIRE_TRIGGERS bypass these triggers'
                                        AS known_bypass_paths
FROM sys.triggers tr
JOIN sys.tables t ON t.object_id = tr.parent_id
WHERE tr.parent_class = 1
GROUP BY tr.parent_id, t.temporal_type_desc
ORDER BY schema_name, table_name;
/* If a trigger is the audit mechanism for a regulated system, the bypass paths
   must be closed: DENY ALTER on the tables so nobody can TRUNCATE or disable
   the trigger, and control who can run bulk loads. Otherwise the audit trail
   has documented holes. Ledger (2022) or temporal tables are stronger. */
