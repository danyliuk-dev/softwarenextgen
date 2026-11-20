#!/usr/bin/env python3
"""Verify Grid navigation in an isolated browser against installed or public docs."""
from pathlib import Path
import subprocess,tempfile,time,urllib.request,json,argparse
p=argparse.ArgumentParser();p.add_argument('origin');p.add_argument('--offline',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1];node=str(root/'artifacts/toolchain/node-v24.22.2-linux-x64/bin/node');out=root/'artifacts/evidence/grid1';out.mkdir(exist_ok=True)
label='linux-installed' if a.offline else 'public'
with tempfile.TemporaryDirectory(prefix='nextgen-grid-browser-') as profile:
 process=subprocess.Popen(['/usr/bin/google-chrome','--headless=new','--remote-debugging-port=9577','--user-data-dir='+profile,'--no-first-run','--window-size=1440,1000',a.origin+('/workspace.html' if a.offline else '/docs/components/manual/grid-editing')],stdout=open(out/(label+'-browser.log'),'w'),stderr=subprocess.STDOUT)
 try:
  for _ in range(90):
   try:
    if any(t.get('url','').startswith(a.origin) for t in json.load(urllib.request.urlopen('http://127.0.0.1:9577/json/list',timeout=2))):break
   except Exception:pass
   time.sleep(1)
  if a.offline:subprocess.run([node,str(root/'tests/offline-app-check.mjs'),'9577','components','2026.10.29.2'],check=True)
  subprocess.run([node,str(root/'tests/grid-navigation-browser.mjs'),'9577']+([] if a.offline else [a.origin]),check=True)
  subprocess.run([node,str(root/'tests/capture-native.mjs'),'9577',str(out/(label+'.png'))],check=True)
 finally:
  process.terminate()
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:process.kill();process.wait()
