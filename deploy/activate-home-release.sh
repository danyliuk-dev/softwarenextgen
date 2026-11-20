#!/usr/bin/env bash
# Run as root on dmewebapp after homepage layout and interaction checks pass.
set -euo pipefail
current=/opt/nextgensoftware/current
previous=$(readlink -f "$current")
release=/opt/nextgensoftware/releases/1.0.12
[[ "$previous" == /opt/nextgensoftware/releases/1.0.11 ]]
[[ -f "$release/Nextgen.Web.dll" ]]
rollback() {
  ln -sfn "$previous" /opt/nextgensoftware/current.rollback
  mv -Tf /opt/nextgensoftware/current.rollback "$current"
  systemctl restart nextgensoftware
  echo 'Site activation failed; previous site restored' >&2
}
trap rollback ERR
ln -sfn "$release" /opt/nextgensoftware/current.sdk1
mv -Tf /opt/nextgensoftware/current.sdk1 "$current"
systemctl restart nextgensoftware
ready=false
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:5338/health | python3 -c 'import json,sys; assert json.load(sys.stdin)["version"]=="1.0.12"'; then ready=true; break; fi
  sleep 1
done
[[ "$ready" == true ]]
trap - ERR
systemctl is-active nextgensoftware dme dme-landing nginx
readlink -f "$current"
echo 'Activated homepage release 1.0.12'
