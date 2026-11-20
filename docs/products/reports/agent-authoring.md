# Authoring reports with Codex or another agent

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


Templates are editable JSON files, not UI state. No model-specific SDK or
API key is needed. The current engine supports text, tables, embedded PNG/JPEG,
parameters, flow pagination, fixed frames, page breaks and optional TypeScript events. Numeric table expressions and flow master-detail tables and horizontal/vertical grouped, stacked and percentage bar charts and categorical line charts with up to three series and a shared-scale legend and Code 39, Code 128 B, EAN-13, EAN-8, UPC-A, QR Code and Data Matrix barcodes and flow cross-tabs with up to three measures and three levels per axis are supported (see template-format.md). Do not invent
inline SQL queries or credentials (use configured source IDs), unsupported chart/barcode types, general-purpose formulas or MRT compatibility.

## Workflow

1. Read the user's requested content, page format and actual data structure.
   Read docs/template-format.md and the schema at
   /schemas/report-template-v1.schema.json (also in Studio/wwwroot/schemas).
   The schema describes authoring structure; the engine is authoritative for
   cross-field constraints, bindings, text fitting and pagination.
2. Create or edit a .nrtemplate file. Preserve unrelated fields. Keep data and
   parameter values in separate JSON files. Use fictional data for examples.
   Do not insert $schema into a template: unknown fields are rejected.
3. Bind text with {{data.path}} / {{parameters.name}}. Table source is a data
   array path, and column field paths are relative to each row.
   Use flow tables for variable-length lists. Fixed frames use points relative
   to the content area of the current page and reject height overflow.
4. Validate against a running local Studio with the client below.
   On nonzero exit, read the JSON error, correct the template and rerun.
5. Inspect calculated pages in Preview and inspect exported PDF for printing.
   Browser SVG text placement may differ slightly from PDF rasterization.
   Deliver the template, sample data and requested outputs; report limitations.

    python3 tools/report-tool.py --template samples/positioned-table.nrtemplate --data samples/positioned-table.data.json
    python3 tools/report-tool.py --template samples/positioned-table.nrtemplate --data samples/positioned-table.data.json --output artifacts/preview.json
    python3 tools/report-tool.py --template samples/positioned-table.nrtemplate --data samples/positioned-table.data.json --format pdf --output artifacts/report.pdf

Add --parameters parameters.json for parameter values, --base for another
local endpoint. Success returns {"ok":true,"pages":1,...}; failures return
{"ok":false,"error":"..."} on stderr and exit 1. No output file is touched
until the server succeeds. Running without --output validates without saving.

## HTTP contract

POST /api/preview and POST /api/render accept
{"template":{...},"data":{...},"parameters":{...}}.
Preview returns {title,pages:[{width,height,commands:[...]}]}.
Commands are tagged with type=text|rect|image|line|polygon; coordinates are points;
image bytes are base64; text includes its resolved style. Lines use x1/y1/x2/y2, color and strokeWidth; consumers must render them for line charts. Polygon commands contain points [{x,y},...] and fill; close the shape and use even-odd fill for circular-chart holes.
PDF export returns application/pdf with X-Report-Pages.
Validation failures return HTTP 400 Problem Details with a detail string.
Preview validates layout; PDF export additionally validates PDF image decoding.

GET /schemas/report-template-v1.schema.json exposes the authoring schema.
This is a local, unauthenticated workbench. Do not send private datasets
to an external model or expose the server publicly without explicit authorization.

This foundation lets Codex create reports through files and API today.
An in-app prompt assistant, MCP server and automatic template application
are not implemented yet.

## Portable Studio project

Create a validated bundle for the user to open with Studio's Open project:

    python3 tools/report-tool.py --template samples/positioned-table.nrtemplate --data samples/positioned-table.data.json --format project --output output/example.nrproject.json

A project is UTF-8 JSON containing kind="nextgen-report-project", version=1,
template, data and optional parameters. The schema is available at
/schemas/report-project-v1.schema.json. The template schema remains unchanged.
The CLI validates layout through the API before writing a project.
Projects are limited to 8 MB and include the data, so share them deliberately.

