#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$root/packaging/toolbin:$root/artifacts/toolchain/node-v24.22.2-linux-x64/bin:$PATH"
export WINEPREFIX="$root/artifacts/toolchain/wine-prefix"
export ELECTRON_BUILDER_CACHE="$root/artifacts/toolchain/builder-cache"
export npm_config_cache="$root/artifacts/toolchain/npm-cache"
command -v node >/dev/null
command -v wine >/dev/null || { echo "Install wine64 and wine32:i386 first" >&2; exit 1; }
export WINEARCH=win64
export USE_SYSTEM_WINE=true
unset ELECTRON_BUILDER_WINE_TOOLSET_DIR
cd "$root"
node packaging/build-windows.cjs "$@"
