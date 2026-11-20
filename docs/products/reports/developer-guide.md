# Developer guide and code examples

Start with a complete working example, then choose the integration for your app.
Commands use the installed product and SDK. Examples contain fictional data. Build only your own application; the supplied libraries and engine are ready to use.

## Installed SDK and first connection

Install **Nextgen Reports**, then copy its `SDK` folder into your application's `vendor/nextgen-sdk`. The package contains prebuilt .NET NuGet libraries and a Flutter/Dart package. The desktop app can author reports immediately; development tools are needed only for building your own application.

## Start the installed engine for integration

The desktop application's engine uses a private session and a dynamically selected port. Applications should start a separate instance of the installed executable with their own state folder and explicit loopback address. Do not reuse the desktop session or its private token.

Set the resources path for your platform (see [Installation](/docs/reports/installation)). For example, on macOS:

```bash
export NEXTGEN_RESOURCES="/Applications/Nextgen Reports.app/Contents/Resources"
```

On Linux, after extracting the AppImage into `~/NextgenInstalled/reports`:

```bash
export NEXTGEN_RESOURCES="$HOME/NextgenInstalled/reports/squashfs-root/resources"
```

Then start the prebuilt engine in a terminal:

```bash
mkdir -p "$HOME/NextgenIntegration/reports"
NEXTGEN_STATE_DIRECTORY="$HOME/NextgenIntegration/reports" \
  "$NEXTGEN_RESOURCES/server/NextgenReports.Studio" \
  --contentRoot "$NEXTGEN_RESOURCES/server" --urls http://127.0.0.1:5274
```

On Windows, use PowerShell instead of the Unix shell commands above. Adjust the resources path if you selected another installation folder:

```powershell
$env:NEXTGEN_RESOURCES = "$env:LOCALAPPDATA\Programs\Nextgen Reports\resources"
$env:NEXTGEN_STATE_DIRECTORY = "$env:LOCALAPPDATA\NextgenIntegration\reports"
New-Item -ItemType Directory -Force $env:NEXTGEN_STATE_DIRECTORY | Out-Null
& "$env:NEXTGEN_RESOURCES\server\NextgenReports.Studio.exe" `
  --contentRoot "$env:NEXTGEN_RESOURCES\server" --urls http://127.0.0.1:5274
```

Leave this terminal open while your app uses the engine; Ctrl+C stops it. Open `http://127.0.0.1:5274` to confirm Studio loads. If the port is occupied, choose another free loopback port and use the same URL in your client. Each running instance needs a separate state directory. The engine is self-contained: do not install .NET or build Studio just to run it.

Local mode is for trusted applications on your computer. Do not change the binding to a public interface. A remote integration requires a separately administered HTTPS server and per-user access controls. Mobile applications cannot reach your computer through the phone's localhost.

## Call the HTTP API

Start the installed engine as described above.

This complete local-mode request writes a PDF containing Hello from HTTP:

```sh
curl --fail-with-body http://127.0.0.1:5274/api/render \
  -H 'Content-Type: application/json' \
  --data '{"template":{"version":1,"blocks":[{"type":"text","text":"{{data.message}}"}]},"data":{"message":"Hello from HTTP"},"parameters":{}}' \
  --output http-example.pdf
```

The command saves `http-example.pdf` in your current directory. Use the same request
with `/api/preview` for layout JSON. Errors use HTTP 400 Problem Details;
`parameterErrors` identifies invalid fields. With server accounts enabled, use
session cookies, login and CSRF; the SDK examples handle that workflow. Remote
hosting requires HTTPS. Use a separately administered HTTPS endpoint for remote access.

## Use the .NET HTTP SDK

From your .NET 10 application directory, run:

```bash
dotnet add package NextgenReports.Client --version 0.2.1 --source ./vendor/nextgen-sdk/NuGet
```
 This example
uses exact lowercase JSON keys, so it has no naming-policy ambiguity:

```csharp
using System.Text.Json;
using NextgenReports.Client;

using var client = ReportClient.Create(new Uri("http://127.0.0.1:5274/"));
using var template = JsonDocument.Parse("""
{"version":1,"blocks":[{"type":"text","text":"{{data.message}}"}]}
""");
var input = ReportInput.FromObjects(template.RootElement,
    new { message = "Hello from the .NET SDK" });
var session = await client.GetSessionAsync();
// If session.Enabled, call LoginAsync with your host-supplied credentials first.
var file = await client.ExportAsync(input, ReportFormat.Pdf);
await File.WriteAllBytesAsync("sdk-report.pdf", file.Content);
```

