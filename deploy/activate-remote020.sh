set -euo pipefail
site=/opt/nextgensoftware/current
old=$(readlink -f "$site")
[[ "$old" == /opt/nextgensoftware/releases/1.0.17 ]]
[[ -f /opt/nextgensoftware/releases/1.0.18/Nextgen.Web.dll ]]
rollback(){ ln -sfn "$old" "${site}.remote-rollback"; mv -Tf "${site}.remote-rollback" "$site"; systemctl restart nextgensoftware; }
trap rollback ERR
ln -sfn /opt/nextgensoftware/releases/1.0.18 "${site}.remote020"
mv -Tf "${site}.remote020" "$site"
systemctl restart nextgensoftware
ready=false
for attempt in $(seq 1 25); do
 if curl -fsS http://127.0.0.1:5338/health | python3 -c 'import json,sys; assert json.load(sys.stdin)["version"]=="1.0.18"'; then ready=true; break; fi
 sleep 1
done
[[ "$ready" == true ]]
python3 /tmp/remote020-publish.py
trap - ERR
systemctl stop nextgensoftware-remote-stage
systemctl is-active nextgensoftware dme nextgen-relay nginx
readlink -f "$site"
