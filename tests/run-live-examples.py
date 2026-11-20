#!/usr/bin/env python3
"""Run the required report-topic browser checks against the public release."""
from pathlib import Path
import subprocess,tempfile,time,urllib.request,json,shutil
root=Path(__file__).resolve().parents[1];node=str(root/'artifacts/toolchain/node-v24.22.2-linux-x64/bin/node');chrome=shutil.which('google-chrome') or shutil.which('google-chrome-stable');assert chrome
out=root/'artifacts/evidence/sdk1';out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='nextgen-live-browser-') as profile:
 process=subprocess.Popen([chrome,'--headless=new','--remote-debugging-port=9370','--user-data-dir='+profile,'--no-first-run','--no-default-browser-check','--window-size=1440,1000','https://softwarenextgen.com'],stdout=open(out/'live-browser.log','w'),stderr=subprocess.STDOUT)
 try:
  for _ in range(90):
   if process.poll() is not None:raise RuntimeError('Test browser exited')
   try:
    if json.load(urllib.request.urlopen('http://127.0.0.1:9370/json/list')):break
   except Exception:pass
   time.sleep(1)
  else:raise RuntimeError('Test browser did not start')
  subprocess.run([node,str(root/'tests/report-examples-browser.mjs'),'9370','https://softwarenextgen.com'],check=True)
  subprocess.run([node,str(root/'tests/capture-native.mjs'),'9370',str(out/'live-windows-installation.png')],check=True)
 finally:
  process.terminate()
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:process.kill();process.wait()
print('PASS all 20 public report topics and Windows installation controls')
