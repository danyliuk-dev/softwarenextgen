# Desktop Studio for Linux, macOS and Windows

Nextgen Reports Desktop opens Studio in a dedicated application window with its
own local engine. It includes the same designer, Preview, Library, JSON/object
workflow, PDF/HTML/image/Office exports and local English documentation.
The published installers support Linux x64, macOS Apple Silicon and Windows x64. See [Installation](/docs/reports/installation) for download, checksum and platform steps.

## Install a release

Download from your signed-in product page on https://softwarenextgen.com. On Linux, open the executable AppImage; on macOS, copy the app from the DMG to Applications and open it there; on Windows, run Setup and use the installed Start-menu shortcut. All engine/runtime files are bundled.

## Software updates

Use **Help → Check for updates…** to go to the authenticated product portal. Download the new installer manually. Save projects and close the application before updating. Back up local data; keep the SDK version used by your own application pinned until you choose to upgrade it.

## Open the application

Open **Nextgen Reports** from its installed location.

Expected startup: a short **Starting the local report engine…** screen, followed
by Studio and a calculated sample report. Select Preview if Design is active. A second launch focuses the existing window
for the same user-data directory. The app chooses a free loopback port; it does
not take port 5274 or reuse the browser demo's engine or Library.

## First desktop report

1. Open **File → Open project…** (Ctrl+O on Linux) and choose a `.nrproject.json`
   file. The project is validated before replacing the workspace. Templates and
   raw JSON can also be opened through Studio's existing file controls.
2. Change a parameter or edit the design/data, then **Generate preview**.
3. Use **File → Save project as…** (Ctrl+Shift+S) for a native save dialog. This
   saves the portable template/data/parameter bundle, not just the PDF. The file
   must be at most 8 MB. Invalid draft JSON cannot be saved as a valid project.
4. Use **Export PDF**, **Export Office**, **Export images** or **Export HTML**.
   A native save dialog selects the destination. Cancel leaves the destination
   unchanged. Studio's **Save project** button also downloads a portable project.
5. To retain versions inside this app, use **Library → Save new copy / Save new
   version**. Close and reopen the desktop app; the Library project remains.
   A separate recovery draft also retains the current workspace between launches;
   see the recovery workflow below.
6. **Help → Developer guide & code examples** opens the English code guide in a
   separate application window. **User manual** and **Desktop guide** are available
   from the same menu. Local documentation works without an Internet connection.

## Recover your workspace

The desktop app checks for changes every three seconds while the workspace is
idle. A private recovery file stores the exact template/data editor text, filename
and applied parameter controls, including unfinished JSON and blank values.
Open Studio dialogs, active generation and exports pause capture; complete those
operations first. Unapplied modal edits, undo history, selection, zoom, navigation,
Library identity and generated preview pages are not included.

1. Edit the report, data or parameters. The disabled status line in **File** shows
   the last successful draft save time. **Save recovery draft now** saves immediately.
2. Close Studio normally, or reopen it after an unexpected interruption.
3. Choose **Restore draft** to resume, **Discard draft** to start with the sample,
   or **Quit** to leave the draft untouched. A restored workspace says **Recovered
   draft** and has no active preview or export snapshot.
4. Fix unfinished JSON if necessary, then **Generate preview**. Recovery never
   executes the restored report's scripts or refreshes external sources itself.
5. **File → Delete recovery draft…** removes only the recovery file after
   confirmation. The open workspace stays unchanged; a subsequent edit creates
   a new draft. Closing without new edits does not recreate a deleted draft.

**Closing:** File → Close Studio or the main window's close button asks for
confirmation, then attempts a final capture. If capture fails, **Keep working**
lets you save or fix the problem; **Close without latest draft** retains only the
last successful snapshot. Normal close stops the owned engine and auxiliary
windows. An unexpected termination can lose edits since the last successful
capture (normally up to three seconds when idle).

Opening a project or creating a new report asks before replacing the workspace
in desktop mode. The recovery file follows the current workspace; it is not a
multi-project history. Save a project file or Library version before switching.
The draft can contain the report's entire data and is not encrypted: it is a
current-user-only local file, not a substitute for backups. Maximum workspace
snapshot size is 16 MB. Oversized or failed writes retain the previous snapshot.
An unreadable recovery file is left untouched and automatic saving is paused;
back up/remove that file while Studio is closed, then restart.


