# Row drill-down and detail reports

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


Drill-down opens an embedded detail report from a rendered table row. It is a
Viewer action: it does not insert pages into the parent report or load a remote
file. Up to three detail levels are supported. Ordinary templates remain
noninteractive unless a table has a `drillDown` definition.

## Try the example

1. Save your current project. In the built-in manual, download **Interactive
   orders project**, then open it using **Open project**. The matching source
   files are `samples/drill-down.nrtemplate` and `samples/drill-down.data.json`.
2. Preview contains 18 orders on multiple pages. The strip above the page controls
   identifies interactive rows. Hover a row to see its outline/action label;
   click it, or focus it with Tab and press Enter/Space.
3. **Order details** shows the selected customer's order lines. Select a line
   to open **Line details**. The breadcrumb shows the current report path.
4. Choose **Back** to return one level. The parent's calculated document, page,
   zoom, search and scroll position are restored without regenerating it.
5. Export PDF, HTML, images or Office while a detail is open: the file contains
   the displayed detail report. Back changes export back to the parent.

The root template/data editors and parameter fields remain the root project's
editors. Save project and Save template preserve that root, including all
embedded detail templates. Unfinished edits do not affect a drill-down click.
A successful Generate preview or project load starts a new root and clears
navigation history. A failed detail request displays an error and leaves the
parent view/request/history intact. There is no URL history, forward button,
automatic detail parameter dialog, or persistence of the navigation stack across
reloads.

## Configure a table

1. Select an ordinary Table in Design, including a table inside a repeated
   section. Choose **Add row drill-down** / **Edit row drill-down** in Properties.
2. Set an action label (1–120 characters). The label appears in the hover tooltip
   and the accessible row name; it is plain text, not a binding or URL.
3. Paste a complete v1 detail-template JSON, or import a `.nrtemplate`/`.json`
   file (up to 2 MB). Create that template in a separate Studio project if a
   visual editor is preferred, then export its template and import it here.
4. Use `{{data.row.id}}`, `{{data.row.customer}}`, etc. for the selected record.
   A child table can use `source: "row.lines"`. `data.source` is the complete
   parent report data after its beforeRender event. It is not the enclosing
   repeat/master record. For a second-level detail, `data.source.row.id` refers
   to the first selected record.
5. Apply runs static validation before changing the parent template. Invalid
   JSON, page settings, blocks or excessive detail nesting leave the dialog open.
   Generate and open an actual row to check runtime data bindings and parameters.
6. Cancel discards changes. **Remove drill-down** removes only the table action.
   Apply/remove participate in the existing Undo/Redo history. Save project keeps
   the definition inline; no external template file is needed afterward.

A minimal table action:

```json
{
  "type":"table", "source":"orders",
  "columns":[{"title":"Order","field":"id"}],
  "drillDown":{
    "label":"Open order details",
    "template":{
      "version":1, "title":"Order details",
      "blocks":[{"type":"text","text":"Order {{data.row.id}}"}]
    }
  }
}
```

Flow, Fixed, grouped, sorted, filtered, master-detail and repeated-section tables
all associate actions with the **original source row**, after filtering/sorting.
Calculated display columns do not become fields in `data.row`. A split row has
one action on each page fragment, all selecting the same record. Headers, group
bands and totals have no actions. Charts, cross-tabs, standalone text and images
do not provide drill-down actions in this stage. Empty tables have no actions.
In master-detail tables the selected record is the child row; retain a parent ID
in your data if the detail needs it.

## Parameters, scripts and exports

Only normalized parent parameters whose names are declared by the detail
are inherited. Others are omitted; detail defaults/required/type/choice/range
rules apply normally. There is no implicit conversion or field-to-parameter
mapping. Use `data.row` for row values. Detail dialog Load/Change events are not
run; supply inherited values or defaults. Missing required values are reported
when opening the row.

The parent is not rerun on navigation: source data and row values come from the
calculated parent snapshot, including beforeRender output. The selected detail
runs its own events under the host's existing trusted-script opt-in. Back restores
cached pages without rerunning either report. Export follows the saved request
of the currently displayed report and reruns that report's scripts, as existing
PDF/HTML export does; time/random-dependent scripts may change its values.

All file exports are **static**. PDF/HTML/PNG/SVG/XLSX/DOCX do not contain clickable
drill-down actions, the navigation stack, embedded detail definitions or hidden
source fields merely because the parent had drill-down. Generated page content
itself still follows the selected template. Save the project for interactivity.

## Protocol and CLI

`POST /api/preview` still accepts template/data/parameters. Interactive results
add an optional `drillDown` object:

- `source`: owned snapshot of the parent data after beforeRender;
- `parameters`: normalized parent parameters;
- `targets`: deduplicated action label/detail-template definitions;
- `rows`: zero-based target index and the original record;
- `regions`: zero-based page/row indexes plus x/y/width/height in page points.

The context contains entire records and parent data, including fields not drawn
on the page. Preview JSON is therefore a data-bearing artifact; use static
exports when only rendered content is intended. The object is omitted when there
are no interactive rows. Drawing commands remain unchanged for existing clients.

To open a region, look up `rows[region.row]` and its target. Submit that target's
template to `/api/preview` with `data: {row: selectedRow, source: context.source}`
and matching inherited parameters. The existing same-origin, request-size and
script rules apply. .NET callers can use `DrillDown.Open(document, rowIndex)` to
construct a `ReportDetailRequest`, then call the ordinary engine/exporter.

With Studio running:

```bash
# Validate the parent, then export order 13's first detail line.
python3 tools/report-tool.py --template samples/drill-down.nrtemplate \
  --data samples/drill-down.data.json --drill-row 13 --drill-row 1 \
  --format pdf --output artifacts/line-detail.pdf
```

CLI row numbers are **1-based indexes of the interactive rows**, in table/render
order after filtering/sorting, not data-array indexes or per-page row numbers.
Repeat `--drill-row` up to three times. All existing output formats and page
selection options apply to the final detail. `--format project` deliberately
saves that final detail request as a separate project; Studio Save project keeps
the root. The standalone .NET CLI exports the supplied root template as before.

## Limits and verification

Three nested detail-template levels; 10,000 interactive rows and 8 MB total
serialized row data per generated report. Filtering reduces the interactive
rows; merely hiding a column does not reduce retained row data. Existing template
JSON depth, page/layout, request (12 MB), imported project (8 MB) and exporter
limits still apply. An oversized detail request fails without changing the
parent. A child template has its own page settings, resources and parameters;
these are not inherited except for matching parameter values.

The local Linux iMac is the verification platform. macOS and Windows remain
unverified. The example contains only synthetic data.