Open project validates layout and decodes browser images before replacing the
current document, then opens Preview. A rejected file leaves current edits intact.
A successful import resets template-only Undo/Redo history, avoiding restoration
of a previous template against unrelated data. Save project saves the current
draft including unsaved edits and parameters; it does not validate layout.
Use Save template when data should not be included. No server storage is used.

## TypeScript authoring

Read docs/report-logic-manual.md before creating logic. Only named synchronous
validateParameters, beforeRender, afterRender, dialogLoad, parameterChanged, dialogButtonClick, dialogPageChanged and dialogPageChanging handlers exist. Use /api/logic/check
for types, then /api/preview with actual data/parameters. Script hosts must explicitly
enable trusted scripts. For dialog drafts use DialogContext / ParameterChangedContext and return DialogUpdate;
verify with /api/dialog/event. Do not invent imports, arbitrary DOM events, C# callbacks,
decimal helpers or undocumented component APIs. Store source in logic.source.

For custom buttons set kind="button", action="custom" and a unique id. Use
DialogButtonContext.componentId to dispatch actions and return DialogUpdate.
POST /api/dialog/event uses event="dialogButtonClick" and componentId="button-id".

DialogUpdate also accepts `components: { "component-id": { visible?: boolean, enabled?: boolean } }`.
Patches merge for the open dialog only; closing/resetting clears them. Containers
propagate state to children; individual TabPage patches are not supported.
Use existing unique IDs. Hidden/disabled values still undergo server validation.

Use `DialogUpdate.options` keyed by parameter name to replace choices of
select/list/radio/checkedList controls. Values are 0–200 unique nonblank single-line
strings, each at most 500 characters. Return `parameters` in the same patch to
select new values; nonempty selections must belong to the new options. Otherwise
Studio preserves valid selections and clears removed ones. Cancel discards options.
Generate uses an effective template with updated options for server validation and
PDF; Save project includes those choices, while Save template keeps the design.

Use `dialogPageChanged(ctx: DialogPageContext): DialogUpdate` for user-selected
TabPage changes. `ctx.componentId` is the selected page ID. Initial selection,
validation reveals and design previews do not execute this handler. The event
notifies after selection; it cannot cancel navigation.

For step buttons, use `kind: "button"` and `action: "next"` or `"back"` inside a
TabPage (optionally in a nested Panel/GroupBox). Navigation uses the nearest
TabControl's page order. Next validates current-page browser constraints, Back
preserves incomplete drafts, and boundary buttons are disabled. Direct tab
selection remains available; server validation still runs on Generate.

Set `sequential: true` on a `tabs` component to require Next for forward user
navigation. Add Next buttons inside intermediate pages. Back/earlier headers
remain available; forward headers are re-blocked after returning. The default is
false. Automatic validation reveals may open any page; this setting is not a
server-side workflow or authorization boundary.

Use `dialogPageChanging(ctx: DialogPageChangingContext): DialogNavigationResult`
to veto user tab/Back/Next navigation. Source is `previousComponentId`, destination
is `componentId`; both must be distinct pages of one TabControl. Return only
`{cancel?: boolean, message?: string}`. No patches are allowed here. Initial
selection, validation reveals and design preview bypass the handler; validate
final report requirements separately in validateParameters.

For nested cross-tabs use rowFields/columnFields (up to three distinct paths, outermost first). See template-format.md and samples/cross-tab-hierarchy.nrtemplate. Row labels repeat on separate lines. Set mergeColumnHeaders: true to merge column-axis parent headings across children and measures (default false); complete headers repeat on each page. Set mergeRowLabels: true for separate level columns and page-local vertical merging; parent labels repeat on continuation pages. Each label column has weight 2 and counts toward the 50-column limit. Each matrix row must fit below the header in this mode, otherwise generation fails. Optional showRowSubtotals/showColumnSubtotals (default false) add parent subtotals after their children, using source records. Count these extra column groups when checking width and the 50-column limit.

