import base64,hashlib,hmac,struct,time,uuid,subprocess,re,secrets,concurrent.futures
from pathlib import Path
import os,requests
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization,hashes
BASE='http://127.0.0.1:15339'
def sql(q):return subprocess.check_output(['psql','-h','/tmp/nextgen-license-sock','-p','55462','-d','nextgen_license_test','-Atc',q],text=True).strip()
def session():
 s=requests.Session();s.headers['X-Forwarded-Proto']='https';return s
def req(s,method,path,**kw):
 for c in s.cookies:c.secure=False
 return s.request(method,BASE+path,allow_redirects=False,timeout=20,**kw)
def get(s,path):return req(s,'GET',path)
def post(s,path,data):return req(s,'POST',path,data=data)
def csrf(r):return re.search("name='__RequestVerificationToken' value='([^']+)'",r.text)[1]
def form(s,path,data,source=None):return post(s,path,{'__RequestVerificationToken':csrf(get(s,source or path)),**data})
def seed(email,role):
 uid=str(uuid.uuid4());token=secrets.token_hex(32).upper();sql(f"INSERT INTO users(id,email,role,generation) VALUES('{uid}','{email}','{role}','{uuid.uuid4()}'); INSERT INTO invitations(id,user_id,token_hash,expires_at) VALUES('{uuid.uuid4()}','{uid}','{hashlib.sha256(token.encode()).hexdigest().upper()}',now()+interval '1 hour')");return uid,token
assert sql('SELECT current_database()')=='nextgen_license_test'
sql('TRUNCATE mail_outbox,invitations,audit,license_devices,licenses,customers,remote_update_devices,users CASCADE')
password='QA-only-'+secrets.token_hex(12)
admin,at=seed('qa-admin@example.invalid','admin');uid,ut=seed('qa-user@example.invalid','user');a=session();u=session();anon=session()
def accept(s,token):return form(s,'/accept',{'token':token,'password':password,'confirm':password})
assert accept(a,at).headers['Location']=='/enroll'
assert get(a,'/admin/licenses').status_code==302
r=get(a,'/enroll');key=re.search("id='setup-key'>([A-Z2-7]+)",r.text)[1];step=int(time.time())//30;d=hmac.new(base64.b32decode(key),struct.pack('>Q',step),hashlib.sha1).digest();o=d[-1]&15;code=str((struct.unpack('>I',d[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
assert post(a,'/enroll',{'__RequestVerificationToken':csrf(r),'code':code}).status_code==200
assert accept(u,ut).headers['Location']=='/products'
assert get(u,'/account').status_code==200
assert get(u,'/admin/licenses').status_code==302
assert post(a,'/admin/licenses/create',{}).status_code==400
r=form(a,'/admin/licenses/customer',dict(first='Test',last='Client',kind='organization',organization='Synthetic Ltd',email='registered@example.invalid'),'/admin/licenses');assert r.status_code==302,r.text
assert sql("SELECT count(*) FROM licenses l JOIN users u ON u.id=l.user_id WHERE u.email='registered@example.invalid'")=='0'
assert sql('SELECT count(*) FROM mail_outbox')=='0'
r=form(a,'/admin/licenses/create',dict(user=uid,product='remote',edition='Standard',seats='1',expires=''),'/admin/licenses');assert r.status_code==302,r.text
lid=sql(f"SELECT id FROM licenses WHERE user_id='{uid}'")
def device(name):
 key=ec.generate_private_key(ec.SECP256R1());pub=key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
 r=requests.post(BASE+'/api/licenses/device',headers={'X-Nextgen-Client':'1'},json={'product':'remote','name':name,'publicKey':base64.b64encode(pub).decode()});assert r.status_code==200,r.text
 return key,r.json()
