# Software Next Generation

Private product portal at https://softwarenextgen.com, ASP.NET Core 10 and PostgreSQL 18.

Public homepage; invitation-only accounts; mandatory TOTP MFA; administrator user/invitation/release management; authenticated product downloads and 78 public documentation pages.

## Build

`python3 packaging/build-docs.py` imports API manuals from sibling NextgenComponents and NextgenReportEngine checkouts, applying installer-oriented sources from `docs/products/<product>/<slug>.md`. Edit these distribution sources for user launch/integration instructions; retain API content and keep repository build steps out of published/offline guides. `dotnet publish server -c Release -o artifacts/site` builds the website. Generated manuals are included in the release, outside wwwroot; manual routes and previews are public.

Run with `ConnectionStrings__Nextgen`, `KeysPath`, `ASPNETCORE_URLS`, `AllowedHosts` and `ReleasesBucket`. Keep secrets outside source. HTTPS is required for cookies; local integration tests use a trusted loopback proxy header and an isolated PostgreSQL instance on port 55461.

## Production

GCP configuration `dme-prod`, project `causal-armor-506513-a7`. VM `dmewebapp` in `us-east4-c`. Service `nextgensoftware`, loopback port 5338, `/opt/nextgensoftware/current`, config `/etc/nextgensoftware/app.env`, persistent keys `/var/lib/nextgensoftware/keys`.

Dedicated database `nextgen_software` and role `nextgen_software_app` on `dme-next-database`. The role has no superuser, role-creation or database-creation rights.

Private bucket `gs://causal-armor-506513-a7-nextgensoftware-installers`, region us-east4, public-access prevention and versioning enabled. VM identity has bucket-scoped objectCreator and objectViewer only. Website streams authenticated downloads; it does not expose public object URLs. Release rows store platform, size and SHA-256. Use the deployment importer for installers exceeding the Cloudflare upload limit; smaller future releases can be uploaded in Administration → Product releases.

Mail uses the existing Microsoft Graph application through `support@dmeclinic.com`. Delivery status `accepted` means accepted by Microsoft Graph, not confirmation of recipient inbox delivery. Failed sends retry with backoff. Invitations expire in 48 hours and are one-use. The apex domain currently has no email-receiving MX configuration; admin@softwarenextgen.com is an application login.

TLS certificate covers apex and www; Nginx redirects www to apex. Certbot renews it automatically with the existing Nginx reload hook. The six pre-existing subdomain records are preserved.

## Accounts and security

A password-only session can only enroll or verify MFA. Every full session is checked against enabled state, current generation and role in PostgreSQL. Blocking a user invalidates existing sessions. Reissuing a password invitation preserves existing MFA and invalidates existing sessions. TOTP and recovery-code consumption are transactional; recovery codes are stored as hashes and displayed once. Encrypted MFA secrets require the persistent Data Protection key directory for disaster recovery. Account lockouts persist in PostgreSQL. Every POST validates antiforgery tokens.

The owner sets their password, scans their own QR and saves recovery codes personally. Do not inspect or export owner MFA secrets. Production QA uses synthetic temporary accounts and must remove them afterward.

## Installer builds

Build in isolated snapshots under artifacts, leaving product checkouts unchanged. `packaging/prepare-components.py` creates the component desktop workspace using compiled Flutter Web assets and self-contained Blazor runtime. Electron shell and builder configuration live under packaging. Native Linux builds produce AppImage; native Apple Silicon builds on MacBook produce DMG. macOS installers are unsigned and not notarized; labels and installation manual disclose this. No Intel Mac claim is made.

The report desktop snapshot uses `packaging/report-private-updates.cjs` so this distribution directs updates to the authenticated portal instead of the public update feed.

## Verification

`tests/integration.py` uses only the isolated local test database. It tests anonymous denial, CSRF, one-use and expired invites, mandatory MFA, TOTP replay, recovery consumption, roles, invitation outbox and blocked-session revocation. `tests/desktop-check.mjs` connects only to explicitly launched test applications with loopback DevTools ports.

## Rollback

Point `/opt/nextgensoftware/current` to the previous tested release and restart only `nextgensoftware`. Preserve the database, key directory and bucket objects. Validate Nginx before any reload. Hide a faulty installer in Administration rather than deleting versioned objects. Existing DME applications are separate.