Delimited data can be imported through POST /api/data/import or tools/import-delimited.py; see [data-import.md](data-import.md). Preview normalized keys/types before binding them. This is a one-time conversion, not a live connector.

Standalone HTML: Studio **Preview → Export HTML**, `report-tool.py --format html`,
or `.html` output from the .NET CLI. All pages, fonts and images are embedded.
See [authoring manual](report-authoring-manual.md) for workflow and limitations.

Nested table filters: `filterGroup` combines AND/OR subgroups with typed constants
and run parameters (3 levels, 10 groups, 20 conditions). Use **Use grouped filters**
in table properties; sample: `samples/nested-filters.nrtemplate` with
`samples/grouped-orders.data.json`. See the authoring manual for steps and limits.

Calculations and conditional cell styling: `samples/conditional-table.nrtemplate`
with `samples/conditional-table.data.json` demonstrates if/coalesce/isNull, numeric
comparisons/logic, guarded division, parameterized discounts and ordered color
rules. In Design, use column Expression and Add style rule; see the authoring
manual for precedence, null behavior, priority and limits.

Repeated document sections: `samples/repeated-sections.nrtemplate` with
`samples/repeated-sections.data.json` creates two complete order packs. Use
Insert → Repeat section and Edit section; data/root/parent bindings, nested
Flow blocks and navigation are described in the authoring manual/template format.
Save/export always includes the whole report, even while editing a child section.

Text/calendar expressions: `samples/text-dates.nrtemplate` and matching data
demonstrate inline `{{= ... }}` and table `textExpression`, strings, null fallback,
number/date formatting and calendar deadlines. See the manuals for functions,
contexts, ISO dates, numeric-column compatibility and limits.

Matrix barcode labels: `samples/matrix-barcodes.nrtemplate` and matching data
create independent repeated QR/Data Matrix labels. Set symbology to `qr` or
`dataMatrix`; module width determines automatic square size, QR correction uses
L/M/Q/H, and optional captions wrap below the quiet zone. UTF-8 payload limit is
512 bytes. See the authoring manual/template format for print sizing and limits.

Composition charts: `samples/circular-charts.nrtemplate` with matching data
shows pie/donut charts. Choose Chart type, Slice colors, Show percentages and
Donut hole ratio in Design. Up to 12 nonnegative rows and one measure; see manuals
for legends, zero data, rounding, sizing and the polygon preview command.


Static diagnostics are available through `POST /api/template/check` with
`{"template": {...}}`. The response is `{"diagnostics":[{"path":"$.blocks[0]",
"message":"..."}]}` (HTTP 200 even for template issues). Paths are zero-based;
`$` denotes a parse/global error. The endpoint reports the first error per invalid
block, stops on global errors, and never executes scripts or validates data/layout.
An empty list does not replace validation of the actual template/data pair.


