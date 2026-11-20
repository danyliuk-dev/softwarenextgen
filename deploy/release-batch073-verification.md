# Components 0.73.0 / website 1.0.15 — 2026-10-30

Paired Blazor and Flutter Web batch editing: bounded staging, full-record review, per-entry undo, discard, one immutable persistence call, safe failures and retry. Repeated edits consolidate; delete replaces update. Current validation/permissions and local row existence are rechecked. Remote off-page UI checks use original queued records; backend atomicity, authorization, concurrency and idempotency remain application responsibilities.

## Checks

- 1,100 Blazor checks. Full Flutter suite passed 303 tests; added remote batch test also passed (304 tests total). Both paired batch scenarios passed together.
- 49 paired manual examples compile/analyze; 94 highlighted examples checked. Both galleries built.
- Visible Chrome: Blazor staged quantities 31 and 42, retained both after failure without mutating the originals, then applied both with one successful write. Flutter staged quantity 35 and applied it with one successful write. Evidence: `artifacts/evidence/batch073`.
- Source links/fragments: 79 manuals, 583 links. Public content/categories/icons and 231 code blocks pass.
- All three runtime payloads contain library 0.73.0 and 112 byte-identical offline files, without stale compressed overlay copies. Matching .NET and Flutter SDKs; no obsolete NuGet package.
- Linux AppImage launched using extraction mode in the current Wayland session; 59 offline manuals and 7,379 links/assets passed, documentation revision 2026.10.30.2. No sandbox disabled.
- macOS DMG mounted, application copied into an isolated installation, ad-hoc signature verified, native app started: 59 manuals and 7,379 links/assets passed. Downloaded artifact SHA-256 matches the MacBook build.
- Windows NSIS installed in the dedicated VM and native app started: 59 manuals and 7,379 links/assets passed. Installed runtime and SDK both confirm 0.73.0. The guest-exec wrapper timed out while the installer continued; its final PASS was collected without restarting installation.
- Production Chrome staged quantities 32/43, retained both after simulated failure (original values 12/24), then applied both in one successful write. Screenshot `production-grid.png`.
- Live production links/fragments: 79 manuals, 4,464 links; 262 public pages/assets, 47 live previews and icons, 8 categories. Full MFA downloads and Range checks passed for all three installers; exact size/SHA-256 matched. Temporary QA user removed; no email sent.

## Delivery

Implementation `01435364f9d6d4740cd8dca65407a15c5959d4e9` pushed and confirmed on origin/main. Website workspace has no initialized Git repository. Website `/opt/nextgensoftware/releases/1.0.15` and preview `/opt/nextgen-component-preview/releases/0.73.0` activated. Three installer records updated atomically with guards against old storage paths/checksums; previous releases and objects retained for rollback. `releases-current.json` synchronized. No schema migration.

QA cleanup: batch073 native applications stopped; Windows ISO ejected and VM shut off. DME, landing and nginx remained active. Windows packaging was interrupted once before producing EXE and succeeded on a fresh isolated repack. Native validation covers installation, startup and served content; browser UI proof uses ordinary visible Chrome.

Final documentation checkpoint: `ffce057c69d7090c40b8a7686db5bed5db285ff5`, confirmed on `origin/main`; Components working tree clean.
