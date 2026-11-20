#!/usr/bin/env python3
from pathlib import Path
import os,subprocess,time,json,urllib.request
root=Path(__file__).resolve().parents[1];node=str(root/'artifacts/toolchain/node-v24.22.2-linux-x64/bin/node');out=root/'artifacts/evidence/sdk1';out.mkdir(parents=True,exist_ok=True)
desktop_env={}
for line in subprocess.check_output(['systemctl','--user','show-environment'],text=True).splitlines():
 key,sep,value=line.partition('=')
 if sep and key in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY']:desktop_env[key]=value
for product,port,var in [('components',9367,'NEXTGEN_COMPONENTS_USER_DATA'),('reports',9368,'NEXTGEN_DESKTOP_USER_DATA')]:
 installer=next((root/'artifacts/installer-sdk1'/product/'installers').glob('*.AppImage'))
 app=subprocess.Popen([str(installer),'--appimage-extract-and-run','--remote-debugging-port='+str(port)],env=dict(os.environ,**desktop_env,**{var:str(out/('profile-'+product))}),stdout=open(out/(product+'-app.log'),'w'),stderr=subprocess.STDOUT)
 try:
  for _ in range(120):
   if app.poll() is not None:raise RuntimeError(product+' exited '+str(app.returncode))
   try:
    tabs=json.load(urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/json/list'))
    if any(t.get('type')=='page' and t.get('url','').startswith('http') for t in tabs):break
   except Exception:pass
   time.sleep(1)
  else:raise RuntimeError('App did not become ready')
  subprocess.run([node,str(root/'tests/offline-app-check.mjs'),str(port),product,'2026.10.29.1'],check=True)
  if product=='reports':
   tabs=json.load(urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/json/list'));url=next(t['url'] for t in tabs if t.get('type')=='page');origin='/'.join(url.split('/')[:3]);subprocess.run([node,str(root/'tests/report-examples-browser.mjs'),str(port),origin],check=True)
  subprocess.run([node,str(root/'tests/capture-native.mjs'),str(port),str(out/(product+'-linux.png'))],check=True)
 finally:
  subprocess.run([node,str(root/'tests/close-desktop.mjs'),str(port)],check=False)
  app.terminate()
  try:app.wait(timeout=15)
  except subprocess.TimeoutExpired:app.kill();app.wait()
print('PASS installed Linux AppImages: both SDKs, 78 offline manuals, 20 report topics')
