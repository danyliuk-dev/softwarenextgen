# Product website release contract

When adding or changing NextgenComponents or NextgenReportEngine, including their visual appearance, update the public website previews and documentation in the same release. This is an explicit user requirement.

- Every component needs an accurate category, a working live preview, a recognizable schematic SVG icon and a matching manual.
- Update report samples, preview pages and manuals when report features or appearance change. Every report guide must have a matching topic entry and working controls in `server/wwwroot/report-examples`; regenerate engine outputs with `design/report-examples/build.py` and verify all topics using `tests/report-examples-browser.mjs`.
- Update homepage overview artwork when it no longer represents the products.
- Maintain schematic catalog icons in `design/build-component-icons.py`; regenerate them for new components. Inspect live previews after product changes and run content/public-access checks before completing a release.
- Keep documentation and previews public, installers behind authentication; Nextgen Remote also requires an active license. MFA is mandatory for administrators, not customers (user-approved licensing policy, 2026-11-17), and the forbidden third-party product names absent from all published content.
- After documentation changes, run `python3 tests/check-doc-links.py` and its `--live` production check. Verify destination fragments as well as HTTP status; never publish links to local gallery ports or repository copies of manuals available on the site.
- Keep desktop/offline manuals synchronized when releasing product documentation updates. Build the offline overlay with `packaging/build-offline-docs.py`, apply it to both platforms, remove stale compressed copies, and validate local links and native installer behavior before publishing.