For XLSX source data, use `tools/import-xlsx.py --list-sheets`, then select a
worksheet with `--sheet` and write a data JSON using `--table`/`--output`. Review
warnings; `--use-cached-formulas` is explicit and never recalculates formulas.
Validate the resulting actual template/data pair with report-tool.py as usual.
See [XLSX import contract](data-import.md#excel-worksheets-xlsx).


For PNG/SVG delivery, validate the actual template/data pair with report-tool.py
using --format png|svg, --first-page/--last-page and --dpi. ZIP is the default;
--single-image requires a one-page selection for a standalone image. Use the
correct output extension and inspect the exported artifact. SVG outlines are not
searchable text. See [page image export](image-export.md).

## Office delivery

Use `--format xlsx|docx --office-mode editable|pages` in `report-tool.py`; ranges
and DPI follow image export. Editable mode exports displayed text strings, not
typed source cells or formulas, and omits graphics. Page mode embeds complete PNG
pages. Explain these limits when delivering Office files; validate the actual
input pair and inspect output. See [Office export](office-export.md).

## Interactive detail reports

Table `drillDown` embeds a v1 template; it is not an external subreport. Detail
inputs are `data.row` (original selected record) and `data.source` (parent data
after beforeRender), plus same-named inherited parameters. See
[Row drill-down](drill-down.md). Validate both the parent and actual child
requests: `report-tool.py --drill-row 13 --drill-row 1` selects nested interactive
rows using 1-based render-order indexes. Static exports use only the selected
view; preserve the root project separately.

## Prepare derived data without scripts

Use template `dataTables` for filter/sort/project/decimal-expression and grouped
aggregate pipelines. Output names must be new root identifiers; later definitions
may read earlier outputs. Point report blocks to these derived table names.
Rules run before trusted script events; keep raw data in project data. Do not feed
prepared output back into the same template. Validate the actual template/data
pair with `tools/report-tool.py`; `--format prepared-data` additionally returns
the computed arrays without scripts/layout. See [data-preparation.md](data-preparation.md)
for semantics, bounded limits, example and API contract.

## HTTP source snapshots

Use `connections` only with host-configured source IDs. Keep URLs/headers/secrets
out of templates and project files. The saved raw snapshot supports offline
rendering. HTTP refresh may be explicit or opted in with refreshOnRender:true.
Use report-tool.py --use-snapshot for offline validation of such projects. `report-tool.py --refresh` refreshes
before generating/saving, while `--format refreshed-data` retrieves only the
candidate response. Validate/render the actual updated template/data pair before
delivery. See [http-connections.md](http-connections.md) for bindings and limits.

## SQL, JSON and object sources

See [data-sources.md](data-sources.md) for all five SQL providers, JSON files,
.NET object callbacks and direct POCO/JSON inputs. Connections keep only host IDs,
target arrays, paths and report-parameter bindings. SQL query overrides require
allowQueryEditing:true in the host catalog; credentials and file paths stay on the host. SQL uses an empty path; JSON/objects may
select a nested array. Refresh previews a candidate; Apply saves the snapshot.
Server generation refreshes opted-in HTTP connections; useSnapshot:true bypasses it. Validate the template against its
actual saved data, including when the source is unavailable. The manual includes
an offline example with total 10.00 and configured refresh to 290.00.

## Host library

Validated portable projects may be saved to the host library through
`POST /api/library`; see [report-library.md](report-library.md). Library saves
perform structural validation only, so continue to validate the actual template/data
pair with report-tool before delivery. Respect expectedVersion conflicts; never
automatically resubmit against a newer base. Downloaded projects remain portable
and contain no library identity.

## Authenticated server

Use report-tool `--user NAME --password-env ENVIRONMENT_NAME` for Author/Admin
sessions; passwords are never command arguments. Viewer can read stored reports
and generated artifacts, but cannot submit arbitrary templates. Admin schedules
pin an explicit library version; updates never silently follow latest. See
[server-operations.md](server-operations.md) for roles, CSRF and schedule APIs.

## .NET / Blazor integration

Use `NextgenReports.Client` for session-aware HTTP generation with JSON or .NET
objects; `NextgenReports.Blazor` supplies an Interactive Server viewer. See
[the integration guide](dotnet-integration.md) and `examples/BlazorDemo`.
One client/cookie jar per user; Author/Admin required for POST generation.
Construct a new `ReportInput` for edits; exports use the successful input snapshot
but rerun generation. Flutter has a separate [Dart/Flutter SDK](flutter-integration.md); WebAssembly is not covered by the .NET SDK.

## Compose report packs

Use `section` for independent page settings and `subreports` plus a `subreport`
block for imported v1 template snapshots. See the template format for data scopes,
parameter inheritance and limits. Import files into the dictionary before delivery;
never invent a runtime file/URL resolver. Validate the complete combined pair with
`report-tool.py --template samples/composed-report.nrtemplate --data samples/composed-report.data.json`.
Expect four pages: cover, landscape overview, portrait order and closing page.
