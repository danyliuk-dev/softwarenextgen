# Template format v1

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


Templates use UTF-8 JSON and the `.nrtemplate` extension; legacy `.json` templates
can also be opened. Unknown properties and block types are rejected. Dimensions
are in points: 72 pt = 1 inch.

```json
{
  "version": 1,
  "title": "Orders",
  "page": {
    "width": 595.28, "height": 841.89, "margin": 42,
    "header": "{{parameters.company}}", "footer": "Page {page} of {pages}"
  },
  "parameters": {"company": {"type": "string", "required": true, "default": "Example"}},
  "images": {},
  "blocks": [
    {"type": "text", "text": "{{data.title}}", "style": {"size": 24, "bold": true}},
    {"type": "table", "source": "orders", "columns": [
      {"title": "Number", "field": "number", "weight": 1},
      {"title": "Amount", "field": "amount", "weight": 1, "format": "N2", "align": "right"}
    ]}
  ]
}
```

## Bindings

- `{{parameters.name}}`: string, number, boolean or string[] parameter.
- `{{data.customer.name}}`: scalar field in the input object.
- Table `source`: array path; column `field`: path relative to each row.
- N0–N6 and F0–F6 format table numbers; dates arrive as strings.
- `{page}` and `{pages}` apply only to page headers/footers.
- Missing fields, missing required parameters and unknown parameters cause errors.

## Blocks

`text` has text, style and spaceAfter. Text wraps and flows onto following pages;
explicit newlines remain, while repeated spaces collapse.

`table` has source, columns, style, padding, headerColor and stripeColor. Column
widths are proportional to weight; headings repeat on new pages. Row height uses
the tallest cell. Long tokens split by Unicode text elements, not UTF-16 units.

`image` has resource, width and height. Resource names a base64 PNG/JPEG entry in
images without a data: prefix. Images retain their aspect ratio and are centered.

