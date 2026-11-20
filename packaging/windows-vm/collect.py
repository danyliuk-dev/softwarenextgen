#!/usr/bin/env python3
"""Collect only the named QA results from the dedicated Windows guest."""
from pathlib import Path
import base64,json,subprocess
root=Path(__file__).resolve().parents[2];dest=root/'artifacts/evidence/sdk1/windows-native';dest.mkdir(parents=True,exist_ok=True)
def call(name,args):
 return json.loads(subprocess.check_output(['virsh','-c','qemu:///system','qemu-agent-command','nextgen-win11',json.dumps({'execute':name,'arguments':args})],text=True))['return']
for name in ['status.txt','results.json','setup.log','failure.txt','components-offline.log','reports-offline.log','reports-topics.log','sdk-client.log','components.png','reports.png']:
 try:handle=call('guest-file-open',{'path':'C:\\NextgenQA\\'+name,'mode':'rb'})
 except subprocess.CalledProcessError:
  if name=='failure.txt':continue
  raise
 try:
  with (dest/name).open('wb') as f:
   while True:
    r=call('guest-file-read',{'handle':handle,'count':65536});f.write(base64.b64decode(r.get('buf-b64','')))
    if r.get('eof'):break
 finally:call('guest-file-close',{'handle':handle})
 print('Collected',name,(dest/name).stat().st_size,'bytes')
