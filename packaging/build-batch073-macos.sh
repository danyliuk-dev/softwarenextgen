#!/bin/bash
set -euo pipefail
export PATH=/opt/homebrew/bin:/usr/local/share/dotnet:$PATH
stage="$HOME/development/nextgen-batch073"
mkdir -p "$stage/mount-old" "$stage/image"
hdiutil attach "$HOME/development/nextgen-cell072/NextgenComponents-0.72.0-cell072-mac-arm64.dmg" -nobrowse -readonly -mountpoint "$stage/mount-old"
ditto "$stage/mount-old/NextgenComponents.app" "$stage/image/NextgenComponents.app"
hdiutil detach "$stage/mount-old"
app="$stage/image/NextgenComponents.app"
rm -rf "$app/Contents/Resources/server" "$app/Contents/Resources/SDK"
ditto "$stage/payload/server" "$app/Contents/Resources/server"
ditto "$stage/payload/SDK" "$app/Contents/Resources/SDK"
cp "$stage/payload/app.asar" "$app/Contents/Resources/app.asar"
chmod +x "$app/Contents/Resources/server/BlazorGallery"
/usr/libexec/PlistBuddy -c 'Set :CFBundleShortVersionString 0.73.0' "$app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Set :CFBundleVersion 0.73.0' "$app/Contents/Info.plist"
codesign --force --deep --sign - "$app"
codesign --verify --deep --strict "$app"
ln -s /Applications "$stage/image/Applications"
hdiutil create -volname NextgenComponents -srcfolder "$stage/image" -format UDZO -o "$stage/NextgenComponents-0.73.0-batch073-mac-arm64.dmg"
# Mount the resulting installer and copy into an isolated installation directory.
mkdir -p "$stage/mount-test" "$stage/installed"
hdiutil attach "$stage/NextgenComponents-0.73.0-batch073-mac-arm64.dmg" -nobrowse -readonly -mountpoint "$stage/mount-test"
ditto "$stage/mount-test/NextgenComponents.app" "$stage/installed/NextgenComponents.app"
hdiutil detach "$stage/mount-test"
export NEXTGEN_COMPONENTS_USER_DATA="$stage/qa-profile"
"$stage/installed/NextgenComponents.app/Contents/MacOS/NextgenComponents" > "$stage/native.log" 2>&1 &
app_pid=$!
trap 'kill "$app_pid" 2>/dev/null || true' EXIT
node "$stage/components-offline-http.mjs" "$NEXTGEN_COMPONENTS_USER_DATA/engine.log" | tee "$stage/native-check.log"
shasum -a 256 "$stage/NextgenComponents-0.73.0-batch073-mac-arm64.dmg"
