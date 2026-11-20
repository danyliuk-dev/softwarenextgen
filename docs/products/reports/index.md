# Nextgen Reports documentation

Installed examples: copy `SDK` from the application resources to a writable folder and run tool commands from that copied SDK folder. It contains `tools/` and `samples/`. Python tools require Python 3 and connect to the [installed integration engine](developer-guide.md#start-the-installed-engine-for-integration); they do not compile the product. Adjust `--base` if you chose a different port. Output paths are relative to your working folder.


All guides and demo UI are in English. Examples use fictional data. Programming
is optional for report authors; application developers can start with runnable code.

## Choose your starting point

| Task | Guide |
| --- | --- |
| Use the desktop application | [Desktop Studio on Linux](desktop.md) |
| Run Studio | [Installation](../README.md#run) |
| Call the engine from application code | [Developer guide and complete examples](developer-guide.md) |
| Integrate a .NET/Blazor app | [.NET client and Blazor viewer](dotnet-integration.md) |
| Integrate Flutter/Dart | [Flutter SDK and Web demo](flutter-integration.md) |
| Create or edit a report | [Report authoring manual](report-authoring-manual.md) |
| Build forms and step-by-step dialogs | [Dialog Toolbox](toolbox.md) |
| Add validation, calculations and dependent choices | [TypeScript and events](report-logic-manual.md) |
| Author template JSON or automate generation | [Template format](template-format.md), [API/CLI authoring](agent-authoring.md) |
| Connect PostgreSQL, MSSQL, MySQL, MariaDB, SQLite, JSON or objects | [Data sources](data-sources.md) |
| Refresh HTTP data or transform snapshots | [HTTP sources](http-connections.md), [data preparation](data-preparation.md) |
| Import data | [CSV/TSV](data-import.md), [Excel XLSX](report-authoring-manual.md#excel-import) |
| Export reports | [Office](office-export.md), [HTML](report-authoring-manual.md#preview), [page images](image-export.md) |
| Add interactive report details | [Drill-down](drill-down.md) |
| Store versions and run scheduled jobs | [Library](report-library.md), [server operations](server-operations.md) |
| Check scope and verification | [Roadmap](roadmap.md), [verification log](verification.md) |

## Learn by doing

1. Open a sample project, change a parameter and generate Preview/PDF.
2. Follow **Build your first report** in the authoring manual. Create a three-row
   table, heading and page numbers; save and reopen the project.
3. Add a company parameter and test Cancel/Generate in the parameter form.
4. Build two dialog pages with Next/Back and test required fields and sequential steps.
5. Read the event guide and try `samples/inventory.nrtemplate` for validation and filtering.
6. Follow the developer guide to connect the installed SDK and generate outputs from your own C# application.
7. Open the Blazor or Flutter demo, change data and inspect the corresponding code guide.

## Read in the browser

Studio **Manual ↗** or **Code → Manual** opens the local English authoring guide.
Its **Developer guide & code examples** link opens readable code, with links to
local .NET, Flutter and data-source guides. The desktop launcher's documentation
action opens the developer guide directly. No GitHub connection is needed. The developer hub uses three numbered cards to
explain the learning path; code blocks have language labels, syntax colors and
**Copy code**. A successful copy shows **Copied**. On restricted browser contexts,
select and copy the text manually. Narrow screens stack the cards; long code lines
scroll inside their code block.
