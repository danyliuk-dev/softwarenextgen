import sys,json,secrets,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp/nextgen-licensing/python')
import websocket
v=json.loads((Path.home()/'.local/share/nextgen-remote/updates/licensing/device.json').read_text());key=secrets.token_hex(32);room=hashlib.sha256(key.encode()).hexdigest();base='wss://connect.softwarenextgen.com'
def connect(path,token=None):
 h=['x-nextgen-host-key: '+key,'User-Agent: NextgenRemote/0.4.0']
 if token:h.append('x-nextgen-license: '+token)
 return websocket.create_connection(base+path,header=h,suppress_origin=True,timeout=20)
try:connect('/relay/host/'+room,'0'*64);raise AssertionError('Unlicensed host accepted')
except websocket.WebSocketBadStatusException as e:assert e.status_code==403,e.status_code
registration=connect('/relay/host/'+room,v['token']);viewer=connect('/relay/join/'+room);ticket=registration.recv();host=connect('/relay/tunnel/'+ticket,v['token']);host.send_binary(b'licensing-qa-synthetic-payload');assert viewer.recv()==b'licensing-qa-synthetic-payload'
registration.close()
try:assert viewer.recv() in ('',None)
except websocket.WebSocketConnectionClosedException:pass
viewer.close();host.close()
print('PASS production relay: unlicensed registration denied; licensed synthetic tunnel relays unchanged bytes; host closure closes active viewer tunnel')
