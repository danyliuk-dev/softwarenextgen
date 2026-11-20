# Components 0.71.0 / website 1.0.13 — 2026-10-29

Released grouped continuous remote Grid ranges for Blazor and Flutter Web. The future-work queue is saved in the Components repository at `docs/roadmap.md` and linked from its README.

Components source commit: `915b58f` (main). Website workspace has no initialized Git repository; website release source and evidence remain in this workspace.

## Delivery

- Website: `/opt/nextgensoftware/releases/1.0.13`.
- Component preview: `/opt/nextgen-component-preview/releases/0.71.0`.
- All three private installer rows retain their existing download IDs. Final files and SHA-256 values: `releases-grouped071.json`; current combined product manifest: `releases-current.json`.
- Documentation revision: `2026.10.29.3`. Public manuals/previews remain anonymous; installers require sign-in and MFA.
- No schema migration. Previous site/preview release directories and installer objects retained. DME, landing and nginx remained active.

## Verification

- 1,064 Blazor checks; 301 Flutter tests; 49 paired compiled/analyzed manual examples; 94 highlighted preview checks. Library/gallery analysis and builds pass.
- Linux AppImage, Apple Silicon DMG and Windows x64 NSIS were installed/launched natively. Each passed 59 offline manuals, 3,989 local links, six Grid navigation topics and grouped-range behavior.
- Production: 79 manuals and 4,462 links/fragments; 262 public pages/assets; 47 component previews/icons in eight categories. Forbidden published names absent.
- Visible ordinary Chrome passed the production grouped-range workflow and six documentation navigation topics. Local Chrome also covered Flutter.
- MFA-authenticated full downloads of all three installers matched SHA-256 and size; Range requests passed. Temporary ordinary-user account removed, no emails sent.
- Evidence: `artifacts/evidence/grouped071/` (native screenshots/logs, activation, production browser/navigation, links, public access and downloads).
- Windows QA scheduled task removed, test media ejected and VM returned to shut-off state.

## Resolved verification issues

The initial Windows QA media was stale because an existing QEMU-owned ISO could not be overwritten. A new ISO was created and its installer checksum verified before the successful native test. Initial desktop navigation could race startup; the harness now waits for the initial document. Production browser testing waits for Retry viewport reset before scrolling. A stale 0.70 NuGet package was removed from all final SDK bundles and the packaging helper now removes obsolete copies after a successful pack.

## Scope limits

Fixed-height rows, at most 100,000 visible slots/records and 512 requested slots. Loaded-window selection/export only. The reference server helper materializes data; a scalable database implementation and full remote export remain application work. Native desktop wrappers do not certify native Flutter controls or screen-reader behavior.
