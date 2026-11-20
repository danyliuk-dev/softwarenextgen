# Components 0.72.0 / website 1.0.14 — 2026-10-30

Paired Blazor and Flutter Web custom field editors and single-cell editing. Existing single-record CRUD remains available. Full record drafts, required/cross-field validation, safe errors, retry, current permissions and stale callback rejection use the existing persistence contract. Batch editing and spreadsheet keyboard navigation remain deferred.

## Checks completed

- 1,071 Blazor checks; 302 Flutter tests; library/gallery analysis; both gallery builds.
- 49 paired compiled/analyzed manual examples and 94 highlighted examples.
- Visible local ordinary Chrome: Blazor invalid quantity, save failure with retained draft, successful retry and cancel; Flutter custom numeric cell save. Screenshots under `artifacts/evidence/cell072`.
- 79 public manuals, local links/fragments, categories/icons and forbidden-name checks. Public/live baseline link check passed before activation; it is not proof of the new production release.
- Linux and macOS native installer startup: each 59 manuals and 7,378 local links/assets. Linux uses AppImage extraction mode (FUSE 2 is absent) and the active Wayland session. macOS uses an isolated installation copied from the new DMG. Native desktop validation covers startup and served content; UI interaction was separately checked in local Chrome.
- All three runtime payloads have library 0.72.0 and 112 byte-identical offline overlay files, with stale `.gz`/`.br` overlay files removed. SDK contains only the 0.72.0 NuGet and matching Flutter package.
- Windows NSIS installed and native app started in the dedicated VM; 59 manuals and 7,378 links/assets passed. Installed manual index and SDK manifest confirm 0.72.0. The host guest-exec wrapper timed out during the long installation; the guest continued and its final PASS status and log were collected.

## Delivery

Released on 2026-10-30. Website: `/opt/nextgensoftware/releases/1.0.14`; component preview: `/opt/nextgen-component-preview/releases/0.72.0`. The three installer records retain their IDs and point to private bucket objects listed in `releases-cell072.json`; `releases-current.json` is updated. Previous files and release directories remain available for rollback. No schema migration.

Implementation commit: `28e76a6`. Final documentation checkpoint: `ac3b895f63a08156ebc82925ebd6aa6196e47d27`, confirmed on `origin/main`; working tree clean. Website workspace has no initialized Git repository; its release source and evidence remain here.

Production Chrome passed invalid quantity validation, retained draft on persistence failure and successful retry (quantity 12 to 28, one successful write). `production-grid.png` records the result. All 79 manuals, 4,463 links/fragments and 262 public pages/assets passed, including 47 previews and schematic icons across eight categories. Full MFA-authenticated downloads and Range requests passed for Linux, macOS and Windows; sizes and SHA-256 match the manifest. Temporary ordinary-user QA fixture removed; no emails sent.

An initial activation detected a hardcoded old `/health` version and rolled back correctly. The health endpoint now derives its version from the assembly; final activation passed with website 1.0.14. DME, landing and nginx remained active.

QA cleanup: isolated Linux/Mac/Windows test applications stopped; Windows QA ISO ejected and VM returned to shut-off state. Local preview servers remain available for review.
