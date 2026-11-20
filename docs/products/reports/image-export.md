# Page image export

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


PNG and SVG export the engine's final positioned pages, including tables, charts,
barcodes, images, headers and footers. They are page pictures, not editable report
projects or data exports. Generate first; Studio exports the last generated
request even if the editors contain unfinished changes. As with PDF/HTML, export
renders that saved request again, so nondeterministic trusted scripts can produce
new values. Save the project separately to preserve template and source data.

## Studio

1. Generate preview, then open **Preview → Export images**.
2. Choose PNG or SVG. PNG offers 72, 150 (default) or 300 DPI. Higher DPI creates
   more pixels; it does not change page breaks or wrap text again. SVG is vector
   and disables the DPI selector.
3. Choose All pages, Current page or Page range. Current uses the viewer's selected
   page at dialog opening; range endpoints are inclusive and start at 1.
4. Leave **Always package as ZIP** checked for an archive. Uncheck it for a single
   selected page to download one PNG/SVG. Multiple pages always produce ZIP.
5. Download and inspect the result. ZIP entries retain original page numbers:
   page-0002.png, page-0003.png, etc. Cancel leaves the report unchanged.

The page background is opaque white. SVG embeds raster images and converts text
into vector outlines using the same regular/bold DejaVu fonts as the report.
It needs no installed fonts or network resources. Text is **not selectable or
searchable** in PNG/SVG; use PDF or HTML when text search/accessibility is needed.
SVG retains physical dimensions in points plus a matching viewBox. Raster PNG
stores its DPI in pHYs metadata; consumers may choose their own print scaling.

PNG dimensions are ceil(page points × DPI / 72). A4 portrait (595.28 × 841.89pt)
is 1241 × 1754px at 150 DPI. For barcode scanning, prefer 150–300 DPI and adequate
module width: a one-pixel module at 72 DPI may require magnification by a detector.
Neither resolution settings nor successful software decoding prove physical
printer/scanner behavior. Raster edges can differ slightly from browser/PDF
antialiasing; layout coordinates and embedded font outlines are retained.

Limits: 72–300 DPI, at most 100 selected pages, 25 million pixels per PNG page,
100 million pixels per PNG export, 25 MB per SVG and 100 MB ZIP. Lower DPI or
select a smaller page range when a limit is reached. Export finishes in memory
before writing the destination; rejected options do not create partial files.
Large exports use native raster memory in addition to the output buffer.

## Installed command-line tools

With local Studio running:

```bash
# All pages, ZIP containing PNG files at 150 DPI
python3 tools/report-tool.py --template samples/sales.nrtemplate \
  --data samples/sales.data.json --parameters samples/sales.parameters.json \
  --format png --output artifacts/sales-pages.zip

# One vector page, standalone SVG
python3 tools/report-tool.py --template samples/circular-charts.nrtemplate \
  --data samples/circular-charts.data.json --format svg \
  --first-page 1 --last-page 1 --single-image --output artifacts/composition.svg
```

Use --dpi 300 for high-resolution PNG and --first-page/--last-page for a range.
--single-image disables forced ZIP only when exactly one page is selected.
The output suffix must match the actual response (.zip, .png or .svg).
Omit --output to validate export without saving it. report-tool.py requires Studio.

## API and .NET

POST /api/export/images accepts the same template/data/parameters as /api/preview,
plus optional options:

```json
{"template":{},"data":{},"options":{"format":"png","dpi":150,"firstPage":1,"lastPage":2,"archive":true}}
```

Defaults: png, 150 DPI, first page 1, last page equal to the report's page count,
archive true. The result is application/zip, image/png or image/svg+xml with
Content-Disposition and X-Report-Pages (number of exported pages). Validation
errors return HTTP 400 Problem Details, including parameterErrors where relevant.
The existing same-origin rules apply. Scripts follow the host's opt-in setting.

For .NET image export, submit the documented JSON body to this endpoint using HttpClient, then save the returned bytes. Use the installed client for preview and PDF/Office export as described in the [.NET guide](dotnet-integration.md).
SVG uses outlined text; no third-party SVG parser is used. SkiaSharp and Linux
native assets are pinned to 3.119.2, with their upstream notices shipped under
licenses/. Local Linux on iMac is verified; macOS/Windows remain unverified.