Use one client per user session. Catch `ReportApiException` for HTTP/validation
errors; handle cancellation and transport errors separately. The client never
replays failed POSTs. Full login, JSON, refresh, export and error examples:
[.NET and Blazor integration](dotnet-integration.md).

## Embed the Blazor viewer

Add the installed `NextgenReports.Blazor` NuGet package, register a client per interactive circuit, and configure static web assets as shown in the [Blazor setup guide](dotnet-integration.md#add-the-blazor-component).

```razor
@using NextgenReports.Client
@using NextgenReports.Blazor
@inject ReportClient Client

<ReportViewer Client="Client" Input="input" />

@code {
    private ReportInput input = ReportInput.FromObjects(
        System.Text.Json.JsonSerializer.SerializeToElement(new {
            version = 1,
            blocks = new[] { new { type = "text", text = "{{data.message}}" } }
        }), new { message = "Hello from Blazor" });
}
```

Assign a new input after edits. Navigation reuses generated pages; Download
regenerates from the successful input snapshot. Viewer accounts cannot submit
new report generation requests. WebAssembly/Auto are not implemented here.

## Use Flutter and Dart

Add the installed SDK package as in [Flutter setup](flutter-integration.md).
For Flutter Web, serve the app from Studio's origin; `Uri.base.resolve('/')`
uses that origin. Native Dart hosts use an explicit HTTPS server URL.

```dart
import 'package:nextgen_reports/nextgen_reports.dart';

final client = ReportClient(Uri.base.resolve('/'));
final input = ReportInput({
  'version': 1,
  'blocks': [{'type': 'text', 'text': '{{data.message}}'}],
}, {'message': 'Hello from Flutter'});

// Place this widget in your page's build method.
// In server mode, complete client.login(...) before displaying it.
final viewer = ReportViewer(client: client, input: input,
  onDownload: (file) async {
    // Integrate your app's save/share flow with file.content and file.fileName.
    // Complete browser implementation: examples/flutter_demo/lib/save_file_web.dart.
  });

// HTTP-only generation (inside an async function):
// final pdf = await client.export(input, ReportFormat.pdf);
// client.close(); // When the owner of the client is disposed.
```

The download callback above marks the host integration point; it does not save
files by itself. The runnable Web demo includes the complete Blob download flow.
Objects need `toJson()`; dates need explicit JSON conversion. Assign new input
snapshots after edits and close the client when finished. Full code covers login,
refresh, cancellation, errors, export options and platform limits in the Flutter
setup guide. Android/iOS devices and native desktop GUI remain unverified.

## Connect SQL, JSON files and application objects

Direct JSON/C# objects require no catalog. For external refresh, the host supplies
source IDs, queries, connection environment variables or callbacks; the report
stores bindings and a saved data snapshot. Supported providers: PostgreSQL,
SQL Server, MySQL, MariaDB and SQLite, plus JSON files and .NET object callbacks.

```json
[{
  "id": "sales", "label": "Sales", "provider": "postgresql",
  "connectionEnvironment": "REPORTS_DATABASE",
  "query": "SELECT id, region, amount FROM orders WHERE region=@region ORDER BY id",
  "parameters": {"region": {"type": "string"}}
}]
```

Save this host catalog outside the report and set `NEXTGEN_DATA_SOURCES` to its
absolute path; set `REPORTS_DATABASE` in the host environment. Create the orders
table/data in your own database. In Studio Connections choose sales, target items,
empty array path, and bind source region to a string report parameter. Refresh,
inspect and Apply snapshot before generating. No refresh occurs implicitly.
See [data sources](data-sources.md) for all five provider configurations, JSON file
and object callback code, expected sample totals, limits and SQL Server's current
live-verification limitation. Never put connection secrets in report parameters.

## Export modes and expected results

| Format/mode | Result |
| --- | --- |
| PDF | Paginated report with embedded fonts |
| HTML | Standalone pages with embedded fonts/images |
| Excel/Word editable | Displayed text in editable cells/paragraphs; graphics omitted |
| Excel/Word exact pages | Complete pages as PNG images; text is not independently editable |

Editable Office does not preserve original typed numbers/formulas or native Office
charts. Exact pages supports page range and DPI. See [Office export](office-export.md)
and [page image export](image-export.md) for API/CLI examples and limits.

## Read and copy code examples

Code blocks use local syntax highlighting for C#, Dart, TypeScript, JSON, Razor markup and shell commands. Different colors identify keywords, strings, numbers, comments, types and properties. Select **Copy code** above a block to copy its original source without formatting. Highlighting works without an external CDN; JavaScript must be enabled. Razor examples highlight markup; embedded C# expressions may use the default text color.
