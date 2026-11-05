# Instance configuration and maintenance

Configuration rarely fixes a slow query, but bad configuration makes every query worse and is cheap
to correct. Check these before believing a hardware problem.

## Memory

**`max server memory`** must be set - the default lets SQL Server take essentially everything and
starve the OS. A workable starting point on a dedicated server: leave 1 GB for the OS per 4 GB of
RAM up to 16 GB, then 1 GB per additional 8 GB, plus headroom for anything else on the box (SSIS,
SSRS, agents, antivirus). On a 64 GB dedicated server, roughly 52-56 GB.

Remember this controls the buffer pool plus most other caches; CLR, linked servers and backup
buffers live outside it. On a VM, avoid ballooning by reserving memory at the hypervisor.

**`min server memory`** matters mainly on shared or virtualized hosts to stop the OS clawing back
memory during idle periods.

**Lock Pages in Memory** (a Windows privilege for the service account) prevents the OS paging out
the buffer pool - worth setting on physical servers with large memory.

Page Life Expectancy is a weak signal on its own; a sudden drop is meaningful, an absolute number
is not. Prefer memory grant waits and `PAGEIOLATCH` waits as evidence of memory pressure.

## CPU and parallelism

**`cost threshold for parallelism`** defaults to 5, a value from 1997 hardware. Almost every OLTP
instance should raise it - 50 is a common, defensible starting point. Too low and trivial queries
get parallel plans whose coordination costs more than they save, generating `CXPACKET` noise.

**`max degree of parallelism`** (MAXDOP): the current guidance is at most 8, and no more than the
number of logical cores in a single NUMA node. For heavily OLTP workloads 4 or 8 is typical; 1 is
appropriate for some vendor applications that mandate it (Dynamics, SharePoint) but should never be
a self-prescribed fix for `CXPACKET`.

Both can be overridden per query (`OPTION (MAXDOP n)`), per database
(`ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP`) and per workload group in Resource Governor.

## tempdb

tempdb is shared by everything - sorts, hashes, version store, temp tables, spills - so its
configuration affects the whole instance.

- **Multiple equally-sized data files** to spread allocation across them: one per logical core up to
  8, then add 4 at a time if `PAGELATCH_UP` contention on 2:1:1 / 2:1:3 persists.
- **Equal size and equal autogrowth** on all files - proportional fill only balances when files are
  the same size. 2016+ configures this at setup and enables the old trace flag 1117/1118 behavior by
  default.
- **Pre-size** the files to what they will actually need, so autogrowth never happens during normal
  operation. Autogrowth on tempdb is a stall.
- 2019+ **memory-optimized tempdb metadata**
  (`ALTER SERVER CONFIGURATION SET MEMORY_OPTIMIZED TEMPDB_METADATA = ON`, requires restart) removes
  the system-table latch bottleneck on very high-concurrency workloads.
- Put tempdb on the fastest local storage available; it does not need to be protected, it is
  recreated at startup.

## Files, growth and storage

- **Instant File Initialization** - grant `Perform Volume Maintenance Tasks` to the service account.
  Data file growth and restores become near-instant instead of zeroing every byte. Log files are
  never instant-initialized.
- **Autogrowth in fixed MB, never percent.** Percent growth compounds; a 200 GB file growing 10%
  stalls the workload for a 20 GB allocation. 512 MB or 1 GB increments are reasonable for data.
- **Pre-size** files so that growth is an exception, and monitor for growth events - they are a sign
  the sizing is wrong.
- **Log file VLF count**: a log grown in tiny increments accumulates thousands of virtual log files,
  slowing recovery, restores and replication. Check `sys.dm_db_log_info`; if VLF count is in the
  thousands, shrink the log once and regrow it in large chunks (8 GB at a time is the usual advice).
- Log file growth in one big step is fine; data file growth in one big step needs IFI to be painless.

## Other instance settings worth checking

