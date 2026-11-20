# SQL, JSON and .NET object data

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


All sources produce an ordinary JSON snapshot. **Data → Connections** selects
host source IDs and binds report parameters; **Refresh sources → Apply snapshot**
replaces the selected root arrays only after every connection succeeds. Cancel or
failure leaves the previous snapshot intact. Generate preview uses that snapshot
unless an HTTP connection explicitly enables refresh before generation. Studio
exports reuse the displayed snapshot. Save project keeps it for offline use. **Undo
refresh** restores the prior data if you have not edited it since Apply.

## JSON without a database

Studio already accepts **Upload JSON**, raw JSON in Data, and `data` in API
requests. The root is an object, e.g. `{"items":[{"amount":12.34}]}`. Nested arrays
are supported by report source paths. Dates use ISO strings. These are direct
inputs, with no host configuration required.

For explicit refresh from a file, create a host catalog containing:

```json
[{"id":"json_demo","label":"Sales JSON","provider":"json","file":"source-objects.json"}]
```

Start Studio with `NEXTGEN_DATA_SOURCES=/absolute/path/to/catalog.json`.
Relative JSON paths resolve against the catalog directory. The file must contain
an array of objects, or an object with a nested array. In Connections select
json_demo, target items, path rows for `samples/source-objects.json`, and no
parameter bindings. Refresh, Apply, Generate: the sample total is 290.00. Editing
the file affects the next explicit refresh. A project cannot choose host paths.
The catalog is read at startup; restart after catalog changes.

## SQL host setup

`NEXTGEN_DATA_SOURCES` accepts these provider IDs:

| Provider | Driver | Connection environment example (synthetic local setup) |
| --- | --- | --- |
| postgresql | Npgsql | `Host=localhost;Database=reports;Username=report_reader;Password=...` |
| mssql | Microsoft.Data.SqlClient | `Server=localhost;Database=reports;User ID=report_reader;Password=...;Encrypt=True` |
| mysql | MySqlConnector | `Server=localhost;Database=reports;User ID=report_reader;Password=...` |
| mariadb | MySqlConnector | Same form as MySQL |
| sqlite | Microsoft.Data.Sqlite | `Data Source=/absolute/path/reports.db` |

Configure actual server certificate trust normally; credentials stay in the
Studio process environment. Use a database principal with **SELECT only on the
required tables/views**, especially for SQL Server. Queries default to trusted host configuration. The host may explicitly enable
project SELECT overrides and schema browsing as described below. The SELECT guard is not an SQL sandbox:
server functions and permissions remain the host administrator's responsibility.
SQLite opens read-only; PostgreSQL/MySQL/MariaDB use read-only transactions.
Every SQL fetch uses a separate transaction that is rolled back after reading.
There is no transaction spanning sources, and no shared consistent database
snapshot across connections. SQL Server depends on its read-only principal.

```json
[{
  "id":"sales", "label":"Sales", "provider":"postgresql",
  "connectionEnvironment":"REPORTS_DATABASE",
  "query":"SELECT id, region, amount FROM orders WHERE region=@region ORDER BY id",
  "parameters":{"region":{"type":"string"}}
}]
```

Set REPORTS_DATABASE to the connection string. Define a string report parameter
selectedRegion. In Connections choose sales, target items, **empty array path**,
and add source binding region → selectedRegion. Save checks names and bindings;
it does not connect. Set a region, Refresh, inspect rows, Apply, Generate. Existing
Prepare data rules can transform the snapshot afterward. SQL aliases must be
unique identifiers; quote an alias when the database requires it.

`samples/data-sources.example.json` includes all five SQL definitions plus JSON.
Only use IDs configured for your host; an unused definition does not connect.
Download **SQL, JSON and objects snapshot project** in Manual. Its offline total
is 10.00. For the SQL example create an orders table with id, region and numeric
amount columns, with West=200 and East=90. Select the matching *_demo source,
bind region → region, then All refresh yields 290.00; East yields 90.00. The
example does not provision databases or accounts.