## Documentation previews

All 78 documentation pages are public. Component manuals embed live Blazor examples from `component-preview.service` on 127.0.0.1:5340. Nginx serves the component demonstrations publicly; installer downloads still require an authenticated MFA session. All 20 report manuals embed topic-specific working examples: Office/image exports, import, preparation, parameters, drill-down, template diagnostics, library and integration scenarios. Examples use included synthetic fixtures and pre-generated outputs from the actual report engine; they do not execute arbitrary user templates on the public server. Preview data is synthetic. The reports' HTML-based authoring manual is sanitized as HTML rather than displayed as escaped source.

`python3 tests/check-content.py` verifies documentation links and the required absence of competitor names from public/member content. Distribution copies are sanitized by `packaging/sanitize-distribution.py`; original product repositories are not modified.

## VM cleanup on 2026-10-28

At the owner's explicit request, removed 454 old DME release directories and 206 staging directories older than 48 hours. Retained the active release, ten recent rollback releases and directories referenced by active processes. Freed 108.14 GiB. Manifest: `/var/log/dme-cleanup-20261028.json`. No database, working data or backup directories were removed; DME, DME.Landing and Nginx remained active.

The public component catalog provides 47 individual on-demand live previews and component search. Homepage 1.0.12 uses real product screenshots and on-demand live examples. Older SVG overview assets remain available; they can be regenerated with `python3 design/build-overviews.py`. The portal uses a navy/indigo/lavender visual palette.

Components are organized into eight categories in `server/ComponentCatalog.cs`, shared by the catalog and documentation navigation. The category/icon completeness check runs in `tests/check-content.py`. Catalog pictures are schematic SVG icons generated by `python3 design/build-component-icons.py`; live previews remain interactive. Product changes must ship matching previews and documentation as required by `AGENTS.md`.

Manual links are normalized by `packaging/doc_links.py` during documentation import: local Blazor examples point to the embedded public preview; Flutter links point to the corresponding implementation section; repository manual URLs point to public manual routes. `python3 tests/check-doc-links.py` validates all document routes and fragments; add `--live` to verify the published HTML and live preview destinations.

Code examples are rendered at import time by `packaging/code_blocks.py` using Pygments 2.19.2, with Razor markup/C# handling, language labels, line numbers, copy and wrap controls. JSON examples are indented; other code content is preserved. Run `python3 tests/check-code-blocks.py` to verify complete coverage, escaping, content preservation and idempotent regeneration. Website documentation changes require rebuilding the desktop installers to update bundled manuals. Current desktop documentation revisions are Components 2026.10.29.2 (grid1) and Reports 2026.10.29.1 (sdk1) on Linux, macOS and Windows. All 20 report topic examples and real downloadable outputs work offline.

## Desktop documentation release

`packaging/build-offline-docs.py --product components|reports --webroot <output>` renders all current manuals with local links, bundled styling/scripts/icons, code highlighting and local previews. `packaging/apply-offline-docs.py <output> <app server wwwroot>` applies the overlay and removes stale compressed copies of replaced files. Components preparation invokes this generator automatically. Report overlays must be applied to published desktop server resources before packaging. Validate with `tests/check-offline-docs.py` and `tests/offline-app-check.mjs <CDP port> <product>` on the native apps.

Documentation-only installer revision `docs2` retains application/library versions 0.70.0 and 0.2.1. The former four-package docs2 release used `deploy/releases-docs-20261028.json`. The current six installer records and SHA-256 values are in `deploy/releases-current.json`. Original bucket objects remain available for rollback; existing download UUIDs were retained. Native Linux AppImages and Apple Silicon DMGs were launched and tested, with all manual assets served locally. macOS packages remain without a Developer ID signature/notarization; ad-hoc integrity signatures were verified after repackaging.

Report topic assets are reproducible with `design/report-examples/build.py` against an isolated local Studio engine on port 5355 with TypeScript enabled. Static UI lives in `server/wwwroot/report-examples`; the offline overlay copies it unchanged. Run `tests/report-examples-browser.mjs <CDP port> <site-or-native-origin>` for all 20 scenarios and their downloads. Reports docs3 replacement manifest: `deploy/releases-reports-docs3.json`.


## Installed SDK release 2026.10.29.1 — website 1.0.9

