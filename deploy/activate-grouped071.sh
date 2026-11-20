#!/usr/bin/env bash
# Coordinated component release. Run only after native installer checks pass.
set -euo pipefail
site=/opt/nextgensoftware/current
preview=/opt/nextgen-component-preview/current
old_site=$(readlink -f "$site")
old_preview=$(readlink -f "$preview")
[[ "$old_site" == /opt/nextgensoftware/releases/1.0.12 ]]
[[ "$old_preview" == /opt/nextgen-component-preview/releases/0.70.0 ]]
[[ -f /opt/nextgensoftware/releases/1.0.13/Nextgen.Web.dll ]]
[[ -f /opt/nextgen-component-preview/releases/0.71.0/BlazorGallery.dll ]]
rollback(){
 ln -sfn "$old_site" "${site}.rollback"; mv -Tf "${site}.rollback" "$site"
 ln -sfn "$old_preview" "${preview}.rollback"; mv -Tf "${preview}.rollback" "$preview"
 systemctl restart component-preview nextgensoftware
 echo 'Activation failed; previous site and preview restored' >&2
}
trap rollback ERR
ln -sfn /opt/nextgen-component-preview/releases/0.71.0 "${preview}.grouped071"
mv -Tf "${preview}.grouped071" "$preview"
ln -sfn /opt/nextgensoftware/releases/1.0.13 "${site}.grouped071"
mv -Tf "${site}.grouped071" "$site"
systemctl restart component-preview nextgensoftware
ready=false
for attempt in $(seq 1 30); do
 if curl -fsS http://127.0.0.1:5338/health | python3 -c 'import json,sys; assert json.load(sys.stdin)["version"]=="1.0.13"'; then ready=true; break; fi
 sleep 1
done
[[ "$ready" == true ]]
curl -fsS http://127.0.0.1:5340/preview/components/grouped-range > /dev/null
python3 /tmp/update-grouped071.py
trap - ERR
systemctl is-active component-preview nextgensoftware dme dme-landing nginx
readlink -f "$site"
readlink -f "$preview"
echo 'Activated website 1.0.13, Components preview 0.71.0 and three guarded installer records'
