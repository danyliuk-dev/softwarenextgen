# CSV / TSV / Excel data import

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


Import is a one-time conversion into the project's JSON data. It does not create
a live file connection or change the report template. Save the project to retain
the imported rows. No uploaded file or server-side file path is stored.

1. Open **Data → Import data**, choose a UTF-8 file (optional BOM), and set the
   target **Table name**. A `.tsv` file selects Tab; other files default to Comma.
   Choose Comma, Semicolon, Tab or Pipe explicitly if needed.
2. Leave **First row contains headers** checked, or uncheck it to use column1,
   column2, etc. Headers are trimmed, must be nonempty/distinct and at most 100
   characters. Field keys use letters/digits/underscores: `Product name` becomes
   `Product_name`; collisions gain suffixes, non-ASCII-only names become columnN.
   The preview shows both original headers and generated field names.
3. **Keep all text** is the default. **Infer columns** examines every nonempty
   value in each column, not only the 20 preview rows. A column becomes boolean
   only for lowercase true/false, or number only for plain decimal values with a
   dot and at most 15 digits. Leading zeros, dates, exponents, locale decimals,
   mixed values and longer numbers stay strings. Whitespace in values is retained.
4. Select **Preview**. Review row/column counts, generated names and types. Each
   column can override the default with auto/string/number/boolean. Changing parse
   options or an override requires another Preview. Forced types reject invalid
   values; they never silently replace bad values with null. Empty numeric/boolean
   cells become null; empty string cells stay empty strings. Entirely empty columns
   infer as string. Formulas and HTML remain literal data.
5. **Apply import** adds one root-level array to the current JSON object. Other
   properties are retained. Existing arrays require **Replace existing table**;
   scalar/object properties cannot be replaced. Table names must be 1–80 ASCII
   letters/digits/underscores, start with a letter/underscore and cannot be
   __proto__, constructor or prototype. Cancel, parse errors and invalid options
   leave data unchanged. A concurrent data edit requires reopening the import.
6. The Data table view selects the imported array. Set a report table's **Data
   source** to the table name and its columns to the generated field keys. Generate
   preview and export PDF. Importing does not automatically rebuild report columns.
7. **Undo import** restores the data before the latest applied import, while it is
   still unchanged. It is separate from template Undo/Redo, has one level and is
   cleared by opening a project. Save/reopen the project to retain imported data;
   loading a project does not retain the original file or import settings.

Quoted fields support embedded delimiters, doubled quotes (`""`) and embedded
line breaks. CRLF/LF/CR record separators are accepted; quoted line endings are
preserved. Empty physical records are skipped, but quoted empty fields are data.
Rows must have identical field counts. Quotes in unquoted fields, unclosed quotes,
characters after a closing quote (including spaces), NUL and duplicate/empty
headers are rejected. There is no comment syntax, delimiter guessing, date parser,
formula evaluation, encoding conversion or automatic refresh in CSV/TSV mode.

Limits: 2 MB UTF-8 input, 10,000 data rows, 50 columns, 200,000 cells including
headers, 64,000 characters per field, 6 MB compact imported JSON. Applying also
checks the existing 8 MB project limit. Preview shows at most 20 rows and truncates
long cell display to 500 characters; the imported values are not truncated.
JSON numbers are used in the browser, so identifiers should remain strings.

## Example and CLI

Try `samples/import/items.csv` or `samples/import/items.tsv` with table name `items`
and Infer columns. Codes 001/002/003 stay strings, quantity/price become numbers,
active becomes boolean, quoted product names retain commas, quotes and line breaks.
Use `samples/import/inventory.nrtemplate` for the resulting JSON data.

With Studio running locally:

```bash
python3 tools/import-delimited.py --input samples/import/items.csv \
  --table items --typing infer --output artifacts/imported-items.json
python3 tools/report-tool.py --template samples/import/inventory.nrtemplate \
  --data artifacts/imported-items.json --format pdf --output artifacts/imported-items.pdf
```

For TSV add `--delimiter tab`; for other delimiters use semicolon/pipe. Use
`--no-header` for generated headers, or repeated `--column-type price=number`
options using normalized field keys. The CLI writes a new JSON object, does not
merge with an existing data file, and refuses an existing output unless `--force`
is given. stdout/stderr are JSON. It calls the same API/parser as Studio.

## API

`POST /api/data/import`, JSON body:

```json
{"text":"id,amount\n001,12.50\n","delimiter":",","hasHeader":true,"typing":"infer","columnTypes":{"id":"string"}}
```

