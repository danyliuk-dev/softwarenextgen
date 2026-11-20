# Permissions and troubleshooting

## Linux

GNOME and other Wayland desktops control screen-sharing consent. Select the intended screen in the system dialog. Saved consent can be invalidated by OS changes or monitor changes. A background service cannot bypass this permission.

## macOS

For sharing the Mac, allow the installed Nextgen Remote app in **System Settings → Privacy & Security → Screen & System Audio Recording**. Remote keyboard and mouse control also needs **Accessibility** permission. Restart sharing after changing permissions. A viewer does not need permission to capture its own screen.

If macOS selects an old app named “previous”, remove that duplicate app from searchable folders and keep backups as archives. Re-add the current app in Applications. Replacing an app with a differently signed build can invalidate earlier consent.

## Windows

Run the application in the signed-in user’s desktop session. A locked screen, the sign-in screen and elevated system dialogs may not be available through the normal desktop session. This release does not offer unattended access before sign-in.

## Connection problems

Confirm that the host is running, the connection link identifies the intended computer, and the key is current. Restarting sharing changes the session key. Host and viewer need outbound HTTPS access. Reconnecting does not automatically restore control after the host revoked it.

## Privacy

Only share your connection details with a trusted person. The relay forwards encrypted session traffic; the access key stays with the endpoints. Screen contents, clipboard text and transferred files may contain private information. The host remains responsible for granting and ending access. Screen capture consent cannot be granted by the relay server.