| Setting | Recommendation |
|---|---|
| `optimize for ad hoc workloads` | ON - stores a plan stub on first execution, avoiding plan cache bloat from single-use ad hoc SQL |
| `backup compression default` | ON - smaller and usually faster backups, small CPU cost |
| Trace flag 3226 | Suppresses successful-backup messages from the error log, which otherwise drown real errors |
| `remote admin connections` | ON - enables the DAC remotely, which is how you get in when the instance is unresponsive |
| Database `AUTO_CLOSE` | OFF, always |
| Database `AUTO_SHRINK` | OFF, always |
| `AUTO_CREATE_STATISTICS` / `AUTO_UPDATE_STATISTICS` | ON unless there is a specific, documented reason |
| Database owner | A real, valid login (often `sa`) - orphaned owners break several features |

**Never shrink a database as routine maintenance.** Shrinking fragments every index thoroughly and
the space is usually reclaimed by the next growth, so the cycle repeats. If a one-time reclaim is
genuinely needed after archiving, shrink and then rebuild indexes - in that order - and expect log
growth.

## Backups and recovery

Backup strategy is derived from RPO (how much data may be lost) and RTO (how long recovery may
take), not from habit. Establish both before recommending anything.

- **FULL recovery model** requires log backups; without them the log grows forever. This is the most
  common cause of "the log filled the disk".
- Typical pattern: weekly full, daily differential, log backups every 5-15 minutes depending on RPO.
- **A backup that has not been restored is not a backup.** Test restores on a schedule and time them,
  because RTO is a measured number, not an assumption. `RESTORE VERIFYONLY` checks readability, not
  recoverability.
- Use `WITH CHECKSUM` on backups, and `sys.dm_db_backup_checksum_failure` / error log monitoring to
  catch corruption early.
- Keep copies off the instance and off the host. For AWS-hosted 2022 instances, `BACKUP TO URL`
  supports S3-compatible storage directly.
- In regulated environments, retention and restore testing are usually a documented SOP requirement -
  make sure the evidence (job history, restore test records) is being kept.

## Integrity and maintenance jobs

- **`DBCC CHECKDB` weekly at minimum**, and read the results - a job that succeeds while CHECKDB
  reports errors is a common failure. On very large databases use `WITH PHYSICAL_ONLY` more often
  and a full check less often, or offload the full check to a restored copy.
- Corruption comes from storage, not from SQL Server. When CHECKDB reports errors, restore from
  backup; `REPAIR_ALLOW_DATA_LOSS` is a last resort that means what its name says.
- **Use Ola Hallengren's maintenance solution** (`DatabaseBackup`, `DatabaseIntegrityCheck`,
  `IndexOptimize`) rather than Maintenance Plans. It handles fragmentation thresholds, statistics,
  time limits, and logging correctly, and it is the de facto standard, which matters for handover.
- Alerting: configure SQL Agent alerts for severity 19-25 and error 825 (read-retry), plus job
  failure notifications. An unmonitored instance is an incident waiting to be discovered by a user.
- Keep `msdb` history trimmed (`sp_delete_backuphistory`), or it slowly poisons backup and job
  performance.

## Security baseline

- Least privilege: application accounts get `db_datareader`/`db_datawriter` plus explicit `EXECUTE`
  on the procedures they use, never `db_owner` or `sysadmin`.
- Prefer Windows/Entra authentication; if SQL logins are required, enforce password policy.
- Disable `xp_cmdshell` unless there is a documented need and a compensating control.
- Encrypt connections (`Force Encryption` / `Encrypt=True` in the connection string) and consider TDE
  for data at rest - note TDE is not a substitute for column-level protection of sensitive fields.
- Audit privileged actions with SQL Server Audit rather than triggers where the requirement is
  server-level.
- Keep cumulative updates current; patch level is `SERVERPROPERTY('ProductLevel')` plus
  `ProductUpdateLevel`.
