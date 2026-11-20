# Components 0.74.1 / website 1.0.17 — 2026-10-31

The 0.74 measured-row feature remains scoped to local collections and loaded server pages. The first 0.74.0 production browser check exposed concurrent Server interop initialization: multiple scroll controllers could overwrite each other's spacers, leaving an empty viewport despite rows existing in the DOM. The owner approved rollback to website 1.0.15, preview 0.73.0 and the previous three Downloads. The first-release temporary MFA QA fixture was removed.

The patch shares one asynchronous initialization task and makes JavaScript controller creation idempotent per top spacer. Disposal awaits and cleans up the same controller. New delayed-interop and duplicate-create regression tests pass; 1,107 Blazor checks pass. Flutter implementation is unchanged from its 309 passing tests. Public/offline versions are 0.74.1 and documentation revision 2026.10.31.2.

Source patch `6f6dd49ad37f45aefc6c8ddfae11aa53babea82c` is confirmed on origin/main. The isolated browser run delayed the JavaScript module by 10 seconds while parent renders occurred: Ctrl+End showed row 10000 intersecting the viewport, 8 visible rows, zero bottom gap, top spacer 479424px and bottom spacer 0px.

Linux AppImage and macOS DMG native installation/startup passed with revision 2026.10.31.2, 59 manuals and 7,380 links per platform. All three payloads contain the 0.74.1 library and matching SDK, 112 identical offline files, and no stale compressed overlay copies. Windows NSIS installation/startup passed with the same 59 manuals and 7,380 links; installed library/SDK 0.74.1 and installer SHA-256 match. The one-time scheduled task was removed; owner-requested persistent autologon remains enabled. Test ISO was ejected and VM shutdown requested.

Production activated website 1.0.17, Components preview 0.74.1, and three guarded installer records. Final Chrome verified row 10000 actually visible (8 intersecting rows, zero bottom gap, spacers 479424px/0px), after search changes and a parent rerender. Public checks passed: 79 manuals, 4,465 links/fragments, 262 pages/assets, 47 live previews/icons across 8 categories. All three MFA downloads and Range requests matched complete file sizes and SHA-256; the temporary ordinary-user fixture was removed without mail. Previous 1.0.15/0.73.0 artifacts remain available for rollback.

Production editing saved quantity 12 → 41 with one successful write; the final measured record stayed reachable afterward. Windows VM is confirmed shut off. Release evidence commit: `b200ce5`.