## Where files live

Default application profile: `~/.config/NextgenReportsDesktop` on Linux,
`~/Library/Application Support/NextgenReportsDesktop` on macOS and
`%APPDATA%\NextgenReportsDesktop` on Windows. **Help → About**
shows the actual path. It contains:

| Location | Contents |
| --- | --- |
| reports/library.db | Desktop Library and project versions |
| reports/schedules.db | Schedule metadata; local desktop mode does not run an authenticated server UI |
| reports/keys | Data-protection keys, restricted to the current user |
| workspace-recovery.json | Last workspace draft, including template/data text and parameters; current-user read/write only |
| studio.log | Current startup/engine log, bounded to 2 MB and reset each launch |
| Other profile files | Electron's local browser state/cache |

Exports and portable projects go to the location you choose. Back up `reports` and `workspace-recovery.json`
while the application is closed. Deleting the application folder does not remove
its profile. Deleting the profile removes saved Library data; preserve a backup
or portable projects first.

Advanced hosts may choose an isolated profile with `NEXTGEN_DESKTOP_USER_DATA`.
The engine uses `NEXTGEN_STATE_DIRECTORY` internally for state/key storage.
Desktop startup overrides inherited server-account and Library/schedule file
settings so it cannot accidentally reuse a separate Studio server's identity
or database paths. It can use explicitly configured `NEXTGEN_DATA_SOURCES` and
`NEXTGEN_HTTP_SOURCES` catalogs; see [data sources](data-sources.md).

## Trusted report scripts

Scripts are disabled by default. To enable the existing TypeScript pipeline for
your trusted local templates, close the app and start it explicitly with:

```sh
# Linux: use your actual downloaded AppImage filename.
NEXTGEN_DESKTOP_SCRIPTS=1 ~/Applications/Nextgen-Reports.AppImage

# macOS: launch the installed executable directly after closing the app.
NEXTGEN_DESKTOP_SCRIPTS=1 "/Applications/Nextgen Reports.app/Contents/MacOS/Nextgen Reports"
```

On Windows, open PowerShell after closing the application, then run (adjust the path if you selected a custom installation folder):

```powershell
$env:NEXTGEN_DESKTOP_SCRIPTS = "1"
& "$env:LOCALAPPDATA\Programs\Nextgen Reports\Nextgen Reports.exe"
```

The compiler uses Electron's bundled Node runtime in a child process; no separate
Node installation is needed by the built app. **Help → About** shows whether
scripts were enabled. Script validation, limits and trust boundaries remain those
in the [event guide](report-logic-manual.md). This is not an offline mobile runtime
or an untrusted-report sandbox.

## Engine ownership and troubleshooting

Each desktop instance owns a fresh loopback server and a random, memory-only
capability. Only its Electron session adds that capability to requests. Opening
the displayed engine URL in an unrelated browser or sending an ordinary curl
request returns 403; use the desktop window. This is separate from the regular
Studio URL at 5274. Cross-origin navigation is not embedded; supported external
links ask before opening the default application.

| Symptom | What to do |
| --- | --- |
| Engine files are missing | Reinstall the verified platform package; do not move individual engine files |
| Sandbox startup failure | Check the Linux sandbox setup above; keep sandboxing enabled |
| Engine startup error | Read the path shown in the error dialog and studio.log |
| Unexpected engine exit | Close/reopen the app and restore the draft or a saved project/Library version |
| Cannot open/save a project | Check file permissions, valid project JSON and the 8 MB limit |
| Missing recent edits after restart | Check the File draft status; capture pauses during modal dialogs, generation and export |

Normal close stops the engine through its stdin lifetime pipe, with termination
fallbacks if it cannot stop. If the parent process dies, pipe EOF also requests
engine shutdown. The app never terminates unrelated Studio/demo processes.
Windows/macOS GUI verification, Developer ID/Authenticode signing, notarization, file associations and autonomous background scheduling remain separate release work.

Security setup follows the [Electron security guide](https://www.electronjs.org/docs/latest/tutorial/security/)
and [single-instance lifecycle API](https://www.electronjs.org/docs/latest/api/app).
