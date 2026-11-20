> Withdrawn: final production scrolling verification found a concurrent initialization defect. Rolled back to 1.0.15/0.73.0 with owner approval; superseded by the 0.74.1 patch verification report.

# Components 0.74.0 / website 1.0.16 — 2026-10-31

Measured variable-height local and loaded server-page Grid rows on Blazor and Flutter Web, including multiline cells, group headers and inline editors. Height estimates, bounded cell construction, anchor correction, end reachability and viewport reset on record-order changes. Continuous remote range readers and trees retain fixed-height contracts; column virtualization remains a separate stage.

## Verified

- 1,104 Blazor checks; all 309 Flutter tests; 49 paired manual examples compile/analyze; both galleries build. Existing optional CupertinoIcons font warning remains.
- Ordinary local Chrome: Blazor variable heights, R10000, grouping/collapse, shrink, and inline quantity save 12 to 37. Flutter selected R00001, reached R10000 with Ctrl+End, resized and shrank to 12 while retaining selection. Details: `artifacts/evidence/variable074/browser-checks.json`.
- Source documentation: 79 manuals, 584 links/fragments; categories and all 47 schematic icons; 231 highlighted code blocks.
- All three runtime payloads contain library 0.74.0 and 112 byte-identical offline files, with stale compressed overlay copies removed. Matching NuGet and Flutter SDKs; new measured-row JavaScript is included in both runtime and NuGet package. Prohibited names absent from the compiled Flutter payloads.
- Linux AppImage installed through extraction mode and launched with the existing sandbox in the local Wayland session: 59 manuals, 7,380 links/assets, documentation revision 2026.10.31.1.
- macOS DMG built on the Apple Silicon MacBook, signature verified, mounted, copied into an isolated installation and launched natively: 59 manuals, 7,380 links/assets. Downloaded DMG SHA-256 matches the native build.
- Source implementation `9171c4591c02758a7ecf35765de5be306fd5db77` confirmed on `origin/main`.

- Windows NSIS installed and launched in the active NextgenQA console session: 59 manuals, 7,380 links/assets. Installation was slow but completed without retry. Persistent NextgenQA autologon was explicitly requested by the owner and remains enabled.

## Pending release gates

Production activation, public/live-link checks and authenticated MFA download verification. Website and preview archives are staged in new release directories, and new private objects are uploaded; active releases are not changed by staging.
