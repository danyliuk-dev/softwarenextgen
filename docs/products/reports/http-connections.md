# Refreshable HTTP JSON sources

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


HTTP connections fetch new source rows explicitly. Save project contains the
connection IDs/bindings and the last applied data snapshot. Opening a project and drill-down use saved snapshots. Generate preview refreshes
only HTTP connections that explicitly enable **Refresh HTTP data before each generation**.
Studio exports reuse the displayed snapshot. Disable automatic refresh to generate
offline when the source or host configuration is unavailable.

## Try the local example

The installed SDK includes a loopback-only sample service with synthetic records. Copy the SDK to a writable folder and open a terminal in that folder. Start the sample service:

```bash
python3 tools/http-source-fixture.py
```

Set `NEXTGEN_RESOURCES` as described in the [developer guide](developer-guide.md#start-the-installed-engine-for-integration). In another terminal, also opened in the copied SDK folder, start the installed engine with the example host catalog:

```bash
NEXTGEN_HTTP_SOURCES="$PWD/samples/http-sources.example.json" \
  NEXTGEN_STATE_DIRECTORY="$HOME/NextgenIntegration/reports" \
  "$NEXTGEN_RESOURCES/server/NextgenReports.Studio" \
  --contentRoot "$NEXTGEN_RESOURCES/server" --urls http://127.0.0.1:5274
```

In Manual, download **HTTP sales snapshot project**, then Open project. Its saved
snapshot totals 190.00. Data → **Connections** shows source `local_orders`, target
`items`, response array path `payload.rows`, and query binding `region` to report
parameter `region`. Set region to All and minimum to 10, then:

1. Choose **Refresh sources**. The preview shows three fetched rows, including
   HTTP-1 / West and HTTP-2 / East. The original source is unchanged at this point.
2. **Cancel** discards the fetched candidate. **Apply snapshot** replaces target
   arrays in Data and marks the report modified. Other root data remains intact.
3. Generate preview: the existing preparation rules run on the new snapshot,
   producing West 200.00, East 90.00, total 290.00. Scripts run only during report
   generation, if the host enabled them; refresh itself runs no scripts.
4. **Undo refresh** restores the previous raw JSON while leaving connection rules
   intact. It is a single-step action and is refused if data has changed since
   Apply. Generate again to reflect the restored data in the report.
5. Save project retains the applied snapshot and portable rules. Stop the source
   service: the saved report still renders/exports. A new refresh will fail and
   leave the existing data/report intact.

The fixture recognizes `region=East` / `West`, plus `Error` (503), `Redirect`
(302, intentionally rejected) and `Slow` (3-second response for Cancel checks).
These are test behaviors, not special handling in the report engine.

## Configure connections in Studio

Data → **Connections** loads the sources configured on the current host.
**Add connection** selects a source ID, a target root array name and an optional
dotted path in the JSON response. Leave the path empty when the response itself
is an array. Targets may replace existing arrays after preview/Apply; replacing
an object or scalar fails. Multiple connections cannot target the same name.

A source lists its allowed query names. Add bindings from those names to existing
string, number or boolean report parameters. Values are normalized using report
parameter defaults/validation, converted to scalar text and URL-encoded. No
string interpolation into URLs or headers occurs. Array parameters are not
supported. Fixed query values can be part of the host-configured URL.

**Save connections** validates definitions and host availability, changes the
report template and closes the dialog. It does not make an upstream request.
Global Undo/Redo restores connection definitions; raw data is unaffected.
Cancel discards editor changes. Use Refresh sources afterward to fetch rows.
A source marked unavailable is preserved in a loaded project; configure that ID
on this host to refresh it. Offline rendering needs only its saved snapshot.

Refresh requests all saved connections in order. Nothing is applied unless all
succeed. The preview shows up to 20 rows / 50 columns per target and truncates long
cells for display only. Apply verifies that template/data/parameters have not
changed since refresh started and that the resulting project fits 8 MB. Cancel
aborts the browser request; the server passes cancellation to upstream I/O. It
cannot undo a GET already received by an external service.

## Host catalog and authentication

`NEXTGEN_HTTP_SOURCES` points to a JSON file read once when Studio starts. If
unset, the catalog is empty and HTTP refresh is unavailable; offline reports
still work. Invalid host configuration fails startup. Restart after changes.
Use a private file outside version control for real endpoints. Only IDs, labels
and allowed query names are exposed by the catalog API.

```json
[
  {
    "id": "sales",
    "label": "Sales service",
    "url": "https://reports.example.com/api/orders?status=paid",
    "queryParameters": ["region", "since"],
    "headerEnvironment": {"Authorization": "SALES_AUTHORIZATION"}
  }
]
```

Set `SALES_AUTHORIZATION` in the Studio process environment to the complete header
value, for example a bearer authorization value supplied by your service. Values
are read at refresh time. They never enter the project, browser catalog, or
connection definitions. Missing/invalid environment values fail refresh without
sending a request. Do not put tokens into report parameters or project data;
those are saved as ordinary project contents. The example catalog has no secrets.

The host chooses exact HTTP(S) endpoints and allowed query keys. Projects cannot
supply URLs, paths to host files, header values or methods. Redirects are rejected,
cookies/default credentials are disabled, and response/error bodies are not
included in failure messages. HTTPS certificate verification remains enabled.
HTTP is supported for deliberate local/internal sources. This is still a local
Studio workbench, not an authenticated public reporting server.

## Fetch all pages

Pagination is configured by the host, not by a report template. The Connections
editor shows its mode, requested page size and page limit. Refresh collects every
page into one candidate; Preview reports the total rows and pages fetched.
For explicit refresh, only **Apply snapshot** replaces the current data. Cancel or any failed page
keeps the old snapshot and calculated report unchanged.

For the local example, open **HTTP sales snapshot project**, then Data →
Connections and select **Demo HTTP orders (page pagination)**, **(offset
pagination)** or **(cursor pagination)**. Keep path `payload.rows` and the region
binding. Save connections, Refresh sources: expect **3 rows · 2 pages fetched**.
Apply and Generate preview: total **290.00**. Undo refresh returns to the previous
snapshot. Region `PageError` fails on the second page; `PageSlow` delays the second
page so you can test Cancel. The saved portable project contains all applied rows
and source IDs, never host pagination configuration or credentials.

A trusted host catalog entry can use:

```json
{
  "id": "paged_sales",
  "label": "Sales (all pages)",
  "url": "https://api.example.com/orders",
  "queryParameters": ["region"],
  "pagination": {
    "mode": "page",
    "parameter": "page",
    "pageSizeParameter": "limit",
    "pageSize": 100,
    "start": 1,
    "maxPages": 50
  }
}
```

| Mode | Requests | End condition |
| --- | --- | --- |
| page | `page=start`, then start+1; `limit=pageSize` on each request | An array shorter than pageSize, including empty |
| offset | `offset=start`, then start+pageSize; set parameter to offset | An array shorter than pageSize, including empty |
| cursor | First request omits cursor; later requests send the returned token | Next cursor is null or an empty string |

For cursor mode set `mode` and `parameter` to `cursor`, omit `start` (or use 0),
and set `nextCursorPath`, for example `meta.next`. That dotted path must exist in
**every** response. Its value must be null or a string of at most 1,024 characters
without control characters. Numeric tokens, a missing path and repeated nonempty
tokens fail the refresh. Empty row pages may continue when a new token is present.
Tokens are URL-encoded query values on the configured endpoint: even a token that
looks like a URL is never followed as a link. Link-header/next-URL pagination is
not supported.

For page/offset modes, the source must honor the requested page size. A full final
page requires one additional empty page. If the page limit is reached before a
valid end condition, refresh fails instead of silently truncating. A response
larger than pageSize also fails. `start` defaults to 0; choose 1 for one-based
page APIs. Rows retain upstream page order; duplicate rows are not removed.
Use stable upstream ordering/snapshots to avoid changes between page requests.

Defaults: page mode, parameter `page`, size parameter `limit`, pageSize 100,
start 0 and maxPages 50. Size is 1–1,000, maxPages is 1–100 and start is
0–1,000,000,000. Paging query keys must be distinct and cannot collide with fixed
URL query keys or report-bound keys. Without `pagination`, existing single-request
sources behave as before. The public catalog exposes only mode, pageSize and
maxPages; endpoint details and cursor paths remain host configuration.

The installed client delegates paging to the configured engine. Call `ReportClient.RefreshDataAsync(input)` and retain the returned candidate only after a successful refresh; the host catalog controls pagination and credentials.

## Response contract and limits

- GET only, HTTP 200, `application/json` or `application/*+json`.
- UTF-8 JSON with depth at most 32; compressed responses are rejected. A host
  should return an uncompressed JSON body for the requested endpoint.
- Response selection must be an array of JSON objects, at most 10,000 rows across all pages per connection. Empty
  arrays are valid. Nested object/array fields inside a row are retained.
- At most 8 connections, 20 query bindings/connection, 1,024 characters/value,
  4 MB per HTTP response, 8 MB cumulative response bytes per connection, 8 MB combined refreshed data, and existing 8 MB project
  limit (which also includes template/parameters and formatting).
- Each request has a 15-second deadline including response-body reads. Each complete connection also has a 60-second deadline. Pages and connections
  run sequentially. Response-size bounds apply even without Content-Length.
- Host catalog: at most 50 sources, 20 allowed query keys/source, 10 environment
  headers/source. IDs/target/path segments are identifiers of 1–80 characters;
  dotted response paths are at most 240 characters. Reserved prototype identifiers
  are rejected. Fixed URL keys cannot also be declared as bound query keys.

The same connection can be used with different target/path/bindings. Fetches are
independent and do not form a transaction at the upstream service. Only applying
the local combined snapshot is atomic. OAuth login/refresh, POST requests and joins
are not implemented. Explicit server schedule jobs may refresh sources before
rendering; see [server operations](server-operations.md).
SQL, JSON files and .NET objects are available through the [shared catalog](data-sources.md).
Prepare data can transform applied rows using the existing derived-table pipeline.

## Template, API and CLI

```json
"connections": [
  {"source":"sales","target":"items","path":"payload.rows",
   "parameters":{"region":"selectedRegion"}}
]
```

The map is query key → report parameter name. `target` defaults to `items`, path
to empty and bindings to `{}`. Source must be supplied. Version remains 1; the
versioned schema includes these definitions. Template validation checks portable
syntax; it does not require a local catalog or network.

- `GET /api/data/sources`: public catalog metadata (no URL/header configuration).
- `POST /api/data/connections/check`: `{template}` validates host IDs/bindings,
  without network requests.
- `POST /api/data/refresh`: `{template,data,parameters}` returns
  `{data,sources:[{source,target,rows,pages}],retrievedAt}`. Data is the complete candidate
  snapshot; the timestamp describes this fetch, not the age of upstream records.
  Errors use HTTP 400; existing same-origin checks still apply.

With the installed .NET SDK, call `ReportClient.RefreshDataAsync(input)` for an explicit refresh. Configure trusted sources in the installed engine host catalog.

```bash
# Fetch candidate JSON only (does not overwrite the input file).
python3 tools/report-tool.py --template samples/http-connections.nrtemplate \
  --data samples/http-connections.data.json --format refreshed-data \
  --output artifacts/refreshed-data.json
# Explicit refresh, then generate and save a portable project with the new snapshot.
python3 tools/report-tool.py --template samples/http-connections.nrtemplate \
  --data samples/http-connections.data.json --refresh --format project \
  --output artifacts/refreshed.nrproject.json
```

`--refresh` runs before rendering or drill-down. Without it, all previous formats
use supplied data as before. `refreshed-data` returns the response envelope and
`pages: null`; `--refresh` with that format does not fetch twice. The standalone
.NET CLI remains offline: supply the selected snapshot as its data file.
Verified locally on Linux iMac; macOS and Windows remain unverified.

## Automatic HTTP refresh before generation

Runnable example: `samples/http-auto-refresh.nrtemplate` and matching data file,
also downloadable from Manual. With the existing HTTP fixture/catalog configured,
Open shows saved 190.00 and Generate fetches 290.00.


In **Data → Connections**, select an HTTP source, enable **Refresh HTTP data before
each generation** and save. The portable connection stores `"refreshOnRender":true`;
omission/false retains the existing offline behavior. This option is HTTP-only.

Click **Generate preview** (or run with parameters). Studio fetches every opted-in
connection, including all configured pages, before preparation/scripts/layout.
Only a successful generation replaces the editable snapshot and displayed report.
A failed source/page or report leaves previous data and preview intact. Other root
fields and connections without the option retain their snapshots. A successful
automatic refresh clears the older Undo refresh entry; save the project to retain
its new data. Opening a project/Library version and drill-down do not fetch.

PDF, HTML, images, Excel and Word exported from Studio reuse the data that produced
the displayed report. They do not fetch again, even if the HTTP service changed
or is unavailable. Trusted time-dependent report scripts can still differ when
exports regenerate layout. Uncheck the option to generate offline from saved data.
An enabled option with an unavailable host source fails generation explicitly.

For API hosts, `/api/preview`, `/api/render` and `/api/export/*` refresh opted-in
HTTP connections by default. Preview adds `sourceSnapshot` only after a successful
automatic refresh. To export the same data, submit it as `data` and set request-level
`"useSnapshot":true`. That flag also allows explicit offline preview/export.
Independent requests without the flag fetch independently; SDK hosts must account
for that when regenerating downloads. The Python client supports `--use-snapshot`; `--refresh` fetches once before
generation and project output retains automatically refreshed data. .NET and Dart
ReportInput accept useSnapshot for the same behavior. The direct .NET engine and standalone CLI
remain offline; hosts can call `DataSourceCatalog.PrepareRenderAsync` before Render.

Schedules honor connection-level automatic HTTP refresh even when their global
Refresh checkbox is off. Global Refresh refreshes all sources once, including
opted-in HTTP connections; it does not fetch them twice. Stored Library versions
are never rewritten by a scheduled run. Viewer saved-version PDF stays offline.
Existing HTTP endpoint, pagination, timeout and size limits still apply. This is
fetch-on-generation, not polling or background synchronization of an open editor.
