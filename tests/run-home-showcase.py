#!/usr/bin/env python3
"""Verify homepage categories, previews and live controls in an isolated browser."""
from pathlib import Path
import subprocess,tempfile,time,urllib.request,json,argparse
p=argparse.ArgumentParser();p.add_argument('origin');a=p.parse_args()
root=Path(__file__).resolve().parents[1];node=str(root/'artifacts/toolchain/node-v24.22.2-linux-x64/bin/node');out=root/'artifacts/evidence/home2';out.mkdir(exist_ok=True)
label='public' if a.origin.startswith('https') else 'local'
with tempfile.TemporaryDirectory(prefix='nextgen-home-browser-',ignore_cleanup_errors=True) as profile:
 process=subprocess.Popen(['/usr/bin/google-chrome','--headless=new','--remote-debugging-port=9577','--user-data-dir='+profile,'--no-first-run','--window-size=1440,1000',a.origin+'/'],stdout=open(out/(label+'-browser.log'),'w'),stderr=subprocess.STDOUT)
 try:
  for _ in range(90):
   try:
    if any(t.get('url','').startswith(a.origin) for t in json.load(urllib.request.urlopen('http://127.0.0.1:9577/json/list',timeout=2))):break
   except Exception:pass
   time.sleep(1)
  subprocess.run([node,str(root/'tests/home-showcase-browser.mjs'),'9577',a.origin,str(out)],check=True)
 finally:
  process.terminate()
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:process.kill();process.wait()
