# Report library and version history

**Library** in Studio's top bar stores complete projects on the current host:
template, parameters and the applied data snapshot. It complements **Save project**,
which downloads a portable file. Library content is not automatically synchronized
to another computer or committed to Git. All users of this local Studio instance
share its library; optional [server mode](server-operations.md) applies Viewer/Author/Admin roles and schedules.

## Save and reopen a report

1. Create/open a project and edit its template/data. Apply changed parameter
   definitions before saving. Generate preview to check actual data and layout.
2. Open **Library**, enter a name and optional version note, then **Save new copy**.
   A new report ID with version 1 appears in the list. Names need not be unique.
3. Close Library and edit the project. Return and choose **Save new version**.
   The linked report receives the next version. Earlier snapshots remain intact.
   Changing Name here renames the library entry; the template title is unchanged.
4. Enter part of a name and press **Find**. Select a report, choose a History
   version and click **Open version**. Confirm replacement of the editor.
   Studio validates and renders the snapshot before applying it; a failed open
   preserves the current project. Save/download any unsaved work before opening.
5. **Download project** exports the selected version as `.nrproject.json` without
   changing the editor. Open it on another Studio instance with **Open project**.

Library Save checks project structure, static template rules and parameter values.
It does **not** render, fetch sources or execute report scripts. A stored version
can therefore have data/layout problems that are discovered on Open/Generate.
Opening has the same behavior as opening a portable project, including trusted
scripts when enabled by the host. Missing source catalogs do not prevent offline
rendering of the saved data. External database credentials remain host-owned;
ordinary data and parameter values are part of every stored snapshot.

New report, successfully opened project/template or Load sample clears the library
link. Editing the currently linked template/data does not. Saving a downloaded
project into a library creates a new entry unless it was opened through Library.
The portable project format contains no library ID and remains version 1.

## Compare history and restore

History lists version number, UTC-backed local display time, version note, size
and the source version for restores. Open/download versions separately to inspect
their contents; there is no field-by-field diff yet.

Select an earlier version and choose **Restore as latest**. Confirm the action.
If version 3 was latest and you restore version 1, version 4 contains version 1's
project; versions 1–3 remain unchanged. The current library name is retained.
The editor remains unchanged until you explicitly **Open version** 4.
Restoration does not fetch data or run scripts.

Saving/restoring requires the expected latest version. If another session saves
first, the request returns a conflict and does not overwrite anything. Your
editor is retained. Download it or **Save new copy** to preserve that work, then
Find/reopen the latest version before editing that report again. Opening an old
version links to that old version: Save new version will conflict if newer history
exists. Use Restore as latest or Save new copy deliberately. There is no force-save.

## Storage, backup and limits

Default storage is `App_Data/library.db` under Studio's content root (normally
the configured content root for a standalone engine). For the installed desktop app, use the profile path in the [Desktop guide](desktop.md); integration instances use your chosen `NEXTGEN_STATE_DIRECTORY`.
`NEXTGEN_LIBRARY_FILE=/absolute/private/path/library.db` selects a different
**dedicated** SQLite library file. Do not point it at a source/application database.
The parent directory is created when Studio starts. The Studio process needs
read/write access; the path is never accepted from projects or exposed by the API.

Reports and versions are committed in one database transaction. Concurrent writers
check the version in that same transaction. A failed save/restore adds no partial
version. Stop Studio before copying the database for a consistent offline backup;
restore that file with Studio stopped. Keep a backup outside build/publish folders
before replacing a deployment. Library content is not encrypted by the application.
Use host filesystem permissions and backups appropriate to your stored data.

Limits: 8 MB/project, 1,000 reports, 200 versions/report, 1 GB of stored project
payloads (database overhead is additional). Find returns up to 100 reports, newest
first; narrow the name search to find older entries. Names: 1–120 characters;
notes: 0–500, without control characters. No delete/prune, folders, tags, automatic
save, migration from other report catalogs is provided. Server roles and schedules
are described in the server guide. At the per-report limit, Save new copy starts fresh history.
At the storage limit, use another dedicated library file and retain the old file.
Remote hosting requires the configured server mode and HTTPS; see the server guide.

## API

All routes are under `/api/library`. POST uses the existing same-origin checks.
Errors: 400 invalid input, 404 unknown report/version, 409 stale expected version,
503 storage unavailable/busy. Requests with a different Origin are rejected.

- `GET ?search=text`: up to 100 `{id,name,latestVersion,updatedAt}` entries.
- `GET /{id}`: latest `{report,version,project}`.
- `GET /{id}/versions`: history metadata, newest first.
- `GET /{id}/versions/{version}`: selected `{report,version,project}`.
- `GET /{id}/versions/{version}/download`: portable JSON project download.
- `POST` with `{id:null,expectedVersion:0,name,note,project}` creates an entry;
  supply an existing ID and its opened version to append a version.
- `POST /{id}/restore` with `{version,expectedVersion}` appends a restoration.

Version metadata is `{version,savedAt,note,restoredFrom,bytes}`. Report IDs are opaque
32-character GUIDs. Times are ISO UTC timestamps. POST success returns the saved
`{report,version,project}`. Do not retry a write blindly after a lost response:
inspect latest/history first, because it may have committed.

Verified locally on Linux iMac. macOS and Windows remain unverified.