Queries must be one SELECT (optional final semicolon), at most 16,000 characters.
No comments, dollar quoting, CTE/WITH, stored procedures, multiple statements or
DML/DDL. Use database views for complex logic. Parameters are named @name; their
names must match host definitions exactly. Values use driver parameters, never
SQL interpolation; table/column names cannot be bound.

Types: string (4,000 characters), int64, decimal, boolean, date (`yyyy-MM-dd`),
datetime (`yyyy-MM-ddTHH:mm:ss[.fffffff]`, no offset), datetimeoffset (explicit Z
or offset), guid. Numeric bindings require JSON numbers, booleans JSON booleans;
report defaults/validation run first. A nullable source parameter may be left
unbound to send SQL NULL. Optional report parameters may normalize empty input
to an empty string: omit the source binding when NULL is intended.
PostgreSQL offset timestamps normalize to UTC; MySQL/MariaDB receive UTC datetime.
SQLite ignores precision/scale metadata and uses its dynamic storage types.
Decimal values use .NET decimal range/precision. SQL dates/times become ISO text,
binary becomes base64, NULL becomes JSON null. Unsupported provider values fail;
use SQL casts for arrays, spatial types or provider-specific objects.

## Browse a database and edit SQL

Runnable example: `samples/sql-workbench.nrtemplate` with `sql-workbench.data.json`.
Download its project from the built-in Manual. It opens offline at 10.00; enable
query editing on sqlite_demo to refresh All=580.00 / East=180.00.


A host operator enables this per SQL source by adding `"allowQueryEditing": true`
to its catalog definition, then restarting Studio. Existing sources default to
false. This exposes the configured query to signed-in users and lets Authors and
Admins browse metadata and submit alternative SELECTs using that source's database
account. Enable it only for trusted authors with a SELECT-only database principal
limited to the intended tables/views; the query guard is not a security sandbox.
Connection strings, passwords and environment-variable names remain on the host.

```json
{
  "id": "sales", "label": "Editable sales", "provider": "sqlite",
  "connectionEnvironment": "REPORTS_DATABASE",
  "allowQueryEditing": true,
  "query": "SELECT id, region, amount FROM orders WHERE region=@region",
  "parameters": { "region": { "type": "string" } }
}
```

1. In **Data → Connections**, choose this source and bind region to an existing
   report parameter. Click **Browse / edit SQL**.
2. Click **Browse database**. Filter table/view/column names, expand a table and
   inspect column types/nullability. Click a table or column button to insert its
   quoted SQL identifier at the editor selection. This does not construct joins.
3. Edit the highlighted SELECT, for example:

   ```sql
   SELECT id, amount * 2 AS amount
   FROM orders
   WHERE region = @region
   ORDER BY id
   ```

4. Click **Preview query**. For the synthetic East=90 example, expect one row with
   amount=180. The first 20 rows are displayed; the report snapshot is unchanged.
   Editing SQL clears the previous preview. Errors do not apply partial data.
5. Click **Use query**, then **Save connections**. This validates the query and
   bindings and saves the override in the project. **Cancel** discards edits.
6. **Refresh sources → Apply snapshot → Generate preview** uses the saved query.
   Save/reopen the project to retain SQL and the last applied data. Opening a
   project remains offline. Clear the SQL override to return to the host query.

Parameters remain host-defined: use exactly the declared `@names`, with the
existing report bindings and types. Preview executes one connection only. Query
text stays limited to 16,000 characters, one SELECT, 15 seconds, 10,000 rows,
100 result columns and 4 MB. SQLite additionally caps each native row/value at
4 MB and reads virtual-table text without native blob-metadata probing.

Schema discovery returns up to 500 tables/views and 10,000 column records in the
current database, subject to account visibility. It lists ordinary column type
and nullability, not keys, relations, indexes or stored procedures. SQLite excludes
internal tables and hidden/generated columns. Provider errors are sanitized.
No host catalog/credential editing or database writes are exposed by Studio.
Removing the host opt-in prevents further query preview/refresh; saved snapshots
remain usable with refresh disabled.

API (Author/Admin, authenticated session and CSRF):

