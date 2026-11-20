# Flutter SDK and web demo

The installed `SDK/Flutter/nextgen_reports` package contains a Dart HTTP client and Flutter `ReportViewer`.
The report engine remains in Studio/server. The package accepts JSON-compatible
maps and objects with `toJson()`, supports cookie/CSRF login, explicit source refresh,
PNG preview, PDF/HTML/XLSX/DOCX export and both Office modes.

## Run the web demo

Open the installed integration engine following the [developer guide](developer-guide.md#start-the-installed-engine-for-integration), then open `http://127.0.0.1:5274/flutter-demo/` in your browser. Adjust the port if you selected another. The installer already contains the compiled web demo and local rendering assets; no Flutter compilation is needed to try it.

1. Local mode immediately shows a three-page equipment report with 65 rows.
   In server mode, sign in as Author/Admin. Viewer sees a permissions explanation
   and cannot submit reports for generation.
2. Use **Next page / Previous page** and **Zoom**. Navigation uses already generated
   PNG pages, without repeating the server calculation. Fit width adapts to the
   available viewport; other zoom values scale the 96 DPI page image.
3. Change **Company** and **Rows**, then **Apply data**. The demo clamps rows to 1–100.
   The new preview starts on page 1 and contains the changed Dart object values.
4. Choose **PDF**, **HTML**, **Excel** or **Word**, then **Download**. Excel/Word offer
   **Editable** or **Exact pages**. Downloads use the last successful input snapshot;
   unsubmitted field edits do not change that snapshot.
5. Enable **Demonstrate report error** and apply. The error replaces the preview;
   Download is unavailable. Clear the checkbox and apply to recover. **Cancel**
   aborts an in-flight request; late responses cannot replace newer results.
6. Switch **Dark theme / Light theme**. Narrow screens wrap the controls and keep
   report scrolling inside the viewer.

## Integrate the package

To build your own app, use Flutter >= 3.38 and Dart >= 3.10. Copy `SDK/Flutter/nextgen_reports` from the installed resources into your app as `vendor/nextgen_reports`. Add this dependency to your pubspec.yaml:

```yaml
dependencies:
  nextgen_reports:
    path: vendor/nextgen_reports
```

Run `flutter pub get` in your own application. The client package comes from the installer; Flutter resolves its declared framework and third-party dependencies normally. Keep the copied package version pinned when updating.
For HTTP-only Dart hosts, import `package:nextgen_reports/client.dart` to avoid
importing Flutter UI. For Flutter, import `package:nextgen_reports/nextgen_reports.dart`.

```dart
final client = ReportClient(Uri.parse('https://reports.example.test/'));
final session = await client.getSession();
if (session.enabled) await client.login(userName, password);

final input = ReportInput(templateMap, {
  'items': [Equipment('Chair', 42.25)],
}, parameters: {'company': 'Example company'});

class Equipment {
  final String name;
  final double amount;
  Equipment(this.name, this.amount);
  Map<String, Object> toJson() => {'Name': name, 'Amount': amount};
}
```

The template must declare `company` and bind `Name`/`Amount` with matching case.
`ReportInput` serializes and owns a snapshot. Later mutations of the supplied maps
or objects do not change it. Construct a new input to apply edits. Template/data
must serialize to JSON objects; parameters must be an object or omitted. Dates,
custom numbers and other non-JSON values need explicit conversion in `toJson()`;
Dart `double` values are not a lossless replacement for arbitrary decimal precision.

```dart
ReportViewer(
  client: client,
  input: input,
  height: 700,
  onLoaded: (pages) => updateStatus('Ready: $pages pages'),
  onError: (message) => showReportError(message),
  onDownload: (file) async {
    // Host-owned save/share flow: file.content, file.mediaType, file.fileName.
    await saveUsingYourPlatformPicker(file);
  },
)
```

`onDownload` is required to enable the Download button. The package never writes to
an arbitrary device path. The web demo includes a Blob/object-URL download callback;
native applications supply their own file picker/share integration. The host also
owns parameter forms, login and application authorization. The widget does not
reproduce Studio's designer, scripted parameter dialogs, search or drill-down.

Use a new `ReportInput` or call `ReportViewerState.reload()` through a `GlobalKey`
to regenerate. Widget disposal/replacement cancels outstanding work. The caller
owns the client and calls `client.close()` when it is no longer needed. On Web,
close releases the transport but does not clear shared browser cookies; call
`logout()` to sign out.

## Client operations

```dart
final cancellation = ReportCancellation();
final pages = await client.preview(input, cancellation: cancellation);
// One render; numbered PNG bytes with width/height metadata.
final layout = await client.previewDocument(input);
final refreshed = await client.refreshData(input);
final updated = ReportInput(templateMap, refreshed['data'], parameters: values);
final word = await client.export(updated, ReportFormat.docx,
  options: const ReportExportOptions(
    mode: OfficeMode.pages, firstPage: 1, lastPage: 2, dpi: 150));
// cancellation.cancel(); aborts a pending operation.
```

Refresh uses the host catalog and returns a candidate snapshot. It never changes
`input` or the library automatically. Office options apply only to XLSX/DOCX;
PDF/HTML export the whole report. Preview and download are separate renders:
time-dependent scripts can produce different results even with identical input.

Errors are `ReportApiException` with `statusCode`, `message` and the server's
optional `parameterErrors`. 401 requires login; 403 can mean permissions or CSRF.
An injected custom HTTP client owns its cookie/cancellation behavior and is not
closed by the SDK. Failed POSTs are not automatically retried. Cancel produces `ReportCancelled`;
the default three-minute operation timeout produces `TimeoutException`. Transport
failures use the HTTP client's exception; malformed/oversized responses produce
format/archive errors. Credentials are never retained for automatic re-login.

## Sessions and hosting

- Native Dart uses a separate cookie jar per client, bound to the chosen origin and
  the server's `Nextgen.Session`/`Nextgen.Csrf` cookies. Do not share a client between
  users. Redirects are disabled. HTTPS is required except localhost/127.0.0.1/::1.
- Flutter Web must share Studio's origin. Browser cookies are shared with Studio
  and other tabs, not isolated per `ReportClient` instance. Use one client per app;
  signing out also affects other tabs of that report server. A fresh session/CSRF
  token is fetched before each operation. Cross-origin CORS access is not enabled.
- The included web build is served at `/flutter-demo/`. Its static assets are public
  in server mode so the login screen can load, but report data and POST APIs keep
  their existing authentication, CSRF, role and HTTPS restrictions.
- Only this asset path permits WebAssembly and blob workers in CSP, required by
  local CanvasKit. Studio's existing CSP is preserved elsewhere. A custom host must
  provide the same-origin routing, static assets and appropriate CSP.
- Author/Admin may generate submitted reports. Viewer uses Studio's saved report or
  scheduled-result downloads; this widget does not bypass those permissions.
- The example is Web-only. A native app must configure a reachable report-server
  HTTPS URL; a phone's localhost is the phone, not this iMac. Device permissions,
  platform packaging, certificates and native save/share UI belong to the host app.

## Limits and verification

Preview: one PNG ZIP at 96 DPI, at most 100 pages, 25 MB per PNG, 100 MB expanded
bytes, 25 million pixels/page and 100 million pixels/preview. ZIP filenames,
entry counts, declared sizes, CRC and PNG dimensions are checked before display;
entries are never extracted to filesystem paths. All HTTP responses are bounded
at 100 MB (error bodies at 64 KB). Large reports can exceed mobile memory despite
these bounds; prefer direct PDF export. PNG text is not selectable and zoom is
raster scaling; export PDF for vector output or editable Office for text editing.

Verified here: Flutter Web in visible Chrome on Linux/iMac, Flutter widget/client
tests, and the native Dart HTTP client against real local/authenticated servers.
Android/iOS devices, Flutter native desktop GUI, macOS/Windows and remote HTTPS
hosting remain unverified. This SDK is a server-backed integration, not an offline
mobile engine. The separate [Linux desktop shell](desktop.md) hosts Studio rather than this Flutter example.

The client uses [http abortable requests](https://pub.dev/documentation/http/latest/)
and [archive](https://pub.dev/packages/archive); the installed package declares its dependency versions. The bundled web demo includes its font license in its assets.

For sources with automatic HTTP refresh, separate preview/export requests may fetch
different data. Pass `useSnapshot: true` to `ReportInput` when using an explicitly
refreshed snapshot for matching preview/download. The default is false. Explicit
refresh still fetches; the option only bypasses automatic fetch during rendering.
