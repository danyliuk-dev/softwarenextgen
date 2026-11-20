# Start a remote session

Before starting, activate your assigned license using **Help → License → Activate license**. See [installation and activation](/docs/remote/installation).

## On the computer you want to share

Open Nextgen Remote and select **Share desktop**. Allow the operating system to share the screen when asked. Share the displayed access key only with the person you trust.

For an independent host, open **File → Connection settings** and set **Relay server** to `https://connect.softwarenextgen.com` before starting sharing. The host displays its connection link after registration. Send that link and the access key privately to the viewer.

## On the viewing device

In version 0.4.3, choose **Connect → My computers** to select another computer registered through the central relay under your account. The list remembers the last registered route. Sharing must be running on the selected host. Enter its current access key to connect.

For a manually supplied address, open **Connect**, enter your name and the host’s access key, then select **Connect**. If the host supplied a computer-specific connection link, enter it under **File → Connection settings → Connection server** first. The default server address is configured for the existing shared host.

You can also open the host’s connection link in a browser. The [browser viewer](https://connect.softwarenextgen.com) is available without installing the desktop client.

## View or control

New participants begin as viewers. Select **Request control** if you need keyboard or mouse access. The host selects the participant and grants permission. Only one participant controls the host at a time. The host can revoke control or stop sharing.

## Files and clipboard

After the host grants control, open **Files**. Select the destination folder on the host and choose **Upload file** or **Upload folder**. To copy an item from the host, select it and choose **Download file** or **Download folder**, then choose a local destination. The desktop app shows the folder buttons when both computers support resumable transfers (0.4.4 or later).

A folder transfer includes empty folders. Choose a destination where the folder name is available. The recipient sees the complete folder after the transfer finishes. If the connection drops, reconnect and request control again within ten minutes to resume. Choose **Cancel** to discard a partial transfer. Each transfer supports up to 50,000 entries and 64 GiB total, with an 8 GiB limit per file.

Use the clipboard controls to exchange text during an authorized control session.

## End the session

Disconnect when finished. On the host, use **Stop sharing** or quit the application to end access. Closing the window can leave the application running in the tray; it is not the same as quitting.

See [Permissions and troubleshooting](/docs/remote/permissions).
