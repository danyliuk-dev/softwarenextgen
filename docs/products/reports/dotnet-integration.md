# .NET client and Blazor viewer

The installed SDK includes two prebuilt NuGet libraries:

- `NextgenReports.Client`: HTTP session, JSON/.NET object input, SVG preview,
  layout JSON, explicit data refresh, PDF/HTML/XLSX/DOCX download and structured errors.
- `NextgenReports.Blazor`: an **Interactive Server** component with page navigation,
  zoom, cancellation, export controls, both Office modes and loading/error states.


The report engine runs in Studio/server. Neither library embeds a native rendering
engine in the browser. WebAssembly/Auto modes and mobile/offline execution are not implemented or
verified by this integration. The separate [Linux desktop shell](desktop.md) hosts Studio. Flutter is covered by the separate
[Flutter/Dart SDK guide](flutter-integration.md).

## Run the example

Open the public topic preview on this page, or the matching offline topic example in **Help → Developer guide & code examples**. Use the installed Studio for authoring and export.

For your own .NET 10 application, copy the installed `SDK` folder to `vendor/nextgen-sdk` and start the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration). Set your application's report-server URL to the loopback URL you chose. No demo project or product build is required.

## Use the HTTP client

Add the ready-built client from the installed local feed:

```bash
dotnet add package NextgenReports.Client --version 0.2.1 --source ./vendor/nextgen-sdk/NuGet
```
No PDF, database, browser or third-party NuGet dependency is needed by this client.

```csharp
using System.Text.Json;
using NextgenReports.Client;

using var client = ReportClient.Create(new Uri("http://127.0.0.1:5274/"));
var session = await client.GetSessionAsync(cancellationToken);
if (session.Enabled)
    await client.LoginAsync(userName, password, cancellationToken);

using var template = JsonDocument.Parse(File.ReadAllText("report.nrtemplate"));
var input = ReportInput.FromObjects(template.RootElement,
    new { items = new[] { new { Name = "Chair", Amount = 42.25m } } },
    new { company = "Example company" });
var file = await client.ExportAsync(input, ReportFormat.Pdf, token: cancellationToken);
await File.WriteAllBytesAsync("report.pdf", file.Content, cancellationToken);
```

The template must declare the `company` parameter and bind the fields `Name` and
`Amount` with matching case. `FromObjects` preserves default .NET property names;
pass your own `JsonSerializerOptions` only if you also use the corresponding names
in the template. No SQL/HTTP refresh happens implicitly.

For existing JSON, construct `new ReportInput(templateJson, dataJson, parametersJson)`.
The constructor clones all JSON elements, so their source `JsonDocument` can be
disposed. Template/data must be objects; parameters must be an object or omitted.
Treat each input as a snapshot and construct a new one after editing values.

Other operations:

```csharp
var preview = await client.PreviewAsync(input, cancellationToken);
// preview.Pages: numbered SVG bytes and a data URL; one render for the entire report.
var layout = await client.PreviewDocumentAsync(input, cancellationToken);
// JsonElement containing the full ReportDocument protocol, including drawing commands.
var refreshed = await client.RefreshDataAsync(input, cancellationToken);
var updated = new ReportInput(input.Template, refreshed.GetProperty("data"), input.Parameters, useSnapshot: true);
var word = await client.ExportAsync(updated, ReportFormat.Docx,
    new ReportExportOptions(OfficeMode.Pages, FirstPage: 1, LastPage: 2, Dpi: 150),
    cancellationToken);
```

`RefreshDataAsync` uses the host's configured sources and returns a candidate
snapshot; explicitly construct a new input to use it. Credentials and connection
strings remain in the host catalog. See [data sources](data-sources.md).
`ReportExportOptions` applies only to Office; PDF and HTML export the whole report.

