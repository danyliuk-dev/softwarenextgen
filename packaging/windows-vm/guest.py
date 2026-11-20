#!/usr/bin/env python3
"""Run a reviewed PowerShell file via the dedicated VM guest agent."""
import argparse,base64,json,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('script',type=Path);a=p.parse_args()
def call(command,args=None):
 payload={'execute':command}
 if args is not None:payload['arguments']=args
 return json.loads(subprocess.check_output(['virsh','-c','qemu:///system','qemu-agent-command','nextgen-win11',json.dumps(payload)],text=True))['return']
encoded=base64.b64encode(a.script.read_text().encode('utf-16le')).decode()
r=call('guest-exec',{'path':'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe','arg':['-NoProfile','-NonInteractive','-EncodedCommand',encoded],'capture-output':True})
for _ in range(180):
 status=call('guest-exec-status',{'pid':r['pid']})
 if status.get('exited'):
  for key in ['out-data','err-data']:
   if key in status:print(base64.b64decode(status[key]).decode('utf-8',errors='replace'))
  raise SystemExit(status.get('exitcode',1))
 time.sleep(1)
raise SystemExit('Guest command timed out; inspect before retrying')