POST `/api/data/schema`:

```json
{ "source": "sales" }
```

`POST /api/data/query/preview` accepts `{template,parameters}` with exactly one
SQL connection and returns a normal refresh candidate. A connection may include
`"query":"SELECT ..."`; omission/empty text uses the host query. The catalog adds
`allowQueryEditing` and, only when enabled, `query`. Schema results contain
`schema`, `name`, `kind`, `sqlName`, and `columns` with name/type/nullable/sqlName.

Live schema browsing and edited-query execution were verified on SQLite on the
Linux iMac. The implementations cover PostgreSQL, SQL Server, MySQL and MariaDB;
new schema browsing against those servers remains unverified in this stage.
Existing PostgreSQL/MySQL/MariaDB refresh verification remains valid historically.

## .NET objects and JSON strings

Use the installed `NextgenReports.Client` package to send ordinary objects or JSON to the installed engine:

```csharp
using NextgenReports.Client;
using var client = ReportClient.Create(new Uri("http://127.0.0.1:5274/"));
// template is a JsonElement loaded from your .nrtemplate file.
var input = ReportInput.FromObjects(template,
    new { items = new[] { new { id = 1, amount = 12.34m } } });
var file = await client.ExportAsync(input, ReportFormat.Pdf);
await File.WriteAllBytesAsync("report.pdf", file.Content);
```

Property names are preserved: the template must bind `items`, `id` and `amount` with matching case. For existing JSON, construct `ReportInput` with JsonElement values. Inputs own a snapshot; create a new input after changing the objects. Load database/service data in your application, then send the resulting objects. Credentials stay in your application or the engine's configured source catalog.

The installed engine supports configured SQL/JSON/HTTP sources; configure them as described above. It does not load arbitrary C# callbacks from a report or JSON catalog. To refresh application-owned objects, query your service again and submit a new input. The optional `NEXTGEN_OBJECT_DEMO=1` host setting exposes a synthetic demonstration source only.

## Limits, API and verification

Up to 50 sources total (including HTTP), 8 connections/project, 20 bindings/source,
10,000 object rows/source, 100 SQL columns, 4 MB/source, 8 MB combined data and
existing 8 MB project limit. SQL text/binary fields are limited to 262,144
characters/bytes. Each fetch has a 15-second deadline; SQL commands also have a
15-second timeout and SQLite receives an interrupt on cancellation. Callbacks
must cooperate. Missing files, connection failures and provider errors return
sanitized errors; Connection strings and file paths stay out of browser metadata and projects.
SQL is exposed and stored only for sources with query editing enabled. Ordinary report data/parameters are saved, so do
not put credentials there.

The same `/api/data/sources`, `/api/data/connections/check`, `/api/data/refresh`
and Python `report-tool.py --refresh` protocol applies to HTTP, SQL, JSON and
objects. Catalog entries add provider and typed parameter metadata. The standalone
.NET CLI remains offline. See [HTTP refresh](http-connections.md) for the complete
snapshot/API workflow and automatic HTTP refresh. A visual join builder and
distributed transactions are not provided.

Verified on Linux iMac with actual PostgreSQL, MySQL, MariaDB and SQLite. SQL
Server driver creation/typed binding is tested; a live SQL Server connection is
**not yet verified**. macOS/Windows are also unverified.

Driver documentation: [Npgsql](https://www.npgsql.org/doc/basic-usage.html),
[SqlClient](https://learn.microsoft.com/en-us/sql/connect/ado-net/connection-strings),
[MySqlConnector](https://mysqlconnector.net/connection-options/),
[SQLite](https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/connection-strings).

Metadata references: [PostgreSQL tables](https://www.postgresql.org/docs/current/infoschema-tables.html), [SQL Server tables](https://learn.microsoft.com/en-us/sql/relational-databases/system-information-schema-views/tables-transact-sql), [MySQL columns](https://dev.mysql.com/doc/mysql-infoschema-excerpt/8.0/en/information-schema-columns-table.html), [SQLite table_info](https://www.sqlite.org/pragma.html#pragma_table_info).