k,d=device('Test Linux');headers={'Authorization':'Bearer '+d['token'],'X-Nextgen-Client':'1'}
r=requests.get(BASE+'/api/licenses/challenge',headers=headers);assert not r.json()['authorized']
assert requests.post(BASE+'/api/licenses/lease',headers=headers,json={'challenge':r.json()['challenge'],'signature':'AA=='}).status_code==401
r=form(u,'/licenses/activate',{'code':d['code'],'license':lid,'confirm':'yes'},'/licenses/activate?code='+d['code']);assert r.status_code==200,r.text
# Same code is single use; full license cannot accept a second key.
k2,d2=device('Second device')
r=form(u,'/licenses/activate',{'code':d2['code'],'license':lid,'confirm':'yes'},'/licenses/activate?code='+d2['code']);assert r.status_code==400 and 'Device limit' in r.text
ch=requests.get(BASE+'/api/licenses/challenge',headers=headers).json()['challenge'];sig=k.sign(('NextgenLicense/v1:'+ch).encode(),ec.ECDSA(hashes.SHA256()));proof={'challenge':ch,'signature':base64.b64encode(sig).decode()}
r=requests.post(BASE+'/api/licenses/lease',headers=headers,json=proof);assert r.status_code==200,r.text
license=r.json();payload=base64.b64decode(license['payload']);server=serialization.load_pem_private_key(Path(os.environ.get('NEXTGEN_TEST_SIGNING_KEY','/tmp/nextgen-licensing/test-key.pem')).read_bytes(),None);server.public_key().verify(base64.b64decode(license['signature']),payload,ec.ECDSA(hashes.SHA256()))
assert requests.post(BASE+'/api/licenses/lease',headers=headers,json=proof).status_code==401
ch=requests.get(BASE+'/api/licenses/challenge',headers=headers).json()['challenge'];bad=k2.sign(('NextgenLicense/v1:'+ch).encode(),ec.ECDSA(hashes.SHA256()));assert requests.post(BASE+'/api/licenses/lease',headers=headers,json={'challenge':ch,'signature':base64.b64encode(bad).decode()}).status_code==401
r=form(a,'/admin/licenses/change',dict(id=lid,status='suspended',seats='1',expires=''),'/admin/licenses');assert r.status_code==302
ch=requests.get(BASE+'/api/licenses/challenge',headers=headers).json()['challenge'];sig=k.sign(('NextgenLicense/v1:'+ch).encode(),ec.ECDSA(hashes.SHA256()));assert requests.post(BASE+'/api/licenses/lease',headers=headers,json={'challenge':ch,'signature':base64.b64encode(sig).decode()}).status_code==401
assert sql('SELECT count(*) FROM mail_outbox')=='0'
# Two simultaneous browser approvals must not exceed a one-device license.
form(a,'/admin/licenses/change',dict(id=lid,status='active',seats='1',expires=''),'/admin/licenses')
did=sql(f"SELECT id FROM license_devices WHERE license_id='{lid}'")
assert form(u,'/licenses/revoke',{'id':did},'/licenses').status_code==302
assert requests.get(BASE+'/api/licenses/access',headers=headers).status_code==401
k3,d3=device('Third device');activation_csrf=csrf(get(u,'/licenses'))
def activate(dev):
 ss=session();ss.cookies.update(u.cookies)
 return post(ss,'/licenses/activate',{'__RequestVerificationToken':activation_csrf,'code':dev['code'],'license':lid,'confirm':'yes'}).status_code
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: statuses=list(pool.map(activate,[d2,d3]))
assert sorted(statuses)==[200,400],statuses
assert sql(f"SELECT count(*) FROM license_devices WHERE license_id='{lid}' AND revoked_at IS NULL")=='1'
assert requests.post(BASE+'/api/licenses/device',headers={'X-Nextgen-Client':'1'},json={'product':'remote','name':'bad','publicKey':None}).status_code==400
print('PASS admin MFA; customer password activation; RBAC/CSRF; client registration without grants/mail; licensing; seat limit; signed device-bound lease; replay/wrong-key denial; suspension')

k,d=[(k2,d2),(k3,d3)][statuses.index(200)]
headers={'Authorization':'Bearer '+d['token']}
k2,d2=device('Seat reduction test')
room='a'*64
url=BASE+'/api/licenses/access?room='+room
assert requests.get(url,headers=headers).status_code==401
nonce=secrets.token_hex(16);stamp=int(time.time());sig=k.sign(f'NextgenRemote/v2/relay/{room}/{stamp}/{nonce}'.encode(),ec.ECDSA(hashes.SHA256()))
signed={**headers,'X-Nextgen-Proof':f"{stamp}.{nonce}."+base64.b64encode(sig).decode()}
assert requests.get(url,headers=signed).status_code==200
assert requests.get(url,headers=signed).status_code==401
def limits(seats,sessions):
 r=form(a,'/admin/licenses/change',dict(id=lid,status='active',seats=str(seats),sessions=str(sessions),expires=''),'/admin/licenses');assert r.status_code==302
limits(2,3)
assert form(u,'/licenses/activate',{'code':d2['code'],'license':lid,'confirm':'yes'},'/licenses/activate?code='+d2['code']).status_code==200
second={'Authorization':'Bearer '+d2['token']}
assert requests.get(BASE+'/api/licenses/access',headers=second).headers['X-Session-Limit']=='3'
limits(1,1)
assert requests.get(BASE+'/api/licenses/access',headers=second).status_code==401
assert requests.get(BASE+'/api/licenses/access',headers=headers).headers['X-Session-Limit']=='1'
limits(2,2)
assert requests.get(BASE+'/api/licenses/access',headers=second).status_code==200
print('PASS single-use room proof, changed device priority, restored eligibility and independent session limit')

def directory(key, device):
 nonce=secrets.token_hex(16);stamp=int(time.time())
 sig=key.sign(f'NextgenRemote/v2/computers/{stamp}/{nonce}'.encode(),ec.ECDSA(hashes.SHA256()))
 h={'Authorization':'Bearer '+device['token'],'X-Nextgen-Proof':f"{stamp}.{nonce}."+base64.b64encode(sig).decode()}
 r=requests.get(BASE+'/api/licenses/computers',headers=h)
 assert r.status_code==200,r.status_code
 assert requests.get(BASE+'/api/licenses/computers',headers=h).status_code==401
 return r.json()
assert directory(k,d)==[]
assert directory(k2,d2)==[{'name':sql("SELECT name FROM license_devices WHERE code='"+d['code']+"'"),'room':room}]
other,ot=seed('other-directory@example.invalid','user')
sql(f"UPDATE licenses SET user_id='{other}' WHERE id='{lid}'")
# A different customer's active license must not expose the first account's routes.
other_license=str(uuid.uuid4())
sql(f"INSERT INTO licenses(id,user_id,product,seats) VALUES('{other_license}','{uid}','remote',1)")
sql(f"UPDATE license_devices SET license_id='{other_license}' WHERE code='{d2['code']}'")
assert directory(k2,d2)==[]
print('PASS account-scoped directory, excludes self, refuses replay and isolates customers')
