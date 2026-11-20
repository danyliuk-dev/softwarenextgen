#!/usr/bin/env python3
"""Validate new installer streams using a temporary ordinary-user QA fixture."""
import base64,hashlib,hmac,struct,time,uuid,secrets,subprocess,os,re,json
from pathlib import Path
import requests
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
def sql(q):return subprocess.check_output(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database'],'-Atc',q],env=env,text=True).strip()
email='qa-remote-updates-20261117@example.invalid';uid=str(uuid.uuid4());token=secrets.token_hex(32).upper();password='QA-'+secrets.token_hex(24)
assert sql("SELECT count(*) FROM users WHERE email='"+email+"'")=='0'
sql(f"INSERT INTO users(id,email,role,generation) VALUES('{uid}','{email}','user','{uuid.uuid4()}'); INSERT INTO invitations(id,user_id,token_hash,expires_at) VALUES('{uuid.uuid4()}','{uid}','{hashlib.sha256(token.encode()).hexdigest().upper()}',now()+interval '15 minutes')")
s=requests.Session();s.headers['X-Forwarded-Proto']='https';base='http://127.0.0.1:15338'
def request(method,path,**kwargs):
 for c in s.cookies:c.secure=False
 return s.request(method,base+path,allow_redirects=False,timeout=180,**kwargs)
def csrf(r):return re.search("name='__RequestVerificationToken' value='([^']+)'",r.text)[1]
success=False
try:
 assert request('GET','/health').json()['version']=='1.0.19'
 devices={}
 for name in ['linux','macos','windows','revoke-test']:
  r=request('POST','/api/remote-updates/device',headers={'X-Nextgen-Client':'1'},json={'name':'Nextgen Remote update QA '+name});assert r.status_code==200,r.text
  devices[name]=r.json()
 first=devices['linux'];activation='/updates/remote/activate?code='+first['code']
 r=request('GET',activation);assert r.status_code==302 and r.headers['Location']=='/login'
 r=request('GET','/accept');assert request('POST','/accept',data={'__RequestVerificationToken':csrf(r),'token':token,'password':password,'confirm':password}).status_code==302
 r=request('GET','/enroll');key=re.search("id='setup-key'>([A-Z2-7]+)",r.text)[1];digest=hmac.new(base64.b32decode(key),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=digest[-1]&15;code=str((struct.unpack('>I',digest[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
 r=request('POST','/enroll',data={'__RequestVerificationToken':csrf(r),'code':code});assert r.status_code==200 and first['code'] in r.text,'MFA return link missing'
 old=json.loads(Path('/tmp/releases-remote020.json').read_text())[0]
 package='/api/remote-updates/package/'+old['sha256'].lower()+'/'+old['filename']
 assert request('GET',package).status_code==401
 for name,device in devices.items():
  bearer={'Authorization':'Bearer '+device['token']}
  assert request('GET','/api/remote-updates/device',headers=bearer).json()['authorized'] is False
  assert request('GET',package,headers=bearer).status_code==401
  path='/updates/remote/activate?code='+device['code']
  page=request('GET',path);assert page.status_code==200
  assert request('POST','/updates/remote/activate',data={'code':device['code'],'confirm':'yes'}).status_code==400
  assert request('POST','/updates/remote/activate',data={'__RequestVerificationToken':csrf(page),'code':device['code'],'confirm':'yes'}).status_code==200
  assert request('GET','/api/remote-updates/device',headers=bearer).json()['authorized'] is True
  r=request('GET',package,headers={**bearer,'Range':'bytes=0-31'});assert r.status_code==206 and len(r.content)==32
  assert request('GET',path).status_code!=200 or 'already used' in request('GET',path).text
  print('PASS MFA approval, CSRF, single use, authenticated Range:',name,flush=True)
 revoked=devices.pop('revoke-test');rid=sql("SELECT id FROM remote_update_devices WHERE token_hash='"+hashlib.sha256(revoked['token'].encode()).hexdigest().upper()+"'")
 page=request('GET','/updates/remote/devices')
 assert request('POST','/updates/remote/revoke',data={'__RequestVerificationToken':csrf(page),'id':rid}).status_code==302
 assert request('GET',package,headers={'Authorization':'Bearer '+revoked['token']}).status_code==401
 sql("UPDATE users SET enabled=false WHERE id='"+uid+"'")
 assert request('GET',package,headers={'Authorization':'Bearer '+first['token']}).status_code==401
 sql("UPDATE users SET enabled=true WHERE id='"+uid+"'")
 output=Path('/tmp/nextgen-update-qa-devices.json');output.write_text(json.dumps({'user_id':uid,'email':email,'devices':devices}));output.chmod(0o600);os.chown(output,Path(__file__).stat().st_uid,Path(__file__).stat().st_gid)
 success=True
 print('PASS device revocation and disabled-account denial. Three temporary device authorizations retained for native upgrade tests; no emails sent.',flush=True)
finally:
 if not success:
  sql(f"DELETE FROM mail_outbox WHERE invitation_id IN (SELECT id FROM invitations WHERE user_id='{uid}'); DELETE FROM invitations WHERE user_id='{uid}'; DELETE FROM users WHERE id='{uid}' AND email='{email}'; DELETE FROM audit WHERE actor='{email}'")
