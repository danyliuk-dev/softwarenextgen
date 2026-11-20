#!/usr/bin/env bash
# Run as root on dmewebapp only after all six native installer checks pass.
set -euo pipefail
current=/opt/nextgensoftware/current
previous=$(readlink -f "$current")
release=/opt/nextgensoftware/releases/1.0.9
[[ "$previous" == /opt/nextgensoftware/releases/1.0.8 ]]
[[ -f "$release/Nextgen.Web.dll" && -f /tmp/nextgen-releases-sdk1.json ]]
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
  if curl -fsS http://127.0.0.1:5338/health | python3 -c 'import json,sys; assert json.load(sys.stdin)["version"]=="1.0.9"'; then ready=true; break; fi
  sleep 1
done
[[ "$ready" == true ]]
python3 /tmp/update-installed-sdk.py
trap - ERR
systemctl is-active nextgensoftware dme dme-landing nginx
readlink -f "$current"
echo 'Activated website 1.0.9 and six installer records'
