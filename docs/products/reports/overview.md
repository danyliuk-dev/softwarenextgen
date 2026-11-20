# NextgenReportEngine

Create reports in the installed **Nextgen Reports** application, or connect your own application to its ready-to-run engine using the included SDK.

## Run

[Install your platform package](/docs/reports/installation), then open **Nextgen Reports** from Applications or your saved Linux AppImage. Studio and the engine start together. Select Preview, change the sample, and export PDF, HTML, images, Excel or Word. No product compilation is required.

## Connect your application

The installed resources include `SDK/NuGet` with `NextgenReports.Client` and `NextgenReports.Blazor`, and `SDK/Flutter/nextgen_reports`. Copy these into your application's vendor directory. Follow the [developer guide](docs/developer-guide.md) to start the installed engine for integration, then [.NET/Blazor](docs/dotnet-integration.md) or [Flutter/Dart](docs/flutter-integration.md) to connect your app. Rendering runs in the engine, not in the browser or mobile device.

## Learn and create

- [Desktop guide](docs/desktop.md): launch, save, recovery and local data.
- [Report authoring manual](docs/report-authoring-manual.md): designer, parameters and export.
- [TypeScript and events](docs/report-logic-manual.md): trusted report logic.
- [Template format](docs/template-format.md) and [API authoring](docs/agent-authoring.md).
- [Data sources](docs/data-sources.md), [data preparation](docs/data-preparation.md), [Office exports](docs/office-export.md) and [image exports](docs/image-export.md).

Use **Help** inside the installed app for offline manuals. Public topic previews use synthetic data; your local projects remain on your computer.