Handle `ReportApiException`: `StatusCode`, `Message`, and optional
`ParameterErrors` (the server's JSON structure) retain validation and role errors.
401 requires a fresh login; 403 can mean permissions or an invalid CSRF token.
The client never automatically replays a failed POST or stores your password.
Transport errors use `HttpRequestException`; cancellation/timeouts use
`OperationCanceledException`; invalid/oversized responses use `InvalidDataException`
or `JsonException`. Dispose the client when its user session ends.

## Add the Blazor component

Add the viewer package from the same feed (its client dependency is included there):

```bash
dotnet add package NextgenReports.Blazor --version 0.2.1 --source ./vendor/nextgen-sdk/NuGet
```
Register **one client per interactive circuit**, not a singleton or pooled shared
cookie handler:

```csharp
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
builder.Services.AddScoped(_ => ReportClient.Create(new Uri(reportServerUrl)));
```

Configure `AddRazorComponents().AddInteractiveServerComponents()`, `app.MapStaticAssets()` and `app.MapRazorComponents<App>().AddInteractiveServerRenderMode()` in your host. Load `_framework/blazor.web.js` in the host document and use `@rendermode InteractiveServer` on the viewer page (or its parent routes).
Include the library stylesheet in the host document:

```html
<link rel="stylesheet" href="_content/NextgenReports.Blazor/viewer.css" />
```

Then render it on an interactive page:

```razor
@using NextgenReports.Client
@using NextgenReports.Blazor
@inject ReportClient Client

<ReportViewer Client="Client" Input="input" OnLoaded="Loaded" OnError="Failed" />

@code {
    private ReportInput? input;
    private void Loaded(int pages) { /* Update your application status. */ }
    private void Failed(string message) { /* Show or record an application error. */ }
}
```

Your host supplies the input, parameter form and login flow. The component does not
reproduce Studio's designer, parameter-dialog scripts, search or drill-down. Assign
a new input object to trigger regeneration. **Generate** reruns the current input;
**Cancel** stops waiting and sends request cancellation. Disposal and replacement
inputs cancel outstanding work; a stale request cannot replace a newer preview.
`@ref` callers may also await `ReloadAsync()`.

The download JavaScript module is imported from
`_content/NextgenReports.Blazor/viewer.js`. Configure static web assets in the host
(the installed NuGet package carries these assets). Allow same-origin JS and `data:` images in
any host CSP. CSS uses `.nr-*` classes and optional variables `--nr-text`,
`--nr-background`, `--nr-control`, `--nr-border`, `--nr-canvas`, `--nr-muted`,
`--nr-error` for application theming.

## Limits and deployment

- `ReportClient.Create` uses an isolated CookieContainer, disabled redirects and a
  three-minute HttpClient timeout. HTTPS is required except for loopback HTTP.
  Custom HttpClient callers must provide equivalent cookie/redirect isolation;
  the constructor does not own that client unless `ownsHttpClient: true` is set.
- Author/Admin may generate from submitted input. Viewer accounts cannot use POST
  generation APIs; use Studio's saved reports/scheduled downloads for those users.
- Preview is one SVG archive, at most 100 pages, 25 MB per SVG and 100 MB expanded.
  All successful responses are bounded to 100 MB by the client; error bodies to
  64 KB. Pages are kept in memory. Large reports should use direct PDF export.
- Preview SVG has outlined text: it looks like the engine output but is not a
  selectable-text or screen-reader transcript. Page navigation has text labels;
  use editable Office/HTML output when the underlying text is needed.
- Download regenerates from the successful input snapshot. Time-dependent scripts
  can differ from the preview. Opted-in HTTP connections refresh on each request unless ReportInput uses
  useSnapshot:true; use a refreshed input with that flag for matching preview/download.
- Cancellation is cooperative; it cannot reverse work already completed by the host.
- A local-mode Studio grants local callers generation access. In your own remotely
  accessible app, authenticate and authorize users before invoking it; use server
  accounts/HTTPS for remote Studio. Do not expose the demo as an open proxy.
- Verified on Linux/iMac with Interactive Server and visible Chrome. WebAssembly,
  macOS, Windows, remote HTTPS deployment and package-registry publication are not
  verified. NuGet packages are supplied by the installer in a local feed; no public registry is required.

Razor library asset handling follows [Microsoft's RCL documentation](https://learn.microsoft.com/en-us/aspnet/core/blazor/components/class-libraries?view=aspnetcore-10.0).
Downloads use `DotNetStreamReference` and an object URL as described in
[Blazor file downloads](https://learn.microsoft.com/en-us/aspnet/core/blazor/file-downloads).

For automatic HTTP sources, `PreviewDocumentAsync` returns `sourceSnapshot` after
a successful refresh. Construct `new ReportInput(input.Template,
layout.GetProperty("sourceSnapshot"), input.Parameters, useSnapshot: true)` to
reuse it for exports. `ReportInput.FromObjects` also accepts `useSnapshot`. The
flag defaults to false and affects automatic refresh only; RefreshDataAsync remains
an explicit fetch. See the [HTTP guide](http-connections.md).