`pageBreak` starts a page; initial, repeated and trailing breaks do not create
empty pages. All blocks accept spaceAfter, which has no useful effect on pageBreak.
Style fields are size, bold, color (#RRGGBB) and align (left/center/right).

## Limits

At most 1,000 blocks, 100,000 rows/table, 10,000 pages, 50 columns, one million
characters per text, and 8 MB base64 per image resource. Studio requests are bounded
to 12 MB. A table heading must leave room for a data row. Headers/footers must fit
on one line within the page width.

## Fixed text, image and table frames

Text, image and table blocks may specify frame:

```json
{"type":"text","text":"Heading","frame":{"x":72,"y":40,"width":250,"height":60}}
```

The origin is the top-left content corner of the current page, after margins.
Frames must fit inside that content area. Missing frame and frame:null are equivalent.
A fixed block does not advance the flow cursor; spaceAfter is ignored. Text wraps
inside its frame and fails on height overflow. Images fit while retaining aspect
ratio. All table rows must fit the fixed frame; use Flow for automatic pagination.
See `samples/positioned-table.nrtemplate` and its data file.

Block order determines painting order; overlap is allowed. pageBreak rejects frame.
A preceding flowing table may advance the current page before a fixed block is drawn.
In Design, Positioning → fixed exposes geometry, drag handles and resizing. Dragging
uses a 2 pt grid and stays inside the page; Undo/Redo treats one gesture as one edit.
Check final positions and overlaps in Preview/PDF. See `samples/positioned.nrtemplate`.

Layout → Align to page supports Left/Center/Right and Top/Middle/Bottom. Focus the
handle and use arrows for 1 pt or Shift+arrows for 10 pt movement. Duplicate offsets
by 12 pt, reversing near an edge; a full-width/height block cannot move along that
axis. Every command supports Undo.

## TypeScript logic

Optional logic declares language:"typescript", apiVersion:1 and source (at most
64,000 characters). Source is checked before execution. Supported handlers:
validateParameters, beforeRender, afterRender, dialogLoad, parameterChanged,
dialogButtonClick, dialogPageChanged and dialogPageChanging.
See the [scripting manual](report-logic-manual.md).

## Parameter input dialog

Studio: **Run with parameters** opens a private draft of the input values.
Cancel discards changes; Generate preview runs the same server validation and
TypeScript events as normal generation. Field errors keep the dialog open.
Successful generation copies values back to the workspace.

In **Page → Parameters**, set **Label**, **Help text**, and **Multiline text**.
Template definitions accept optional label (up to 200 characters), help
(up to 2000 characters), and control (see Extended Toolbox fields and components below).
Multiline is only valid for string parameters. Auto uses a text input, number
input or checkbox according to the parameter type. These properties affect
presentation, not the value types or TypeScript API.
A visual dialog layout is available. dialogLoad and parameterChanged handlers can
return parameter patches and a message; see the scripting manual for draft semantics.

Dropdown: a string parameter with control "select" and options ["North", "South"].
Options may contain 0–200 unique, nonblank strings of at most 500 characters,
without line breaks. Matching is exact and case-sensitive.
Only select, list, radio and checkedList controls may have nonempty options. Required dropdowns reject empty
values; optional dropdowns allow the empty string. Defaults and supplied values
are checked against options during binding, before report scripts run.

## Visual parameter dialog

Optional root property dialog contains title, width, height and components.
Dimensions are CSS pixels: width 280–1200, height 120–1200.
Each component has a unique id, kind (see the component kinds below), text,
x, y, width (minimum 80), height (minimum 32).
Fields require parameter referencing an existing parameter; each binding is unique.
Labels must not have a parameter binding. Components must fit inside the form.
Up to 100 components are allowed. The component order determines keyboard order.
The parameter definition determines the actual control and validation.
Only components listed in dialog.components appear in the custom dialog.
Unplaced parameters retain existing/default values but are not automatically shown.
Without a dialog, Studio generates a field for each parameter. Form layout does not
affect CLI/API rendering; the engine validates its structure and bindings.
Small screens stack controls within their containers. Load, Change and Custom Click handlers are supported; see report-logic-manual.md.

### Component anchors

Optional component anchors is a unique array of "left", "top", "right", "bottom";
default ["left","top"], empty is allowed. The Studio designer applies anchors
when changing Form width/height, then saves the resolved integer geometry.
Opposite anchors stretch a dimension; trailing-only anchors move the coordinate
by the size delta; neither anchor moves it by half the delta (rounded).
Invalid resulting bounds/minimum size reject the complete resize.
Runtime displays saved geometry; small-screen stacking remains independent.

## Extended Toolbox fields and components

Parameter type also supports string[]. Control may be auto, multiline, password,
date, time, datetime, color, select, list, radio, checkedList or range.
checkedList requires type string[]; range requires number and finite minimum <
maximum. Other non-auto controls require string. Choice controls allow 0–200
unique options. Minimum/maximum may be supplied only for numeric parameters.

Dialog component kinds also include panel, group, button, link, image, progress,
separator, table and tree. Optional parentId names a panel/group/tabpage; cycles are
rejected. Coordinates remain relative to the form and children must fit their
parent. Optional settings: action (submit/reset/cancel/custom/next/back), href, resource, source,
value (0–100). Only fields bind parameter. Source is a dotted input-data path,
resource is an embedded image key. See [Toolbox](toolbox.md) for runtime limits.

Tab containers use `kind: "tabs"`; their direct children must be `kind: "tabpage"`
with `parentId` referencing the container. At least one page is required.
Pages must fit below the 36 px tab header. Fields bind parameters inside pages
using the same global form coordinates. See [tabbed forms](toolbox.md#tabbed-forms).

Masked string parameters use `control: "masked"` and a required `mask` property,
for example `"mask": "LL-000", "default": "AB-123"`. All values passed through
the API must include mask literals. The bounded mask grammar is documented in
[MaskedTextBox](toolbox.md#maskedtextbox); no arbitrary regex is evaluated.

Custom dialog buttons use `kind: "button", action: "custom"`. Their unique `id`
is passed as `DialogButtonContext.componentId` to `dialogButtonClick`.

Dialog event results may include `components: Record<string, { visible?: boolean; enabled?: boolean }>`.
This is transient runtime state, not a template property. Missing properties preserve
state; containers affect descendants. Unknown/duplicate IDs, non-boolean values,
unsupported properties and individual TabPage updates are rejected atomically.
Closing/resetting clears state. Hidden/disabled parameter values remain subject to
report validation. Tab selection supports dialogPageChanged(ctx: DialogPageContext); componentId identifies the selected TabPage. Use dialogPageChanging for cancellable user navigation.

DialogUpdate.options maps parameter names to string arrays for select/list/radio/checkedList.
Each array replaces that parameter's choices (0–200 unique, nonblank single-line
strings, max 500 characters each). The same patch may include a selected value in
parameters; it must belong to the new choices (empty draft selections are allowed).
Without an explicit value, still-valid selections are retained and removed choices
are cleared. CheckedList retains its intersection in option order.
Options are draft state until Generate succeeds. Studio sends an effective template
with these choices for preview/PDF, retains the committed choices in the sidebar,
and materializes them in saved projects without rewriting the design template.
Saved template-only files retain the original choices and event handlers.
Empty lists still enforce requiredness at generation; optional empty choices work.

Navigation actions `next` and `back` require kind `button` with a TabPage ancestor.
They navigate sibling pages of the nearest enclosing TabControl in template order.
Next validates the current page's browser field constraints; Back does not validate.
Boundary buttons are disabled. Successful navigation emits dialogPageChanged;
Generate still validates all parameters on the server. Direct tab selection remains available.

TabControl supports optional boolean `sequential` (default false). When true,
forward tab headers are disabled; Next validates the current page and advances
one sibling page. Back and earlier headers remain available; returning re-blocks
forward headers. Validation-error reveals may open any page. This is UI navigation
only; Generate and server validation remain independent. True is rejected on
components other than tabs. Each nested TabControl has its own setting.

`POST /api/dialog/event` accepts `event: "dialogPageChanging"` with componentId
(destination) and previousComponentId (source), distinct TabPages in the same
TabControl. The handler returns DialogNavigationResult: optional boolean cancel
and optional message (max 2000 characters); all other response fields are rejected.
Allowed transitions then invoke dialogPageChanged. Initial selection and automatic
validation reveals bypass this event. It does not replace final report validation.

## Table grouping and sums

Optional table `groupBy` is a nonempty row-relative scalar field path. Omit it
(or set null) with empty groupFields for no grouping. Groups preserve first occurrence order after optional sorting, and rows
preserve that order within each group. Strings are case-sensitive; number 1
and 1.0 share a group, string "1" is separate. Null is a valid key; missing keys,
objects and arrays are errors. Up to three distinct grouping paths are supported: groupBy followed by groupFields.

Column `sum: true` (default false) adds decimal aggregates. Every selected value
must be a JSON number representable as decimal; missing/null/string values and
overflow fail generation. Formatting is applied after summation. Table flags
`showGroupTotals` and `showGrandTotal` default to true. Without aggregates
neither creates rows. Empty arrays have zero Sum/Count grand totals and blank Average/Min/Max. Without grouping fields,
only a grand total is available. Non-aggregate total cells remain blank; a full-width
caption precedes the numeric row. Column formats and alignment apply to totals.

Column and active group headings repeat on page breaks; total captions and values
stay together. Fixed tables must fit their frame. Example: `samples/grouped-orders.nrtemplate`
and `samples/grouped-orders.data.json`; expected grand totals 13 and 310.30.

### Column aggregate

Prefer `aggregate: "sum" | "average" | "min" | "max" | "count"`; omit or use null
for none. Legacy `sum: true` remains supported when aggregate is absent/null or
"sum". Combining it with another aggregate is an error; clear legacy sum when
changing aggregate. One aggregate per column; duplicate a column for several.

Sum/average/min/max require decimal numbers in every row. Average divides the
sum of original rows by their count (grand average is not an average of group
averages); decimal sum overflow is an error even when the average might fit.
Min/max do not sum. Count counts rows including null/string values, not distinct
or non-null values; the field must still exist for normal row rendering.
Column number formats apply to both rows and totals, so leave the format unset
for a string field with count. Empty sum/count are 0; empty average/min/max are
blank. All aggregates share subtotal/grand-total switches and pagination rules.

### Table sorting

Optional `sortBy` is one nonempty row-relative dotted field path; omit/null keeps
source order. `sortDirection` is `"asc"` (default) or `"desc"`. Sorting is stable,
occurs before grouping and affects only this table, without mutating input data.
Groups follow first occurrence in the sorted rows; equal sort keys retain source
order in both directions. Set sortBy equal to groupBy to order groups by key.

All non-null keys must have the same type: decimal number, string or boolean.
Numbers compare numerically; strings use case-sensitive ordinal comparison,
independent of locale; false precedes true ascending. Null sorts first ascending
and last descending. Missing keys, mixed non-null types, arrays/objects and
numbers outside decimal range fail. Date strings sort as text. No sorting by
aggregated values; use sorts for additional keys or beforeRender for advanced ordering.
Example: add `"sortBy": "amount", "sortDirection": "asc"` to the table in
samples/grouped-orders.nrtemplate: groups East/South/North, grand total 310.30.

### Table filter

Optional `filter` (omit/null disables) is `{ "field": "amount", "operator": "gte",
"value": 80 }`. Field is row-relative, including dotted paths. Operators: eq
(default), ne, gt, gte, lt, lte, contains, isNull, isNotNull. Non-unary operators
require a string/decimal/boolean value or parameter reference; contains requires string; ordered
comparisons accept text/numbers, not boolean. Unary null operators ignore value.

Filter runs before sorting/grouping/aggregation, on every source row. It changes
only this table, not input data. All totals use surviving rows. No matches behave
like an empty source. Missing filter paths fail, including with isNull. Non-null
field values must match the literal type; no coercion. Numbers compare as decimal;
strings and contains are ordinal/case-sensitive. Empty contains matches all
non-null strings. Null matches ne and isNull, but no ordinary equality/ordered/
contains comparison; isNotNull matches any non-null value. Other operators reject
objects/arrays and out-of-range numeric values. Invalid definitions fail even
for empty sources. Use filters/filterMatch for flat AND/OR combinations; nested conditions require beforeRender. Example: grouped-orders amount gte 80 gives total 205.50, quantity 3.

### Parameter-bound filter values

Use `"filter": {"field":"amount", "operator":"gte", "parameter":"minAmount"}`
instead of a constant value. `parameter` names a declared scalar report parameter,
not a dotted path. A non-null constant `value` and `parameter` cannot coexist.
Null-check operators cannot reference parameters. Definitions reject unknown
names, string[] types and incompatible operators (contains requires string;
ordered comparisons require string/number). At run time the engine resolves
current/default parameter values without mutating the template, then validates
and filters even when the source is empty. Missing optional number/boolean values
are errors; empty string is valid text, not a signal to disable filtering.
Decimal range/type rules remain unchanged. Project files preserve the binding
and supplied run parameters; Preview/PDF use the same resolved values.

Example: samples/parameter-filter.nrtemplate with samples/grouped-orders.data.json.
Default minAmount=80 gives 205.50; supplied 100 gives 125.50; 0 gives 310.30.

### Combining table filters

`filters` is an array of additional TableFilter objects (default empty).
`filterMatch` is `"all"` (default, AND) or `"any"` (OR). The existing optional
`filter` remains supported and participates as the first condition; `filters`
may also be used alone. Maximum 20 conditions total across both properties.
Null lists/elements, unsupported match modes and over-limit combinations fail.
With no conditions both modes include every row. OR never duplicates rows.

Each condition can use its own constant or parameter. Definitions and parameter
values are validated even for empty sources. Every condition is evaluated on
every source row without short-circuiting, so missing fields/type errors are not
hidden by another match. The resulting rows are sorted, grouped and aggregated.
No nested groups or mixed AND/OR trees. Example: samples/combined-filters.nrtemplate
with grouped-orders.data.json gives 125.50 in all mode, 280.00 in any mode.

### Multiple sort fields

`sorts` is an ordered array of `{ "field": "amount", "direction": "asc" }`.
Direction defaults to asc; desc is also supported. The existing optional sortBy /
sortDirection is the highest-priority key, followed by sorts in array order.
The array can be used alone. At most five keys total across both forms; null
lists/elements, empty paths and invalid directions fail, including on empty data.

Each next key refines ties only; complete ties preserve source order. Types are
validated independently per key across all filtered rows, including low-priority
keys that do not affect the final order. Null/ordinal/decimal rules apply to each
key. Filtering precedes sorting, and grouping preserves the resulting order.
No keys means source order; sorting never changes the input JSON. Example:
samples/multi-sort.nrtemplate with grouped-orders.data.json orders customer asc,
then amount asc: East Clip/Cable, North Chair/Monitor, South Lamp/Desk.

### Nested table groups

`groupFields: ["order", "category"]` adds inner levels after optional `groupBy`.
The list alone can define all levels. At most three distinct, nonempty dotted
paths are allowed in total; null lists and repeated fields are errors. Scalar key
rules above apply independently at every level. Equal child keys under different
parents stay separate. Every level preserves first occurrence after filtering and
sorting. Parent aggregates use original rows, including weighted row averages,
never aggregates of child totals. Nested subtotal captions identify their level/key.
All active ancestor headings repeat on page breaks and stay with the first row
fragment. `showGroupTotals` controls every level; `showGrandTotal` is independent.
Example: `samples/nested-groups.nrtemplate` + `samples/nested-groups.data.json`:
North order A 125.00, B 40.00, North 165.00; South A 80.00, B 10.00,
South 90.00; grand total quantity 10, amount 255.00. This is grouping of a flat
array, not master-detail or a nested data source.

## Numeric table column expressions

Optional column `expression` overrides `field`; field may be omitted or empty when
expression is present. Clear/omit expression (or set null) to use the normal field.
Example: `{"title":"Net","expression":"round(row.quantity * row.price * (1 - parameters.discount), 2)","format":"F2","aggregate":"sum"}`.

Decimal-only grammar: literals with a dot (no exponent), `row.path`, declared number
`parameters.name`, unary +/- and binary + - * / %, parentheses, abs(x), min(a,b),
max(a,b), round(x,digits). Standard arithmetic precedence, left associative binary
operators. round requires integer digits 0–6 and uses midpoint away from zero.
References/functions are case-sensitive. Row path parts use ASCII letters/digits/_
and start with a letter or underscore. Limit 512 characters, 128 AST nodes, 32
nested expressions. Comparisons, numeric logic and conditional/null functions are
described below. No JS execution, strings, dates, JSON booleans, arrays, other
calculated columns or aggregate references.
Scripting need not be enabled. Syntax and number-parameter declarations are checked
even for empty arrays. Evaluation applies only to rows surviving filters; absent,
non-number, out-of-decimal-range, divide-by-zero and overflow fail generation.
Null must be handled explicitly using coalesce/isNull or equality with null.

Filters/sorts/groups use source fields; expressions do not create source fields.
Numeric aggregates use expression results at every group level and grand total;
Count still counts rows. Decimal calculations precede display formatting; use round
explicitly for rounding each row before aggregation. No pagination-dependent values.
Example template/data: samples/calculated-columns.nrtemplate and
samples/calculated-columns.data.json. discount default 0.1 gives total 325.17;
override 0.2 gives 289.04. Russian and built-in manuals include authoring steps.

## Master-detail tables

Optional table `masterSource` is a path to a parent array in the current data
context (report root outside repeat sections). When set, `source` resolves a child
array within each parent; otherwise it uses the current context. `masterHeader`
(default "Details", empty hides it) supports `{{master.path}}`, current-context
`{{data.path}}`, report-root `{{root.path}}` and `{{parameters.name}}`. Master references
are available only in this header. Fixed frames with masterSource are rejected.

Each parent is rendered as a separate flow table in original parent order.
Filters/sorts/groups/expressions run independently on its children; every aggregate
resets per parent. Grand total is the parent's total, with no cross-parent total.
Parent headings repeat with column/active group headings after page breaks, and
stay with the first row fragment. SpaceAfter separates parents and follows the
block. Empty children render headers/empty aggregate values; empty masters render
no tables. Limits: 10,000 object parents, 100,000 combined detail rows before
filtering, masterHeader length 10,000. Every parent must have its child array;
missing/null arrays and missing header fields are errors. Nested child paths are
allowed, but recursively nested master-detail blocks and joins are not supported.
Use beforeRender to join independent arrays or prepare shared calculations.

Example: samples/master-detail.nrtemplate + samples/master-detail.data.json.
Expected parent totals: SO-101 281.30, SO-102 80.00, empty SO-103 0.00.

## Chart block

`{"type":"chart","source":"regions","categoryField":"name","valueField":"net","title":"Net sales","height":260,"format":"F2"}`.
The chart uses shared vector rectangle/line/text commands in SVG Preview and PDF.
Defaults: source items, categoryField category, valueField value, empty title,
chartKind bar, orientation horizontal, height 280pt, format F2, barColor #4F6BED, negativeColor #C45555, style size 9.
Format is null or N0–N6/F0–F6; null uses the decimal's general representation.
Title supports data/parameters bindings. Style controls font size/bold/color;
label/number alignment is fixed. Frame is unsupported; spaceAfter applies normally.

Source must be an array of at most 30 rows. Category/value paths are row-relative;
values must be decimal JSON numbers, categories scalar (null → (null)). Missing
fields, nonnumeric values, arrays/objects as categories and invalid settings fail.
Each row is an independent bar in source order, including duplicate categories.
There is no built-in aggregation/filter/sort/formula/master binding. Prepare data
in beforeRender when needed. Empty source displays No data.

Scale includes zero. Signed bars share a zero axis; zero values omit the bar.
Lengths use original values; numeric formatting only affects labels. Chart height
must fit one page's content area; it moves whole to a new page when needed. Labels
wrap within their row; insufficient height/width fails rather than clipping.
Maximum title length 10,000. One legacy series or up to three explicit series, horizontal/vertical bars or categorical lines. Pie/donut composition charts are described below; other chart types are not supported.
Example: samples/bar-chart.nrtemplate + samples/bar-chart.data.json.

### Vertical columns

Set `orientation: "vertical"`; the only other supported value is `horizontal`
(default for existing templates). Values/null/unknown strings outside this enum fail.
Positive bars extend upward from the zero line and negative bars downward. All-zero,
positive-only and negative-only data keep a zero-inclusive scale. Zero bars are omitted.
Formatted values occupy a centered band above the plot; category labels wrap in
equal-width slots below it. Duplicate categories remain independent and source order
is preserved. No axes with date/numeric spacing, extra tick marks or aggregation.

The plot reserves a left gutter for zero, 8pt between value/category labels and the
plot, and at least 40pt plot height. Each category slot must be at least 16pt wide,
and formatted values must fit on one line with 4pt side padding. Too many categories,
long labels or wide values fail with an actionable error; widen the page, increase
height, reduce font/precision or shorten/reduce categories as appropriate. A chart
stays on one page. Colors, title bindings, formatting, empty-data behavior and all
other chart constraints apply unchanged. Example: samples/column-chart.nrtemplate
with samples/bar-chart.data.json.

### Categorical line chart

Set `chartKind: "line"`; `bar` is the default. Unknown/null kinds are rejected.
Line charts always use categories left-to-right and values vertically, regardless
of the stored valid orientation (retained for switching back to bars). Category
spacing is equal; this is not an XY/time-scale chart. Points connect in source
order, with straight 1.5pt segments in barColor. Every point has a 4pt square marker;
negative markers use negativeColor, nonnegative markers use barColor. Zero points
are included. One record has one marker and no segment; empty data shows No data.

The scale includes zero. Markers are inset 2pt from the plot edges to stay inside.
Values appear above the plot and categories below, using the same width/height
checks as vertical bars. Missing/null/non-numeric values fail rather than creating
gaps. There is no smoothing, date spacing, sorting, aggregation or area fill. Multiple series use the series list below. Format affects labels only. The chart moves whole to a new page.
Example: samples/line-chart.nrtemplate + samples/bar-chart.data.json.

Preview documents now include `type: "line"` commands with x1/y1/x2/y2 (points),
color (#RRGGBB) and strokeWidth (points), in addition to text/rect/image commands.
External Preview consumers must support this command to display line-chart segments.

### Multiple chart series

Optional `series` is an array of up to three objects, each with `title` (default
Value), `valueField` (value), `format` (F2 or null for general decimal format), and
`color` (#4F6BED). Titles must be distinct nonempty strings up to 100 characters
(case-sensitive); fields are dotted paths relative to each source record. Formats
are N0–N6/F0–F6 or null, colors #RRGGBB. Null arrays/items are rejected.
Missing/empty series preserves the legacy single-value layout. A nonempty list
replaces valueField/format/barColor/negativeColor, which the renderer ignores in
that mode. The schema still validates any explicitly supplied legacy properties.

All series share source/categoryField and a zero-inclusive scale. Grouped bars
are side by side by default (or arranged vertically within each horizontal category).
barMode enables value stacking or percentage normalization as described below. Lines connect each series independently in source order.
Each series retains its color for positive/negative/zero markers and value labels.
NegativeColor applies only in legacy mode. Use distinct colors for readability.
One legend entry per series appears above the chart, including when there is no
data. Titles wrap; legend height is included in the block height. Even a list of
one series shows its legend. The whole chart moves to a new page when required.

Vertical/line values occupy one line per series above the plot, in legend order;
categories are below. Horizontal values align to the individual bars. Missing,
null or nonnumeric values fail; there are no gaps. Width/height errors are explicit,
without clipping or shrinking. Maximum 30 source records still applies; multiple
series/legend may require more height or fewer categories. No dual axes, mixed
chart types, interpolation, sorting or automatic aggregation.

Designer Add series preserves the legacy value/format/color as the first series
and adds a second. Move/remove controls manage order; at least one explicit series
remains. Use single series transfers the remaining field/format/color to legacy
properties and removes the legend (the saved NegativeColor becomes active again).
Undo/Redo and project export preserve series. Example: samples/chart-series.nrtemplate
+ samples/chart-series.data.json: grouped bars, columns and lines across three pages.

### Stacked and percentage bars

`barMode` is `grouped` (default), `stacked` or `percent`. Unknown/null modes fail.
It is active only for bar charts with a nonempty series list. Lines and legacy
single-value charts ignore the saved valid mode; returning to bars restores it.
Designer disables Bar mode for lines/legacy charts. Use single series resets mode
to grouped when converting back to legacy fields.

In stacked mode, each category has one bar composed of series segments. Positive
values accumulate from zero right/up, negative values separately left/down, in
series order. The global scale uses the largest positive and negative category
sums, not the largest individual value. Series colors/legend remain unchanged.
Zero values have labels but no segments. Labels show original formatted values,
outside the segments (in legend order at right or above the plot).

In percent mode, positive values in each category divide by that category's positive
sum, negative values by the magnitude of its negative sum. Each nonempty side thus
reaches +100% or -100% independently; mixed-sign categories can span -100% to +100%.
This is not a share of the signed/net total. An all-zero category shows 0% labels
without segments. Labels show normalized percentages using each series' Number
format plus `%` (F1 recommended); they do not show the original amounts. Rounding
may make displayed shares total 99.9% or 100.1%, but geometry uses unrounded values.
No source values are modified. Calculations use finite double geometry, including
sums larger than decimal.MaxValue; individual inputs must still be decimal numbers.

Both orientations, up to three series, legend/order/colors, Flow pagination,
empty data and existing width/height checks apply. Percentages can require wider
label space. No mixed bar/line stacking or totals printed inside segments.
Example: samples/stacked-charts.nrtemplate + samples/stacked-charts.data.json:
four pages for stacked/percent × horizontal/vertical. North 120/60/60 becomes
50%/25%/25%; South 60/-30/-10 becomes 100%/-75%/-25%; East stays all zero.

## Code 39 barcode block

`{"type":"barcode","value":"{{data.orderCode}}","moduleWidth":1,"height":70,"showText":true,"fontSize":10}`.
Defaults: symbology code39, value CODE39, moduleWidth 1pt, height 60pt, showText true, fontSize 9pt.
Value supports data/parameters bindings, maximum binding text length 10,000; the
resolved payload must contain 1–80 standard Code 39 characters: A–Z, 0–9, space,
`- . $ / + %`. No trimming, uppercasing, checksum or Extended ASCII. Start/stop *
are automatic; * in the payload is invalid. Preserve leading zeros using strings.

Module width is 1–4pt; wide:narrow ratio is 3:1 and the inter-character gap is one
module. Each side's white quiet zone is max(18pt, 10 modules). Natural total width
is `(16 * (payloadLength + 2) - 1) * moduleWidth + 2 * quietZone`. It must fit the
page content width; there is no automatic compression. Height includes caption
and a 4pt gap when showText is true. Bar height must be at least 20pt, font size
must be positive and at most 36pt, and the unwrapped caption must fit the symbol.
Bars are black on an explicit white background, using shared vector commands.

Only Flow; no frame or table-cell placement. QR/Data Matrix are described below. Code 39 has no checksum. The block
moves whole to the next page and honors spaceAfter. Invalid values, bindings,
height/width and text overflow produce ReportException. Sample: samples/code39.nrtemplate
and samples/code39.data.json, decoded payload SO-2026-001. Optional independent
verification uses independent barcode decoding.
See THIRD-PARTY-NOTICES.md for the pattern-table attribution and license.

### Code 128 B

Set `symbology: "code128b"` on a barcode block. The default is `code39`;
unknown/null symbologies are rejected. The resolved payload is 1–80 printable
ASCII characters U+0020–U+007E, including lowercase, spaces, underscore and *.
No trimming or case conversion occurs. Unicode, DEL, controls and FNC escape
characters are rejected. This is Code Set B only: no A/C switching, numeric
compression, GS1/FNC1 or application identifiers.

Start B, the mandatory modulo-103 weighted checksum and stop are automatic;
the caption contains only the original payload. Symbol width is
`(11 * (payloadLength + 2) + 13) * moduleWidth`, plus the same quiet zones as Code 39.
Bars/spaces are 1–4 modules wide. All common height, caption, Flow pagination,
binding, module-width and page-fit checks apply. No automatic shrinking occurs.
Example: samples/code128b.nrtemplate + samples/code128b.data.json, decoded payload
so_2026-001. PDF output has independent decoding checks.py); checks all printable ASCII, checksum, spaces and 80 characters.

### EAN-13, EAN-8 and UPC-A

Use `symbology: "ean13"`, `"ean8"` or `"upca"`. Only ASCII digits are accepted:

| Symbology | Input without check digit | Complete input/caption |
|---|---|---|
| ean13 | 12 digits | 13 digits |
| ean8 | 7 digits | 8 digits |
| upca | 11 digits | 12 digits |

Short input receives a modulo-10 check digit (weights 3/1 from the right).
Complete input must have the correct check digit; it is never silently repaired.
No trimming, padding or numeric coercion. Data/parameter bindings are expanded first;
store codes as strings to preserve leading zeros. Caption and encoded bars include
the calculated digit, while the template/data remain unchanged.

EAN-13 and UPC-A occupy 95 modules, EAN-8 occupies 67. Each white quiet zone is
max(18pt, 11 modules). Common 1–4pt module, caption/font, height, Flow/page-fit rules
apply. Black vector bars have equal heights, with a centered caption below the
whole symbol; this is not a retail packaging layout with extended guard bars and
positioned digit groups. No UPC-E, EAN supplements, GS1-128 or GTIN allocation checks.
The application encodes digits, not product-registration status. Actual printer/
scanner and packaging compliance have not been verified.

Example: samples/retail-barcodes.nrtemplate + samples/retail-barcodes.data.json.
Expected values: 5901234123457, 96385074 and 036000291452. Some readers report
UPC-A as equivalent EAN-13 with a leading zero (0036000291452); the report caption
remains the 12-digit UPC-A value. Independent PDF decoding:
independent retail-barcode decoding checks (Pillow, zxing-cpp and pdftoppm), including all ten
EAN-13 first-digit parities, leading zeros, full/short inputs and hidden captions.

## Cross-tab block

`{"type":"crossTab","source":"items","rowField":"region","columnField":"quarter","valueField":"amount","aggregate":"sum","format":"F2","showRowTotals":true,"showColumnTotals":true}`.
These values are defaults. Style defaults to 9pt, with standard text style properties.
Source is an array in the current data context (report root outside repeat
sections); fields are dotted paths relative to each record.
Both categories must be nonempty strings (maximum 200 characters), exact comparison,
first-seen axis order. Maximum 100,000 records, 1,000 row and 20 column categories.
Values must be decimal JSON numbers; Count ignores valueField values but still
requires a valid field path in the template. Aggregates: sum/average/min/max/count.
Missing intersections are zero for sum/count, blank otherwise. Totals aggregate
raw records, including Average. Display format is null or F0–F6/N0–N6.

Only Flow, with repeated headers and existing table text wrapping/pagination.
Each numeric column needs at least 40pt; row labels take two shares of width.
No horizontal pagination or built-in filters.
Empty input retains headers and enabled totals. Row totals add a right Total column;
column totals add a bottom Grand total row with ordinary row styling. Both default
true and can be disabled independently. spaceAfter applies once to the whole block.
Example: samples/cross-tab.nrtemplate + samples/cross-tab.data.json.

### Multiple cross-tab measures

Optional `measures` defaults to `[]`. Empty uses legacy block valueField/aggregate/format
unchanged. A nonempty array (1–3 entries) takes precedence; those three legacy
properties are then ignored by the engine, including runtime validation. The schema
still validates any supplied legacy properties; omit unused ones in new templates.
Null arrays/items fail.
Each measure has title (default Value, nonempty, maximum 100 characters, distinct
ordinal case-sensitive titles), valueField (default amount), aggregate (default sum)
and format (default F2). Field/aggregate/format follow the same single-measure rules.

Example: `"measures":[{"title":"Sales","valueField":"amount","aggregate":"sum","format":"F2"},{"title":"Orders","valueField":"amount","aggregate":"count","format":"F0"}]`.
Within each category, columns follow measure order; headings contain the category
and measure title on separate lines. Row totals have one column per measure;
column and grand totals aggregate original records independently (never cell averages).
Maximum 50 rendered columns: `labelColumnCount + (categoryCount + subtotalColumnGroups + (showRowTotals ? 1 : 0)) * measureCount`.
The existing width rule still applies. Explicit one-measure arrays retain titles;
empty arrays preserve legacy headings. Sample: samples/cross-tab-measures.nrtemplate
with samples/cross-tab.data.json, landscape page, Sales/Orders/Average.

### Nested cross-tab axes

Optional `rowFields` and `columnFields` contain up to three distinct dotted field
paths, outermost first. Each defaults to `[]`, which uses rowField/columnField.
A nonempty list replaces its legacy field (ignored by engine validation; omit unused
legacy properties in new templates). Null lists/items, blank paths, duplicates and
more than three levels are rejected. Category rules apply to every level.

Example: `"rowFields":["region","city"],"columnFields":["year","quarter"]`.
Children retain first-seen order within each parent. Interleaved records are grouped
by parent; equal child names under different parents remain independent. Limits of
1,000 row categories and 20 column categories count complete leaf paths. Existing
measure, width, record and rendered-column limits remain unchanged.

Each leaf prints its complete path on separate lines, outermost first. Parent labels
repeat by default. Column headings can be merged with mergeColumnHeaders (see below).
Optional intermediate subtotals are described below;
there are no collapse/drill-down controls. Totals still aggregate source records across leaf
paths; Average is never an average of displayed values. Repeated page headers include
all column levels and measure titles. Empty data keeps headers and enabled totals.
Sample: samples/cross-tab-hierarchy.nrtemplate + samples/cross-tab-hierarchy.data.json.

### Cross-tab group subtotals

`showRowSubtotals` and `showColumnSubtotals` are independent booleans, default false.
The row switch adds a subtotal row after every non-leaf row group; the column switch
adds one subtotal column per measure after every non-leaf column group. Three-level
axes subtotal the inner group first, then its parent. Labels show the parent path
followed by `Subtotal`. Single-level axes and empty input add no subtotals.

Subtotals aggregate original records once at each ancestor intersection, including
intersections of row and column subtotals. Sum/Average/Min/Max/Count and per-measure
formats retain their normal semantics; grand totals never include subtotal values.
The switches do not depend on showRowTotals/showColumnTotals. Old templates retain
their layout. Subtotal rows use ordinary matrix-row styling and pagination;
subtotal column headings repeat with the other headers on every page.

The 1,000-row/20-column limits still count leaf paths. Subtotal rows are additional
(up to 2,000 for three levels). Subtotal columns count toward the 50 rendered-column
limit and the minimum 40pt numeric-column width. Disable column subtotals, reduce
categories/measures or widen the page when the matrix does not fit. All non-leaf
groups are subtotaled together; per-level selection is not supported.
Example: samples/cross-tab-subtotals.nrtemplate + samples/cross-tab-hierarchy.data.json.
North subtotal Sales 90.00 / Average 30.00; grand total 110.00 / 27.50.

### Merged cross-tab column headers

`mergeColumnHeaders` is a boolean, default false. When true, each column-axis level
has its own header band. A parent's cell spans all contiguous child columns and
measures under that exact parent path, including its enabled subtotal columns.
Equal names under different parents are never merged together. Explicit measures
get a separate bottom band. Legacy single-measure mode has no measure-title band.

The row-field corner spans all header bands; Total spans the category bands, with
measure headings below it. Subtotal spans the remaining category bands below its
parent. Text is centered in numeric header cells, wrapped within the combined width,
and header heights grow to fit it. The complete header repeats on each page.
Generation rejects a header that cannot fit with one data line on a page.

This changes only column-header presentation: row-axis labels repeat full
paths unless mergeRowLabels is enabled; data/aggregates/order/limits are unchanged, and no horizontal pagination is
added. Empty input keeps the corner and enabled Total/measure headings. Merged
headers may be taller than ordinary headings, so page counts can change.
Example: samples/cross-tab-merged-headers.nrtemplate + samples/cross-tab-hierarchy.data.json.

### Merged cross-tab row labels

`mergeRowLabels` is a boolean, default false, independent of mergeColumnHeaders.
When true, each row-axis level becomes a separate label column (weight 2 each).
The rendered-column limit includes all these label columns: labelColumnCount is
row-axis depth when enabled, otherwise 1. Numeric columns still need at least 40pt;
extra label columns can require a wider page even with unchanged data.

Adjacent labels merge vertically only for the same complete category prefix and
within one page. The parent label repeats at the top of its continued group on
each new page. Parent cells include their own subtotal row; Subtotal spans the
remaining label columns, and Grand total spans all label columns. Label cells use
a white background, left/top-aligned text and borders; numeric stripes remain.

Each source matrix row must fit below the repeated header when row merging is on.
Rows are kept whole; overly tall labels produce a clear error. Increase page height,
reduce font size or disable Merge row labels to return to ordinary split-row behavior.
No rows or label text are silently truncated. Counts, order and aggregates are unchanged.
Empty input keeps separate field headings and enabled totals. Undo/Redo and project
serialization preserve the switch. Example: samples/cross-tab-merged-rows.nrtemplate
with samples/cross-tab-hierarchy.data.json.

### Nested table filter groups

A table may specify `filterGroup` instead of `filter`/`filters`:

```json
"filterGroup": {
  "match": "all",
  "filters": [{"field":"amount","operator":"gte","parameter":"minAmount"}],
  "groups": [{"match":"any","filters":[
    {"field":"customer","operator":"eq","value":"North"},
    {"field":"customer","operator":"eq","value":"South"}
  ]}]
}
```

Each group's `match` is all (AND, default) or any (OR), combining its direct
conditions and child groups. This example means amount >= minAmount AND
(customer = North OR customer = South). All ordinary filter operators, typed
constants, dotted paths and string/number/boolean parameters are available.
`filterMatch` only governs legacy filters and is ignored for a group tree.

Limits per table: 3 levels including the root, 10 groups including the root,
20 conditions across the tree. Every group must contain at least one condition
or subgroup. Null lists/elements, unknown modes and mixing a tree with nonempty
legacy filters are errors. JSON schema describes structure; the engine also
checks total counts and depth. Every condition is validated/evaluated even when
another branch determines the result, so invalid data types are never hidden by
short-circuiting. Missing paths retain ordinary filter error behavior.

Filtering precedes sorting, grouping, numeric expressions and totals. Flow,
Fixed and master-detail tables use the same logic; for master-detail, fields
refer to the current child row and filtering runs separately per parent.
Source JSON is unchanged. `filterGroup: null` retains legacy behavior.

### Conditional calculations and cell styles

Numeric expressions additionally accept `== != > >= < <=`, `&& || !`, `null`,
`if(test,yes,no)`, `coalesce(value,fallback)` and `isNull(value)`.
Precedence, highest first: unary + - !, * / %, + -, one comparison, &&, ||.
Comparisons and logical operators return decimal 0/1. Tests treat zero as false
and any nonzero decimal as true; JSON boolean/string values are not coerced.
Chained comparisons are invalid; use `a < b && b < c` or parentheses.

`if` evaluates only its chosen branch; &&/|| short-circuit; coalesce evaluates
its fallback only when the first result is null. All branches are parsed and
parameter declarations validated even for empty input. Missing row paths still
fail when accessed: coalesce only handles JSON null, not missing fields, invalid
types, divide-by-zero or overflow. Equality/inequality permit null; ordering,
arithmetic and logical tests require numbers. `isNull` returns 1 for null, else 0.
The final expression result must be a non-null decimal. Existing limits apply.

Optional column `styleRules` is an ordered array, at most 10 rules per column and
100 per table. Each rule has a numeric `when` expression (default "1") and at least
one of `color`/`background` in #RRGGBB. Null/omitted colors inherit the table style.
The first rule whose expression returns nonzero wins as a whole; rules do not
cascade. All syntax/colors are validated, but later conditions are not evaluated
once a rule matches. Errors identify the column and rule number.

```json
{"title":"Net", "expression":"if(row.quantity == 0, 0, row.amount / row.quantity)",
 "styleRules":[{"when":"row.amount < 0", "color":"#842029", "background":"#F8D7DA"}]}
```

Rules apply to data cells, including every page fragment of a split row, but not
headers, group headings, totals, cross-tabs or charts. Unmatched cells use normal
text/stripe colors. Colors do not affect layout metrics or totals. Flow, Fixed
and master-detail tables share the rules; master-detail references each child
row. Conditions reference source numeric fields/number parameters, not computed
columns. Formula/filter/style evaluation does not mutate the source data.

## Repeated report sections

`{"type":"repeat","source":"orders","pageBreakBetween":true,"spaceAfter":12,"blocks":[...]}`
repeats its child blocks for each object in an array. Sources are dotted paths
relative to the current data context (the report root outside a section).
Only object records are accepted; missing/non-array sources and scalar/null
records fail. Empty arrays emit no section content or spacing.

Inside a record, text/chart-title/barcode bindings use `{{data.path}}` for that
record, `{{root.path}}` for report data after beforeRender, and `{{parent.path}}`
for the enclosing record (the root for a top-level section). Parameters/resources
remain global. A child table/chart/cross-tab source resolves inside the current
record. Table row formulas/filters retain their ordinary child-row semantics;
master-detail headers additionally support `{{master.path}}`. Parent bindings
outside a repeat are errors. Global page headers/footers always bind root data,
with global page numbering. Context is restored after a section; later sibling
blocks cannot accidentally use the last repeated record.

Children may contain text, embedded images, tables (including master-detail,
formulas and conditional styles), charts, cross-tabs, barcodes, page breaks and
nested repeat sections. All children must use Flow; Fixed frames inside any
section are rejected even for empty data. Three repeat levels are supported.
The engine limits the template to 1,000 blocks including descendants, the report
to 10,000 repeated records across all sections and 100,000 rendered block
instances, plus its existing 10,000-page limit. Cancellation applies during
iteration. Child definitions are validated even when no records exist.

`pageBreakBetween` starts subsequent records on a new page, but does not force a
break before the first record or after the last. An explicit child Page break
can start every record on a new page. Normal Flow pagination and table header
repetition remain active. Section text headings are not repeated automatically
when their following tables continue. There is no keep-together or per-section
page numbering/header/footer. `spaceAfter` applies after each record, not once
per section; an empty section adds none.

This is inline repetition, not a link to another template/file/server. Sections
share page settings, fonts, parameters and embedded resources. Scripts run once
for the entire report, not once per section. Source data is not modified.
Example: samples/repeated-sections.nrtemplate and repeated-sections.data.json.

## Text and calendar expressions

Inline bindings accept `{{= expression }}` in Text (Flow/Fixed), page headers and
footers, chart titles, barcode values and master-detail headings. Example:
`Due {{= formatDate(addDays(data.ordered, 7), 'dd MMM yyyy') }}`. Existing dotted
bindings keep working. Substituted values are literal: braces in data/results
are not evaluated as another binding.

A table column can use `"textExpression":"upper(row.name)"` instead of `field`.
It produces display text, supports Flow/Fixed/master-detail/repeated sections and
may use Count. It cannot combine `expression`, `format`, Sum/Average/Min/Max or
legacy `sum:true`; use formatNumber inside the text expression. Numeric columns
retain the existing decimal `expression` language and aggregate behavior.
Text results do not become new source fields: sort/group/filter/style rules still
reference original row fields. The engine never changes source JSON.

References: `data.path`, `root.path`, `parent.path` inside a repeat, `master.path`
in a master-detail heading, `row.path` only in a table textExpression, and declared
scalar `parameters.name`. In tables data is the enclosing report/repeat context,
row is the current child row; master is not available in cell expressions.
Missing paths are errors. JSON null is a value; arrays/objects are rejected.
Parameters may be string, number or boolean, not string[]. Global page expressions
use root data and have no row/parent/master context.

Literals are single-quoted strings (escapes: `\'`, `\\`, `\n`, `\r`, `\t`), decimal
numbers without exponent, true, false and null. Expressions are nested function
calls/references/literals; no operators, script evaluation or current-time function.

| Function | Behavior |
|---|---|
| concat(a, ...) | 1–16 scalar arguments, invariant number/boolean conversion; null becomes empty |
| upper(s), lower(s), trim(s) | Invariant case conversion / whitespace trimming |
| replace(s, old, replacement) | Case-sensitive ordinal replacement; old must not be empty |
| substring(s, start, length), length(s) | Zero-based UTF-16 indices/length; invalid ranges fail |
| coalesce(a, fallback) | Fallback only for null, not empty text or a missing path; lazy |
| eq(a, b), if(condition, yes, no) | Exact scalar equality (no coercion); boolean condition; only selected branch runs |
| formatNumber(number, format) | Invariant N0–N6 / F0–F6 |
| formatDate(date, format) | ISO calendar date to an allowed display format |
| addDays(date, days) | Whole calendar-day offset, returns ISO yyyy-MM-dd |
| daysBetween(start, end) | Signed end minus start calendar days; no time-of-day rounding |

Dates must be real `yyyy-MM-dd` strings, years 0001–9999. Times, timestamps, timezone
offsets and locale-specific input are rejected. Allowed output formats:
`yyyy-MM-dd`, `dd/MM/yyyy`, `MM/dd/yyyy`, `dd.MM.yyyy`, `dd MMM yyyy`, `MMMM d, yyyy`,
`yyyy-MM`. Month names are invariant English. Date arithmetic handles leap years
and rejects values outside the date range. Integer arguments are bounded to
±1,000,000; there is no month/year arithmetic or localization setting.

Limits: 512 characters, 128 nodes, 16 levels and 16 function arguments per
expression; each string input/intermediate/result is at most 16,000 UTF-16 units.
Definitions are syntax/context-checked even for empty tables/repeats; argument
values are checked when evaluated. Errors identify table columns. Empty result
text is allowed. Examples: samples/text-dates.nrtemplate and matching data JSON.

## QR Code and Data Matrix

Barcode `symbology` also accepts `qr` and `dataMatrix`. Both encode the resolved
`value` as UTF-8, including text-expression and repeat/parameter bindings. Values
must contain non-whitespace text, at most 512 UTF-8 bytes; leading/trailing spaces
are preserved. Invalid Unicode and control characters other than CR/LF/tab fail.
The byte limit applies after binding, not to the source expression's length.

`moduleWidth` remains 1–4pt and scales every square module uniformly. Symbol
version/dimensions are selected automatically for the payload. QR includes four
white modules per side; square Data Matrix ECC200 includes one. Black modules
are vector rectangles, coalesced into horizontal runs; Preview/PDF/HTML use the
same layout without an external image service or native imaging dependency.

Optional `qrErrorCorrection` is L/M/Q/H, default M; it is ignored by other
symbologies but must always contain a valid enum value. A higher QR correction
level can increase symbol size for the same payload. Data Matrix uses ECC200;
there is no configurable correction level, rectangular shape or DMRE mode.

For matrix symbols `height` is retained for switching back to 1D but does not
control layout (it must still be positive). Actual square size = encoded matrix
width including quiet zones × moduleWidth. With `showText:true` the payload wraps
under the whole square, after a 4pt gap; fontSize retains its usual limit of 36pt.
Caption drawing never intrudes into quiet zones. Hide text for long payloads or
characters unsupported by the report font. The caption is not the encoded value:
wrapping does not add whitespace or alter encoded bytes.

The entire symbol plus optional caption must fit the page content area and moves
as one block when remaining page space is insufficient. A too-wide/tall symbol
fails instead of shrinking modules or clipping. Flow only, including repeats;
Fixed frames and table-cell barcodes remain unsupported. No logos, color/inversion,
structured append, GS1/FNC1, application-identifier parsing, or automatic URL/Wi-Fi
payload construction. Payload text is encoded exactly; URLs are not opened.

Example: samples/matrix-barcodes.nrtemplate with matrix-barcodes.data.json produces
two shipping labels with independent tracking QR and internal Data Matrix codes.

## Pie and donut composition charts

Use `chartKind: "pie"` or `"donut"` on a Chart block. Source/category/value bindings
are unchanged. These types accept one legacy measure (`valueField`/`format`) or
one explicit series; more than one series is rejected. Orientation and barMode
are retained but ignored. For multiple measures use separate circular charts.

The source must be an array of at most 12 rows, with scalar categories and
nonnegative decimal numeric values. Source order is preserved; duplicate categories
are separate slices, not grouped. Null categories display `(null)`. Zero values
remain in the legend but emit no slice; all-zero data displays `No positive values`,
empty data `No data`. Negative/null/nonnumeric values fail. The decimal total must
not overflow. No sorting, filtering or aggregation is implicit: prepare summaries
before rendering (data or beforeRender).

`sliceColors` is a list of 1–12 #RRGGBB colors; the default is
["#4F6BED","#008844","#B45309","#863BB0","#C45555","#008C99"]. Colors are assigned
by original row index and reused cyclically, including zero rows. barColor,
negativeColor and a series color do not override this palette.
`showPercentages` defaults true. The legend always includes category, formatted
value and total; optional percentages use one invariant decimal place. Rounding
can make displayed percentages sum slightly above/below 100%; sector geometry
uses unrounded proportions. `donutHole` defaults .55 and must be .2–.8, a ratio
of inner radius to outer radius; ignored for other chart types. New option values
are validated even when another type is selected or data is empty.

Sectors start at 12 o'clock and proceed clockwise. The chart sits left, a wrapping
legend right. Height includes the title, plot and legend; increase height/reduce
font or shorten categories if the legend does not fit. At least 80pt is required
for both circle diameter and legend width. No outside/inside-slice labels are
placed, so small slices do not cause overlapping captions. Flow only, including
repeat contexts; the whole chart moves together to the next page. Fixed charts
and automatic multi-page legends are not supported.

The shared document protocol adds `type: "polygon"`, `points: [{x,y},...]` in page
points and `fill: "#RRGGBB"`. Clients must close and fill these polygons using the
even-odd rule; reverse inner boundaries preserve donut holes. Circular boundaries
use chords of at most two degrees, giving identical vector geometry in SVG
Preview, PDF and standalone HTML. No external chart library or raster image is
required. Example: samples/circular-charts.nrtemplate and matching data JSON.

## Table row drill-down

Optional `drillDown: {"label":"Open details","template":{...v1 template...}}`
embeds a detail template in an ordinary Table. Omitted/null disables it. Label is
plain text, 1–120 characters; default Open details. Up to three nested detail
levels are statically validated, including empty source tables. Detail templates
have their own page/images/parameters/logic/dialog/blocks definitions.

The Viewer opens the selected original row with `{row: record, source: parentData}`
as data. ParentData is the snapshot after beforeRender, not a repeat/master
record. Matching normalized parent parameters are inherited; other detail
parameters use defaults/required validation. Row values are not automatically
converted into parameters. Child scripts obey the same host opt-in; parameter
dialogs do not run automatically. Back restores cached pages and view settings.

Flow/Fixed, groups, sorting/filtering, master-detail and repeat tables are
supported. Headers/totals are not links; split-row fragments select one record.
Display expressions do not become row data. Cross-tabs/charts have no actions.
The optional ReportDocument.drillDown metadata carries source/parameters,
deduplicated targets, rows and page-point regions. Draw commands are unchanged;
static exporters ignore interaction metadata. Limits: 10,000 interactive rows,
8 MB serialized row data per report, existing JSON/request/page limits.

See [drill-down.md](drill-down.md) for protocol, authoring steps, CLI and limitations.
Example: samples/drill-down.nrtemplate with samples/drill-down.data.json.

## Derived tables

Optional top-level `dataTables` contains up to 20 ordered definitions with
`name`, `source`, `filters`, `filterMatch`, `sorts`, `groupBy` and `columns`.
Each output column has `name`, exactly one `field`/numeric `expression`, and
optional `aggregate` (sum/average/min/max/count); count has neither source.
Filters and sorts use existing Table contracts. Grouped nonaggregate columns
must copy a group field. Output names cannot replace existing root fields.

Rules execute after parameter normalization, before scripts/layout, independently
on each render. Raw data is preserved; derived outputs can feed later rules and
report blocks. Empty global summaries emit count/sum 0 and average/min/max null;
empty grouped summaries emit no rows. Limits and full semantics, including typed
keys and source ordering, are in [data-preparation.md](data-preparation.md).
Sample: `samples/data-preparation.nrtemplate` and matching `.data.json`.

## Portable data connections

Optional `connections` contains up to eight `{source,target,path,parameters,query,refreshOnRender}`
definitions. Source is a host catalog ID; target is a distinct root array name;
path selects a response array for HTTP/JSON/objects (empty means root and is required for SQL); parameters maps allowed
source keys to declared scalar report parameter names. Optional query (up to 16,000
characters) overrides SQL only for host sources with allowQueryEditing enabled.
File paths, URLs and credentials never belong in templates. refreshOnRender defaults
to false and opts an HTTP connection into refresh before server generation.

The direct engine remains offline. Studio server generation refreshes opted-in HTTP
connections before preparation/scripts; useSnapshot:true bypasses fetching. Studio
exports reuse the displayed snapshot. Explicit refresh returns a candidate snapshot.
See [http-connections.md](http-connections.md) for defaults, typed values, limits,
atomic Apply/Undo, host setup and API/CLI. Sample: `http-connections.nrtemplate`
with `http-connections.data.json`.

## SQL, JSON and object sources

See [data-sources.md](data-sources.md) for all five SQL providers, JSON files,
.NET object callbacks and direct POCO/JSON inputs. Connections keep only host IDs,
target arrays, paths and report-parameter bindings, plus optional SQL overrides for
explicitly editable host sources. Credentials and file paths remain on the host. SQL uses an empty path; JSON/objects may
select a nested array. Refresh previews a candidate; Apply saves the snapshot.
HTTP refresh before generation is an explicit per-connection option. Validate the template against its
actual saved data, including when the source is unavailable. The manual includes
an offline example with total 10.00 and configured refresh to 290.00.

## Page sections and imported subreports

A `section` block starts on a fresh page, renders its `blocks` with its own `page`
settings, then resumes the enclosing page settings on a fresh page. Settings use
the same defaults and validation as the report page. Data, parameters, images and
imported subreport names are shared with the enclosing report. Fixed blocks fit
the section's content area. A section cannot be inside a repeat; put a repeat
inside a section instead. Empty sections are rejected.

```json
{"type":"section","page":{"width":841.89,"height":595.28,"margin":36,
 "header":"Overview","footer":"Page {page} / {pages}"},
 "blocks":[{"type":"text","text":"Landscape overview"}]}
```

`subreports` is a dictionary of imported v1 templates, keyed by identifiers
(`[A-Za-z_][A-Za-z0-9_]{0,79}`, at most 20 per template). A `subreport` block names
one with `reference`. `source` is a dotted path resolving to a data object; empty
or omitted means the current object (including a repeat record).

```json
{"version":1,"subreports":{"summary":{"version":1,
 "blocks":[{"type":"text","text":"{{data.customer}}"}]}},
 "blocks":[{"type":"subreport","reference":"summary","source":"order"}]}
```

Each imported report owns its page settings, images, data preparation and parameter
schema. Same-named parent parameter values are inherited; child defaults apply to
other parameters. The child validates inherited values against its own schema.
Its `data` and `root` refer to its prepared object; parent scope is restored after
it finishes. Child drill-down keeps the child's data and parameter snapshot.
Scripts, dialogs and connections in imported templates are rejected: prepare or
refresh data in the parent. No file paths, URL fetching or automatic file watching
occur during generation. To update an external template, import it again and select
the new snapshot. Existing references retain their saved version.

Sections, subreports and drill-down allow at most three combined template nesting
levels; repeat depth has its existing independent three-level limit. Each template
retains its 1,000-block limit; the whole render retains the 100,000-instance and
10,000-page limits. `frame` is not supported on section/subreport blocks and
`spaceAfter` is ignored for those page-isolated containers. Initial, repeated and
trailing boundaries do not add empty pages. `{page}` / `{pages}` always number the
complete output, including all sections and imported reports. PDF, HTML, image
exports and Word use each page's geometry; Excel retains its existing custom-paper
size approximation. Validate the actual combined template/data, not only the child.

See `samples/composed-report.nrtemplate`, its matching data and the independently
importable `samples/order-subreport.nrtemplate`.
