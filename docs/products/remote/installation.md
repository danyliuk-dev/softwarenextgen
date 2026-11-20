# Install Nextgen Remote

Sign in to the [product downloads](/products/remote#downloads) with your account and an active Nextgen Remote license. Choose the package for your system. Compare its SHA-256 with the checksum shown on the download card.

## Linux x64

Extract the tar.gz archive into a permanent folder and run `nextgen-remote` from your desktop session. Keep the included files together. This package requires a compatible Linux system with Qt 6 and its Quick Controls, Dialogs and platform plugins. Wayland sharing also requires a working desktop portal, PipeWire and GStreamer. It is not a fully self-contained AppImage. Ask your administrator to install missing runtime packages if the application does not start.

## macOS Apple Silicon

Extract the ZIP and move `Nextgen Remote.app` to your Applications folder. The current development build is signed with an Apple Development identity, not a notarized Developer ID distribution signature. macOS may require approval to open it. Review the publisher and use the system’s normal approval flow; do not disable macOS security protections. Intel Macs are not included in this release.

## Windows x64

Extract the ZIP into a permanent folder and run `nextgen-remote.exe`. Keep all DLLs, plugins and the QML folder beside the executable. This is a portable package, not an MSI installer. Windows may show a publisher warning for the unsigned executable. Follow your organization’s policy before running it.

## Updating

Versions 0.3.0 and later check SoftwareNextgen when the application starts and automatically install newer verified packages when no remote connection is active. The application restarts with the same host/viewer arguments and keeps your settings.

Starting with 0.4.0, activate each computer once under **Help → License → Activate license**. Sign in with the account registered by your administrator, compare the activation code, select your assigned Nextgen Remote license, and approve. Customer accounts do not require an authenticator; administrator accounts still require MFA. Codes expire after ten minutes. Never approve a code you did not request.

The license controls desktop sharing, native viewer connections and access to updates. A valid signed permission is cached for up to seven days, bounded by the license expiry. The app refreshes it online at startup and hourly. The central relay checks active host licensing on registration and periodically during the session. Deactivation or suspension closes server access on the next check; a previously issued offline permission can remain valid until its expiry. Local expiry checks run every 30 seconds.

Manage activations at [My licenses](https://softwarenextgen.com/licenses). Deactivate an unused computer before activating another when your device limit is reached. For renewal or suspension questions, contact your administrator. A computer reinstall may require a new activation.

License verification remains enabled when automatic updates are disabled. Synthetic demo mode does not capture your desktop; it is not a licensed remote-work session. Earlier releases do not implement runtime licensing and cannot be retroactively made tamper-proof; the production relay enforces server access independently.

The updater checks a publisher-signed manifest and the package checksum. It keeps a rollback copy and restores the previous version if the new window cannot start. A failed version is not retried automatically. Updates need outbound HTTPS and write access to the installed application folder. Linux system dependencies still need to be installed by your administrator.

To disable automatic installation, clear **Install updates automatically at startup** in Help → Updates. Manual checking and installation remain available. Logs are in the `nextgen-remote/updates` directory under the OS user's application-data folder.

Older 0.2.0 installations need one manual replacement with a current package to obtain this update system.

Continue with [Start a remote session](/docs/remote/getting-started).

## Device keys and connection limits in 0.4.2

Unlock the login keyring on Linux, login Keychain on macOS, or sign in to the Windows account that owns the activation. On first use, Remote moves its existing device key into the operating system's credential store and verifies the saved key before deleting the old file. A locked or unavailable store must be unlocked before connecting.

The installation limit keeps the earliest approved devices eligible. Raising it restores eligible devices. A separate concurrent session limit counts viewer tunnels across all hosts of the license on the central relay. Lowering it closes excess sessions at their next check (within one minute under normal network conditions). Offline permissions retain their signed expiration date.
