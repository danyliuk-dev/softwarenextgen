from pathlib import Path
import os,subprocess,signal
root=Path(__file__).resolve().parents[1];out=root/'artifacts/evidence/variable074';out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ)
for line in subprocess.check_output(['systemctl','--user','show-environment'],text=True).splitlines():
 k,sep,v=line.partition('=')
 if sep and k in ['DISPLAY','XAUTHORITY','WAYLAND_DISPLAY','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS']:env[k]=v
env['NEXTGEN_COMPONENTS_USER_DATA']=str(out/'linux-profile')
app=root/'artifacts/variable074/installers/NextgenComponents-0.74.0-variable074-linux-x86_64.AppImage'
p=subprocess.Popen([str(app),'--appimage-extract-and-run','--ozone-platform=wayland'],env=env,stdout=open(out/'linux-app.log','w'),stderr=subprocess.STDOUT,start_new_session=True)
try:
 with (out/'linux-native.json').open('w') as log:subprocess.run([str(root/'artifacts/toolchain/node-v24.22.2-linux-x64/bin/node'),str(root/'tests/components-offline-http.mjs'),str(out/'linux-profile/engine.log')],check=True,stdout=log,stderr=subprocess.STDOUT)
 print((out/'linux-native.json').read_text())
finally:
 os.killpg(p.pid,signal.SIGTERM)
 try:p.wait(timeout=15)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
