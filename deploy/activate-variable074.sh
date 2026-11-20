#!/usr/bin/env bash
# Coordinated component release. Run only after native installer checks pass.
set -euo pipefail
site=/opt/nextgensoftware/current
preview=/opt/nextgen-component-preview/current
old_site=$(readlink -f "$site")
old_preview=$(readlink -f "$preview")
[[ "$old_site" == /opt/nextgensoftware/releases/1.0.15 ]]
[[ "$old_preview" == /opt/nextgen-component-preview/releases/0.73.0 ]]
[[ -f /opt/nextgensoftware/releases/1.0.16/Nextgen.Web.dll ]]
[[ -f /opt/nextgen-component-preview/releases/0.74.0/BlazorGallery.dll ]]
rollback(){
 ln -sfn "$old_site" "${site}.rollback"; mv -Tf "${site}.rollback" "$site"
 ln -sfn "$old_preview" "${preview}.rollback"; mv -Tf "${preview}.rollback" "$preview"
 systemctl restart component-preview nextgensoftware
 echo 'Activation failed; previous site and preview restored' >&2
}
trap rollback ERR
ln -sfn /opt/nextgen-component-preview/releases/0.74.0 "${preview}.variable074"
mv -Tf "${preview}.variable074" "$preview"
ln -sfn /opt/nextgensoftware/releases/1.0.16 "${site}.variable074"
mv -Tf "${site}.variable074" "$site"
systemctl restart component-preview nextgensoftware
ready=false
for attempt in $(seq 1 30); do
 if curl -fsS http://127.0.0.1:5338/health | python3 -c 'import json,sys; assert json.load(sys.stdin)["version"]=="1.0.16"'; then ready=true; break; fi
 sleep 1
done
[[ "$ready" == true ]]
curl -fsS http://127.0.0.1:5340/preview/components/grouped-range > /dev/null
python3 /tmp/update-variable074.py
trap - ERR
systemctl is-active component-preview nextgensoftware dme dme-landing nginx
readlink -f "$site"
readlink -f "$preview"
echo 'Activated website 1.0.16, Components preview 0.74.0 and three guarded installer records'
