# Windows builds on the Linux iMac

This is a maintainer guide. Product users install the packaged applications; see [Installation](installing.md).

The build host also requires the .NET 10 SDK and the prepared product snapshots described below.

The Windows x64 distributions contain Electron, a self-contained .NET server, installed client SDKs and the same offline manuals as the public website. No .NET runtime installation is required on the customer's computer.

## Host setup and build

Run `packaging/setup-windows-host.sh` once to install Wine and virtualization prerequisites. It uses Ubuntu packages and asks for the local sudo password in Terminal. Never put passwords in scripts.

`packaging/windows-toolchain.lock.json` records Node, Electron and builder versions. Run `python3 packaging/prepare-windows-toolchain.py` to download and verify the pinned portable tools. The current workspace keeps the verified Node runtime and Windows Electron distribution in `artifacts/toolchain`. The isolated product snapshots and their builder dependencies are under `artifacts/components-source` and `artifacts/report-source`. `packaging/build-windows.sh` uses system Wine with a dedicated prefix under `artifacts/toolchain/wine-prefix`.

```bash
./packaging/build-windows.sh
```

For an installer-only retry after a completed payload build, use `./packaging/build-windows.sh reports --repack` (or `components`). This removes incomplete NSIS archive caches but does not republish application files.

Outputs are `artifacts/installer-sdk1/{components,reports}/windows/*-sdk1-win-x64.exe`. The script publishes self-contained win-x64 servers, applies offline manuals, copies SDKs and creates current-user NSIS installers. Authenticode signing is not configured. Native Flutter Windows application development, if added later, needs a Windows build toolchain; the current desktop packages embed the already-built web galleries.

## Native Windows QA

`packaging/windows-vm/nextgen-win11.xml` defines the dedicated `nextgen-win11` libvirt domain: 2 vCPU, 8 GiB RAM, an 80 GiB sparse disk, Secure Boot, TPM 2.0 and NAT. It does not pass through iMac disks. SPICE listens only on loopback. Windows uses the official Enterprise Evaluation image; this is a time-limited test installation, not a permanent Windows license.

`packaging/windows-vm/prepare.py --bootstrap` prepares unattended setup media without installers. After both builds finish, run it without that option to include installers and QA tests. The media and `artifacts/windows-vm/credentials.json` contain private test-account credentials; keep them private and eject the setup media after provisioning. Never publish these files with product artifacts.

The first-logon script installs the test tools, verifies the guest-tools bootstrapper against its pinned SHA-256 from the official Fedora HTTPS download (Windows retains driver-signature validation), installs both NSIS applications and runs the offline manual and report-example checks inside Windows. Results are stored in `C:\NextgenQA`. A bootstrap installation stops at `READY_FOR_INSTALLERS`; that is not a passing installer test. Final completion requires `PASS` and the native screenshots/results. GUI tests must run in the logged-on user's interactive session.

```bash
virsh -c qemu:///system start nextgen-win11
virt-manager --connect qemu:///system --show-domain-console nextgen-win11
virsh -c qemu:///system shutdown nextgen-win11
```

Do not wipe or recreate the disk after setup. Keep installer release metadata and hashes separate from private VM credentials. Publish only the six product installers after native QA and the public/private-access release checks pass.

The provisioned VM has completed the sdk1 native checks and is normally shut down when unused. Start it with `virsh -c qemu:///system start nextgen-win11` and open it in Virtual Machine Manager. Setup media and one-time autologon were removed; private local QA credentials are retained in `artifacts/windows-vm/credentials.json` (mode 0600). Do not rerun unattended installation against its existing disk. Native evidence is in `artifacts/evidence/sdk1/windows-native/`.


## QA autologon — 2026-10-31

At the owner's explicit request, the dedicated `nextgen-win11` VM retains automatic sign-in for its existing `NextgenQA` local test account. Private credentials remain in the protected QA configuration and are never published. Release QA uses a one-shot scheduled task in the logged-on console session; the task removes itself after completion. The persistent VM disk and existing test tools are preserved.
