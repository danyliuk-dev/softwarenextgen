# Excel and Word export

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


Generate preview, then choose **Preview → Export Office**. Select Excel (.xlsx)
or Word (.docx), a content mode, and All pages, Current page or an inclusive Page
range. Current page is captured when the dialog opens. Download creates a normal
Office file; no additional ZIP extraction, Office installation or network service
is needed to export. Cancel does not change the report.

## Choose the content mode

| Mode | Excel | Word |
|---|---|---|
| Editable text | One worksheet per selected report page, named `Page 2`, etc. Text lines become rows; distinct horizontal positions become columns. | A table of positioned text lines for each selected page, with a section boundary between source pages. Text remains editable. |
| Page images (exact layout) | One complete PNG page anchored on each worksheet, with the report's physical dimensions. | One complete PNG page positioned on each document page, with matching page size. |

Editable mode preserves **displayed strings**, including formatting already
applied by the report, leading zeros, Cyrillic, totals and text beginning with
`=`. Excel stores these as strings, never formulas or inferred numeric/date
values. To calculate further, convert the relevant cells to numbers in Excel.
This is a layout-text export, not the underlying source-data table: wrapped lines
stay separate, repeated headers/footers remain, grouped/cross-tab headers are
flattened, and overlapped fragments at the same position are joined by a newline
in Excel. It does not recreate report formulas, native charts or semantic table
relationships. Word retains basic font size, bold, color and alignment; fonts
are not embedded and may be substituted by the Office reader. Excel uses its
reader's default cell styling. Cell fills, lines, pictures, diagrams and barcodes
are **omitted from editable mode**. Use Page images to preserve every visual.
An image-only page has no editable text and therefore produces an empty sheet or
section in this mode. Word may reflow tables and add physical pages; Excel column
widths are approximate. Editability does not imply pixel-identical layout.

Page images retain the entire calculated report, including charts, barcodes,
images and conditional formatting. Text inside them is not editable, searchable
or selectable. Choose 72, 150 (default) or 300 DPI; this controls PNG pixels, not
report pagination. Higher DPI increases size and is preferable for small text
and barcodes. DPI is disabled in editable mode. The XLSX print setup fits each
worksheet on one paper page. A3, A4, A5, Letter and Legal report sizes are mapped
to standard paper; other sizes print fitted to A4, while the image on the sheet
retains its physical extent. Office/printer settings can still alter print scale.
For physical printing where exact scale matters, use PDF and verify the printer.

Both modes export the **last generated request**. Unfinished editor changes are
not included. Like PDF/HTML, export renders that saved request again; trusted
scripts that use time or randomness can produce new values. Save the project
separately to keep source data, template, scripts and designer settings.

## Limits and errors

- At most 100 selected pages, each no larger than 22 inches (1584 pt) on either
  side; page dimensions must be positive.
- Page images: 72–300 DPI, 25 million pixels per page and 100 million total.
- Editable text: 100,000 fragments, 5 million characters total, 32,767 characters
  per fragment/Excel cell, at most 256 distinct text columns per source page.
- Files are limited to 100 MB. Reduce the range or image DPI if rejected.
- Export finishes in memory before writing the destination; invalid options do
  not replace an existing output file. The Studio dialog shows the error and
  remains open so the options can be corrected.

## Installed command-line tools

With local Studio running:

```bash
python3 tools/report-tool.py --template samples/sales.nrtemplate \
  --data samples/sales.data.json --parameters samples/sales.parameters.json \
  --format xlsx --office-mode editable --output artifacts/sales.xlsx

python3 tools/report-tool.py --template samples/sales.nrtemplate \
  --data samples/sales.data.json --parameters samples/sales.parameters.json \
  --format docx --office-mode pages --first-page 2 --last-page 3 --dpi 150 \
  --output artifacts/sales-pages.docx
```

Output suffix must match `.xlsx` or `.docx`. Omit `--output` to validate without
saving. `--single-image` applies only to PNG/SVG exports.

## API and .NET

`POST /api/export/office` accepts the same `template`, `data`, `parameters` as
`/api/preview`, plus optional `options`:

```json
{"template":{},"data":{},"options":{"format":"xlsx","mode":"editable","firstPage":1,"lastPage":2,"dpi":150}}
```

Defaults: `xlsx`, `editable`, first page 1, last page equal to report page count,
150 DPI. Response uses the standard XLSX/DOCX media type, Content-Disposition and
X-Report-Pages (selected **source** pages, not Word's eventual reflowed page count).
Validation errors return HTTP 400 Problem Details; parameter errors also include
parameterErrors. The existing same-origin and trusted-script rules apply.

With the installed .NET SDK, call `ReportClient.ExportAsync` with `ReportFormat.Xlsx` or `ReportFormat.Docx` and `ReportExportOptions`; see the [.NET integration guide](dotnet-integration.md). Save the returned file bytes through your application. Files use Open XML packages with no macros, external
relationships or formula evaluation. Tests validate both formats with Microsoft's
Open XML SDK; the SDK is a test-only dependency. Package structures follow the
[SpreadsheetML](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/structure-of-a-spreadsheetml-document)
and [WordprocessingML](https://learn.microsoft.com/en-us/office/open-xml/word/overview)
documentation. Export itself uses .NET XML/ZIP and the existing PNG renderer.

Linux on the local iMac is the verification platform. Native Microsoft Excel/Word,
macOS and Windows remain unverified; browser download verification is not a claim
that Microsoft Office has been tested.