Returns `{columns:[{header,field,type}],rows:[{...}]}`. Defaults are comma, header
true and typing strings. Overrides are keyed by generated field names and may be
auto/string/number/boolean; unknown fields/types fail. The endpoint returns rows,
not a report data root object; callers choose their table name. Validation errors
return HTTP 400 Problem Details. Import performs no filesystem or URL access.


## Excel worksheets (.xlsx)

Open **Data → Import data**, select `samples/import/inventory.xlsx`, choose
**Worksheet → Items**, set Table name to `items` and Types to **Infer columns**.
Preview shows three rows: codes retain leading zeros, quantity/price become
numbers, active becomes boolean and delivered contains ISO dates. Apply import,
use `samples/import/inventory.nrtemplate`, then Generate. Replacement, Cancel,
Undo import, field overrides and project saving behave exactly as for CSV/TSV.
Changing the worksheet, header, types or formula option invalidates the preview.
Delimiter is disabled for XLSX. Keep all text remains the default.

The Summary worksheet contains a formula. Preview initially rejects it. Only after
recalculating and saving a real workbook in Excel/LibreOffice should you enable
**Use cached formula values** and Preview again. The sample has an explicitly
prepared cache of 187.7. The importer never calculates formulas; caches can be
stale even when present. Missing caches and Excel error cells fail. This behavior
follows the [SpreadsheetML formula/cache distinction](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-formulas).

Worksheets, including hidden ones, are listed in workbook order. Empty rows are
skipped, sparse cells are filled with empty values and hidden/filtered rows and
columns are included. Headers are the first nonempty row unless disabled. Values
outside columns A–AX fail; merged cells must be unmerged first. There is no range
selection, named-table selection or automatic refresh. Other worksheets are not
imported until selected.

Text, shared/rich strings, numeric and boolean cells are read as stored values;
Excel fonts, colors, display rounding, currency/percent symbols and numeric
zero-padding are not imported. Store identifiers as text in Excel. Numeric
exponents are expanded to decimal text; inference still uses the conservative
15-digit rule. Values outside decimal range/precision (28 significant digits,
28 fractional places) fail instead of silently rounding.

Recognized date formats become ISO text: built-in 14–22, 45 and 47 and custom
formats with date/time tokens y/d/h/s after removing quoted/escaped literals and
locale/color annotations. Both 1900 and 1904 date systems are supported. Date-only
formats produce yyyy-MM-dd; time-only produce HH:mm:ss with optional milliseconds;
combined formats produce yyyy-MM-ddTHH:mm:ss. Unrecognized formats remain numeric
values. Negative/out-of-range date serials, Excel's fictitious 1900-02-29 and
elapsed-time formats ([h]/[m]/[s], built-in 46) fail. Convert unsupported dates or
durations to explicit ISO text/plain numbers in the workbook first.

Only transitional .xlsx is supported, not .xls, .xlsm, .xlsb, strict OOXML or
encrypted workbooks. No macros, external links or XML external entities are run
or fetched. Limits: 4 MB file, 1,024 ZIP entries, 16 MB per expanded part, 32 MB
expanded total, 100 worksheets; the shared 10,000 data rows / 50 columns / 200,000
cells / 64,000 characters per field / 6 MB JSON / 8 MB project limits also apply.

### XLSX CLI and API

```bash
python3 tools/import-xlsx.py --input samples/import/inventory.xlsx --list-sheets
python3 tools/import-xlsx.py --input samples/import/inventory.xlsx --sheet Items \
  --table items --typing infer --output artifacts/xlsx-items.json
python3 tools/report-tool.py --template samples/import/inventory.nrtemplate \
  --data artifacts/xlsx-items.json --format pdf --output artifacts/xlsx-items.pdf
```

The XLSX CLI supports --no-header, repeated --column-type FIELD=TYPE,
--use-cached-formulas and --force. It writes a new JSON data object, not a merge.
Existing outputs are refused without --force. Warnings are included in JSON stdout.

`POST /api/data/xlsx/sheets` accepts `{contentBase64:"..."}` and returns
`{sheets:[{name,hidden}]}`. `POST /api/data/xlsx` accepts
`{contentBase64:"...",sheet:"Items",hasHeader:true,typing:"infer",columnTypes:{},useCachedFormulas:false}`
and returns `{columns,rows,warnings}`. Errors return HTTP 400 Problem Details.
No server-side file paths are accepted; neither endpoint persists the workbook.
