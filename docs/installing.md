# Installation and first launch

Download the package for your product and platform from your signed-in product page at https://softwarenextgen.com. Downloads require MFA; manuals and previews are public. Compare the downloaded file's SHA-256 with the value on the product page.

## Linux x64

Keep the AppImage in a permanent folder, for example `~/Applications`. Mark the downloaded file executable using its actual filename, then open it:

```bash
chmod +x ~/Applications/PRODUCT.AppImage
~/Applications/PRODUCT.AppImage
```

If FUSE is unavailable, append `--appimage-extract-and-run`. The application includes its runtime; .NET, Node.js and Flutter development tools are not required to use it.

## macOS Apple Silicon

Open the DMG, drag the application into `/Applications` or `~/Applications`, eject the disk image and open the installed application. These packages target Apple Silicon. They are not Developer ID signed or notarized. If macOS blocks the application, verify its origin/checksum and approve this application in System Settings → Privacy & Security. Keep Gatekeeper enabled.

## Windows x64

Run the downloaded `.exe` installer. Choose the installation folder and complete Setup, then open **NextgenComponents** or **Nextgen Reports** from the Start menu or desktop shortcut. Installation is for the current user. The engine and its runtime are included; no .NET SDK, Node.js or Flutter installation is needed to use the app. The current installers are not Authenticode signed; check their source and published SHA-256 before running them.

To find the installed resources, open the application's shortcut properties and choose **Open file location**, then open `resources`. The usual locations are `%LOCALAPPDATA%\Programs\NextgenComponents\resources` and `%LOCALAPPDATA%\Programs\Nextgen Reports\resources`; use the directory you selected during Setup. Copy `SDK` from there into your application as described below. Keep projects and profile data when uninstalling if you plan to reinstall.

## NextgenComponents

Open **NextgenComponents**. In **Workspace**, choose **Blazor gallery**, **Flutter gallery** or **Documentation**. The local server starts automatically and closes with the application. The galleries work without building anything. Use the Getting started guide to connect the installed SDK to your own application.

## NextgenReportEngine

Open **Nextgen Reports**. The application starts its own engine and opens Studio. Open a project or edit the sample, generate Preview and export. Use **Help → User manual**, **Developer guide & code examples** or **Desktop guide** for offline documentation. The SDK is for integrating your own application; normal report authoring needs no development tools.

## Locate the installed SDK

Both products include `SDK/NuGet` and `SDK/Flutter` in their resources directory. Copy the SDK to a stable location owned by your application, such as `vendor/nextgen-sdk`, before connecting it. Keep it pinned to the installed product version when updating.

On macOS, resources are under `/Applications/NextgenComponents.app/Contents/Resources` or `/Applications/Nextgen Reports.app/Contents/Resources`. Adjust the prefix if installed in `~/Applications`.

On Linux, extract a copy of your downloaded AppImage into a separate empty folder to obtain stable SDK and engine paths (the temporary running mount is not a stable dependency path):

```bash
mkdir -p ~/NextgenInstalled/product
cd ~/NextgenInstalled/product
~/Applications/PRODUCT.AppImage --appimage-extract
```

Resources are now in `~/NextgenInstalled/product/squashfs-root/resources`. Use different folders for Components and Reports. Extraction uses the installed distribution and does not compile the product. The original AppImage remains the normal desktop launcher. In the integration guides, `NEXTGEN_RESOURCES` means the absolute resources directory for that product.

## Updates

Download the new package from your signed-in product page. Close the application before replacing it and back up report projects. Refresh the copied SDK only when deliberately upgrading your application's dependency. This distribution uses authenticated manual downloads, not a public automatic-update feed.