The public/offline manuals now start from installation and connect the installed SDK. Components ships NextgenComponents.Blazor 0.70.0 as NuGet plus its Flutter package. Reports ships NextgenReports.Client and NextgenReports.Blazor 0.2.1 as NuGet, its Flutter/Dart package, Python tools and matching samples. Desktop report sessions stay private; integration uses a separate instance of the installed executable with explicit loopback binding and isolated state.

Build SDKs with `python3 packaging/build-installed-sdk.py`. It copies only required projects into staging and creates NuGet packages with their static web assets; product checkouts are not changed. Render manuals with `packaging/build-docs.py`, build both offline overlays, then apply `packaging/prepare-installed-app.py <components|reports> <copied native app resources>`. This replaces obsolete SDK source/manual copies and removes stale compressed documentation. Components' normal preparation also copies the generated SDK. For Reports, apply this overlay to the native unpacked app before repackaging. `packaging/build-installed-appimages.cjs` packages the staged Linux apps; macOS DMGs must be packaged and verified natively.

Run `tests/check-installed-workflow.py`, `tests/check-content.py`, `tests/check-code-blocks.py`, `tests/check-doc-links.py`, `tests/check-offline-docs.py`, and the native offline/topic browser checks. `tests/installed-sdk-consumer` is a clean .NET consumer: restore from the generated local NuGet feed and run with `NEXTGEN_REPORT_URL` pointing at an isolated installed engine. It must return an actual PDF. Validate a clean Blazor host and Flutter consumer as well. Production publication and the `--live` documentation check are required before calling this release published.

## Windows build on the iMac

See [Windows build and native QA](docs/windows-build.md). Host prerequisites are installed with `packaging/setup-windows-host.sh`; `packaging/build-windows.sh` creates both Windows x64 NSIS installers. The evaluation VM is dedicated to native installer verification.

Website 1.0.9 and all six sdk1 installers are published. Native Linux, macOS and Windows checks passed the 78 manuals and 20 Reports examples. The Windows client SDK rendered a 23,976-byte PDF. Production verified 4,340 documentation routes/fragments, 183 public pages/assets and authenticated MFA downloads of all six files with exact SHA-256 and Range support. The temporary QA account was removed. See `docs/verification.md` and `artifacts/evidence/sdk1/`.

Website 1.0.10 groups the five Grid guides directly after NgDataGrid in Data & documents. Public and offline navigation use the ordered topics in `server/ComponentCatalog.cs`. Components grid1 packages include matching offline navigation; Reports remains sdk1. To package the prepared Components resources use `NEXTGEN_ARTIFACT_REVISION=grid1` with the AppImage/Windows builders. Guarded release manifest: `deploy/releases-grid-20261029.json`.

## Homepage product showcases — 1.0.12

`server/HomeShowcase.cs` exposes all 47 components in eight catalog-driven categories and all 20 report examples in six categories. Each category has an item selector with matching screenshot, live demo and guide; returning to a category restores its last selection. The hero combines an actual Grid screenshot with a generated report page. Home-only CSS/JS is isolated in `home-showcase.css` and `home-showcase.js`; it is not part of desktop manuals. Only one live iframe can be active, and closing or switching removes it. `design/capture-home-previews.mjs` captures synthetic public examples through an explicitly launched test Chrome on port 9590. `tests/run-home-showcase.py <origin>` checks choices, live controls, removal, image loading and desktop/mobile overflow.


## Components 0.72.0 — website 1.0.14 (2026-10-30)

Released custom Grid field editors and single-cell editing on Blazor/Flutter Web with full-record validation, guarded draft callbacks and explicit Save/Cancel. Public previews/manuals and all three native installers are synchronized; offline revision 2026.10.30.1. See `deploy/release-cell072-verification.md` and `deploy/releases-cell072.json` for evidence and hashes. `/health` derives the site version from its assembly. Future authorized fixes/enhancements proceed through checks, scoped commit/push, synchronized release and production verification without a repeated publication approval request.


## Components 0.73.0 — website 1.0.15 (2026-10-30)

Grid batch editing for Blazor and Flutter Web: staged changes, review/undo, one persistence callback and retained queues on failure. Website previews and public/offline documentation released together with Linux, macOS and Windows installers. Native startup, all documentation links, production Chrome and MFA-authenticated downloads verified. See [release evidence](deploy/release-batch073-verification.md).
