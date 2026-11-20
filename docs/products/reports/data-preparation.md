# Derived tables and visual data preparation

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


Data → **Prepare data** builds reusable derived arrays without changing source
JSON. Rules are stored as `dataTables` in the report template and travel with
Save template / Save project. They run for every generation and every export,
including API, Python CLI and the standalone .NET CLI. No script opt-in is needed.

## Try it

Download **Prepared sales project** from the built-in manual and Open project.
The source pair is `samples/data-preparation.nrtemplate` and
`samples/data-preparation.data.json`. All records are synthetic.

1. Generate preview. The table and chart show West 120.00 and East 70.00; total
   revenue is 190.00 across three qualifying orders.
2. In Data → Prepare data, select a table to inspect its rules. Choose
   **Preview data**: `sales` has four paid rows, `qualified` has three rows,
   `regional` groups those rows and `ranked` sorts revenue descending.
3. Change parameter `minimum` to 60 outside the dialog, reopen and preview.
   Only West remains, with revenue 120. Preview uses the current root parameter
   values/defaults; it does not open or execute parameter dialogs.
4. Cancel discards all edits. **Apply rules** is enabled only after successful
   preview of the current rules. It changes the template, not source data.
   Generate preview updates report pages. Undo/Redo restores the rules.

The Data tab's ordinary Table/JSON view and dictionary continue to represent raw
source data. Inspect generated arrays in Prepare data → Preview data. Enter a
produced table name, e.g. `ranked`, in a report Table or Chart's Data source.
Output field names are those defined by the rules; they may not appear in raw
source suggestions. Generated rows are not persisted in project data.

## Build a pipeline

**Add table** creates a rule. Set a unique output name and a dotted **Source
array** path into raw data or a table produced by an earlier rule. Output names
must not already exist at the data root. Names are case-sensitive identifiers:
letters/digits/underscore, starting with a letter/underscore, 1–80 characters;
`__proto__`, `prototype` and `constructor` are reserved. Paths use these segments.
Moving a dependent table before its producer fails preview without saving it.
There is no implicit overwrite, forward reference or dependency reordering.

Each rule executes in this fixed order:

1. **Filter source rows**: up to 20 conditions with All/Any. Use `eq`, `ne`, `gt`,
   `gte`, `lt`, `lte`, `contains`, `isNull`, `isNotNull`. Values can be a named
   report parameter or a scalar constant. Numbers and booleans use JSON syntax;
   quote strings to distinguish `"123"` from `123`. Plain non-JSON text is also
   treated as a string. Null tests do not use a value. Comparisons follow the
   existing table-filter rules; text matching is ordinal and case-sensitive.
2. **Sort source rows**: up to five dotted fields with Ascending/Descending.
   Ties retain source order. Non-null values within one sort field must have
   the same scalar type. Null sorts first ascending, last descending.
3. **Output columns and groups**: choose projection or aggregation as below.

With no output columns and no grouping, complete source records are preserved.
With columns, each output identifier copies a **Field** (including nested JSON)
or evaluates a **Numeric expression**, e.g. `row.quantity * row.price` or
`coalesce(row.discount, 0)`. Expressions use the existing bounded decimal table
language and numeric `parameters.name`. Columns evaluate against the source
row independently, not earlier output columns. Use another derived table to
filter/sort/calculate from newly produced fields.

For a summary, set up to three comma-separated **Group fields**, then add output
columns for each desired group field and aggregate columns: Sum, Average, Min,
Max or Count. A nonaggregate output column must copy a group field. Count counts
rows and takes no field/expression. Other aggregates require decimal numbers in
every row; handle null explicitly with a numeric expression such as
`coalesce(row.amount, 0)`. Mixed or nonnumeric values fail with the table name.
Groups follow first occurrence after source sorting. For sorting by totals,
add a subsequent rule whose source is the grouped result.

Group keys are typed scalars: numeric `1`/`1.0` share a group, string `"1"` is
separate; null is a valid key. Nested object/array keys are rejected. A summary
without group fields produces one global row, including on empty input:
Count/Sum = 0, Average/Min/Max = null. A grouped empty input produces no rows.
Average is based on source rows, not group averages. Decimal overflow and division
by zero are errors. Missing fields use the engine's existing binding errors.

## Execution and errors

The order is parameter normalization → derived tables → trusted script events
(including beforeRender) → layout → exporters. Scripts see generated arrays and
can change them afterward. Data preview runs only the preparation rules, never
scripts or layout: it can succeed while a later script/report fails. The report
uses its own final calculated data, including for drill-down snapshots.

Preparation starts from raw input on every render; results are not fed back into
source JSON. A failure does not partially update the source/editor, saved rules,
or previous report. Editing any rule invalidates its preview. Apply checks that
source/template/parameters have not changed since opening the dialog. Preview
shows up to 20 rows and 50 columns per table; nested/long cells are truncated
only in this display. Outputs used by the report retain their complete values.

Limits: 20 derived tables, 10,000 input rows per rule, 100,000 input rows across
all rules, 50 output columns, 3 group keys, 8 MB complete prepared data (raw data
plus all outputs). Filtering does not bypass the input-row limit. Existing
project/request/expression/layout limits also apply. Reduce source data or remove
unused intermediate tables when limits are exceeded. No joins, SQL/HTTP refresh,
visual text formulas, nested filter groups, or dependency graph editor in this
stage; trusted beforeRender remains available for other transformations.

## Template and API

```json
"dataTables": [
  {
    "name": "totals", "source": "items", "groupBy": ["region"],
    "columns": [
      {"name":"region","field":"region"},
      {"name":"revenue","expression":"row.quantity * row.price","aggregate":"sum"},
      {"name":"orders","aggregate":"count"}
    ]
  }
]
```

Optional fields default to empty lists, `filterMatch: "all"`, output name
`prepared`, source `items`. Lists must not be null. `field`, `expression` and
`aggregate` may be omitted/null, subject to the column rules above. Version stays
1 and the versioned schema includes `dataTables`. Static template checking
validates rule definitions; actual source fields, collisions and numeric types
are checked when preparing data.

`POST /api/data/prepare` accepts the same `{template,data,parameters}` body as
preview, returning `{data: {...rawData, ...derivedTables}}`. It does not validate
layout or execute scripts. Errors return HTTP 400 with a detail message.
From .NET, submit the documented request to this endpoint. Normal SDK preview/export requests also run the same preparation automatically in the installed engine.

With Studio running:

```bash
python3 tools/report-tool.py --template samples/data-preparation.nrtemplate \
  --data samples/data-preparation.data.json --format prepared-data \
  --output artifacts/prepared.json
python3 tools/report-tool.py --template samples/data-preparation.nrtemplate \
  --data samples/data-preparation.data.json --format pdf \
  --output artifacts/prepared.pdf
```

`prepared-data` writes the API response envelope and reports `pages: null`; other
formats retain their existing behavior. Its output is a computed snapshot, not
source data for the same pipeline (existing output names would collide).
Verified platform: local Linux on iMac. macOS and Windows remain unverified.
