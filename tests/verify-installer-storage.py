import subprocess,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];rows=json.loads((root/'deploy/releases-docs-20261028.json').read_text());evidence=[]
for r in rows:
 local=root/'artifacts/desktop-docs2'/('macos' if r['platform'].startswith('macOS') else r['product']+'/installers')/r['filename']
 checksum=json.loads(subprocess.check_output(['gcloud','--configuration=dme-prod','storage','hash',str(local),'--format=json'],text=True))[0]['crc32c_hash']
 remote=json.loads(subprocess.check_output(['gcloud','--configuration=dme-prod','storage','objects','describe','gs://causal-armor-506513-a7-nextgensoftware-installers/'+r['storage_name'],'--format=json(size,crc32c_hash,generation)'],text=True))
 assert int(remote['size'])==r['size'] and remote['crc32c_hash']==checksum,r['filename']
 evidence.append({'filename':r['filename'],'sha256':r['sha256'],**remote})
 print('PASS cloud size/CRC32C:',r['filename'],flush=True)
(root/'artifacts/evidence/desktop-docs2-storage.json').write_text(json.dumps(evidence,indent=2))
