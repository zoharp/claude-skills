# Indexing and storage

Contents: [Clustered index](#choosing-the-clustered-index) · [Nonclustered design](#nonclustered-index-design)
· [Missing index DMVs](#reading-the-missing-index-dmvs) · [Consolidation](#consolidating-and-removing-indexes)
· [Fragmentation](#fragmentation-and-maintenance) · [Columnstore](#columnstore)
· [Compression](#compression) · [Partitioning](#partitioning) · [Data types](#data-types-and-row-width)

## Choosing the clustered index

The clustered index *is* the table, and its key is appended to every nonclustered index. Get it
wrong and every other index pays.

Good clustered key: narrow, unique, static, and ever-increasing. An `int`/`bigint` identity or a
sequence hits all four. Requirements in detail:

- **Narrow** - the key is duplicated into every nonclustered index; a 4-byte key versus a 16-byte
  `uniqueidentifier` is a large difference multiplied across every index and page.
- **Unique** - if it is not, SQL Server adds a 4-byte uniquifier anyway.
- **Static** - updating a clustered key relocates the row and updates every nonclustered index.
- **Ever-increasing** - new rows append to the end, avoiding page splits and fragmentation.

Random GUIDs (`NEWID()`) as a clustered key cause constant mid-page splits and fragmentation.
`NEWSEQUENTIALID()` fixes the ordering, but if the value must be a GUID for application reasons,
consider clustering on an identity and keeping a unique nonclustered index on the GUID.

The last-page insert hotspot is the counterargument: extremely high insert rates on an
ever-increasing key contend on the final page (`PAGELATCH_EX` on the table's last page). That
scenario - thousands of inserts per second - is where `OPTIMIZE_FOR_SEQUENTIAL_KEY = ON` (2019+)
helps. Do not apply it prophylactically.

Heaps (no clustered index) are appropriate for staging tables written by bulk load and read once.
For anything queried by predicate, cluster it.

## Nonclustered index design

Key column order follows the query's predicates:

1. **Equality predicates first**, most selective first among them.
2. **Range predicates next** (`>`, `<`, `BETWEEN`, `LIKE 'x%'`) - only one range column benefits.
3. Columns needed for `ORDER BY` / `GROUP BY`, to avoid a sort.
4. Everything else the query selects goes in `INCLUDE`, not the key.

`INCLUDE` columns live only at the leaf level, so they enlarge the index far less than key columns
and are not subject to the 900/1700-byte key size limit. That is how a covering index avoids key
lookups without bloating the tree.

```sql
-- WHERE CustomerId = @c AND OrderDate >= @d ORDER BY OrderDate; SELECT Status, Total
CREATE NONCLUSTERED INDEX IX_Orders_CustomerId_OrderDate
    ON dbo.Orders (CustomerId, OrderDate)
    INCLUDE (Status, Total)
    WITH (ONLINE = ON, DATA_COMPRESSION = PAGE, FILLFACTOR = 90);
```

`ONLINE = ON` requires Enterprise (and 2019+ for some resumable variants); on Standard the build
takes a schema modification lock for its duration - which on a large table means an outage. Say so
when recommending an index on a Standard instance, and offer the maintenance-window plan.

**Filtered indexes** are excellent for the "small hot subset" pattern - open orders in a table of
completed ones, or `WHERE IsDeleted = 0`. Caveat: the query's predicate must be provably covered by
the filter, and parameterized queries frequently fail to match, so verify with an actual plan.

**Unique indexes** are not just constraints - uniqueness informs the optimizer's cardinality
estimates and often produces better plans. Declare it when it is true.

## Reading the missing index DMVs

`sys.dm_db_missing_index_details` and the green hint in a plan are **suggestions from a single
query's perspective**, not a design. They over-include columns, ignore existing indexes, ignore
write cost, and never consolidate. Never create one verbatim.

Use them as evidence: `scripts/index_analysis.sql` ranks them by estimated impact. Then check
whether an existing index can be extended (adding an `INCLUDE` column or reordering keys serves
several queries with one index), and confirm with an actual plan before and after.

## Consolidating and removing indexes

Duplicate and overlapping indexes are pure cost - storage, write amplification, buffer pool, and
longer maintenance. If `IX_A (CustomerId)` and `IX_B (CustomerId, OrderDate)` both exist, the first
is redundant: a leading-column prefix match is served by the wider index.

Before dropping anything, check `sys.dm_db_index_usage_stats` for seeks, scans, lookups and
updates. An index with zero reads and heavy writes is a candidate for removal. Two cautions that
have burned people:

- The DMV resets on service restart (and, in some versions, on index rebuild). Judge over a full
  business cycle including month-end and quarter-end reporting.
- An index with no usage may still be enforcing a unique constraint or supporting a foreign key
  check.

Safer than dropping: `ALTER INDEX ... DISABLE`, observe, then drop once confident. Disabling a
*clustered* index makes the entire table inaccessible - never do that as a test.

## Fragmentation and maintenance

Modern guidance is that fragmentation matters much less than the industry assumed, and the
statistics update that comes with a rebuild is often what actually helped. Reasonable defaults:

| Avg fragmentation | Action |
|---|---|
| < 10% | Nothing |
| 10-30% | `ALTER INDEX ... REORGANIZE` (online, resumable, updates no statistics) |
| > 30% | `ALTER INDEX ... REBUILD` (updates statistics with fullscan) |

Only consider indexes above roughly 1,000 pages; below that the index likely lives on mixed extents
and fragmentation is meaningless. On SSD and cloud storage the read-ahead penalty that motivated
aggressive defragmentation is largely gone.

Because reorganize does not update statistics, any maintenance plan built on reorganize needs a
separate statistics update step. Use Ola Hallengren's `IndexOptimize` rather than the built-in
Maintenance Plan wizard - it handles thresholds, statistics, time limits and resumability properly.

`ALTER INDEX ... REBUILD WITH (RESUMABLE = ON, ONLINE = ON, MAX_DURATION = 60 MINUTES)` lets a
large rebuild pause at a maintenance window boundary and resume later - a large operational
improvement for 24x7 systems.

## Columnstore

Clustered columnstore is the right choice for analytic tables: batch mode execution, 10x
compression, and segment elimination. It is the wrong choice for OLTP row lookups.

Things that decide success or failure:

- **Rowgroup quality.** Aim for close to 1,048,576 rows per rowgroup. Trickle inserts land in the
  delta store and stay row-oriented until the tuple mover compresses them. Load in batches of at
  least 102,400 rows to compress directly.
- Check `sys.dm_db_column_store_row_group_physical_stats` for undersized or open rowgroups and for
  the deleted-row count; a high deleted-row percentage needs a `REORGANIZE WITH (COMPRESS_ALL_ROW_GROUPS = ON)`.
- **Nonclustered columnstore on a rowstore table** supports real-time operational analytics - reports
  hitting the columnstore while OLTP continues on the clustered index. Consider it before building
  a separate reporting copy.
- Ordered clustered columnstore (2022) improves segment elimination when queries consistently filter
  on one column, at the cost of a more expensive load.

## Compression

Page compression typically yields 50-75% space reduction on real schemas, and because compressed
pages stay compressed in the buffer pool, it often *improves* IO-bound query performance at a small
CPU cost. Available in all editions since 2016 SP1.

```sql
EXEC sp_estimate_data_compression_savings 'dbo','Orders',NULL,NULL,'PAGE';
ALTER TABLE dbo.Orders REBUILD WITH (DATA_COMPRESSION = PAGE, ONLINE = ON);
```

Rule of thumb: PAGE for large, read-heavy or archival tables; ROW for hot tables with heavy update
churn; none for small tables where it does not matter. Compression is set per partition, so an
archive partition can be PAGE while the current one is ROW.

2022 adds XML compression for `xml` columns, which is worth checking on any schema that stores
documents or audit payloads as XML.

## Partitioning

Partitioning is a **manageability** feature, not a performance feature. Expect these benefits:
near-instant archival via `SWITCH`, partition-level rebuilds and compression, and partition
elimination when queries filter on the partitioning column.

Expect these costs: the partitioning column must be part of every unique index key; statistics are
maintained per table not per partition (incremental statistics help); parallel plans over many
partitions can behave unexpectedly; and it is a substantial schema change to reverse.

The sliding-window pattern - `SWITCH` the oldest partition out to a staging table, drop it, `SPLIT`
a new empty one at the top - turns "delete last year's rows" from an hours-long logged operation
into a metadata change.

## Data types and row width

Row width determines pages read, which determines almost everything else.

- Use the narrowest correct type. `bigint` where `int` suffices doubles that column everywhere,
  including in every index that carries the clustered key.
- `nvarchar` doubles storage over `varchar`. Justify Unicode per column, not per schema - though
  note 2019+ UTF-8 collations make `varchar` viable for Unicode data with far less space for
  Latin-script text.
- Avoid `(MAX)` types unless values genuinely exceed 8,000 bytes; they change how rows are stored
  and block some optimizations.
- Prefer `datetime2(n)` over `datetime` - more range, more precision, and `datetime2(0)` is smaller.
- Store UTC. `datetimeoffset` when the original offset is genuinely needed.
- Avoid `float` for money; use `decimal` with explicit precision.
- `sql_variant`, `text`/`ntext`/`image` (deprecated) and untyped `xml` all cause pain later.
