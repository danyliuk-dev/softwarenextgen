#!/usr/bin/env python3
"""Validate new installer streams using a temporary ordinary-user QA fixture."""
import base64,hashlib,hmac,struct,time,uuid,secrets,subprocess,os,re,json
from pathlib import Path
import requests
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
def sql(q):return subprocess.check_output(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database'],'-Atc',q],env=env,text=True).strip()
email='qa-docs-release-20261028@example.invalid';uid=str(uuid.uuid4());token=secrets.token_hex(32).upper();password='QA-'+secrets.token_hex(24)
assert sql("SELECT count(*) FROM users WHERE email='"+email+"'")=='0'
sql(f"INSERT INTO users(id,email,role,generation) VALUES('{uid}','{email}','user','{uuid.uuid4()}'); INSERT INTO invitations(id,user_id,token_hash,expires_at) VALUES('{uuid.uuid4()}','{uid}','{hashlib.sha256(token.encode()).hexdigest().upper()}',now()+interval '15 minutes')")
s=requests.Session();s.headers['X-Forwarded-Proto']='https';base='http://127.0.0.1:5338'
def request(method,path,**kwargs):
 for c in s.cookies:c.secure=False
 return s.request(method,base+path,allow_redirects=False,timeout=180,**kwargs)
def csrf(r):return re.search("name='__RequestVerificationToken' value='([^']+)'",r.text)[1]
try:
 r=request('GET','/accept');assert request('POST','/accept',data={'__RequestVerificationToken':csrf(r),'token':token,'password':password,'confirm':password}).status_code==302
 r=request('GET','/enroll');key=re.search("id='setup-key'>([A-Z2-7]+)",r.text)[1];digest=hmac.new(base64.b32decode(key),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=digest[-1]&15;code=str((struct.unpack('>I',digest[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
 assert request('POST','/enroll',data={'__RequestVerificationToken':csrf(r),'code':code}).status_code==200
 items=json.loads(Path('/tmp/nextgen-releases-docs2.json').read_text())
 for item in items:
  page=request('GET','/products/'+item['product']);assert item['filename'] in page.text and '2026.10.28.2' in page.text
  path='/download/'+item['id'];r=request('GET',path,headers={'Range':'bytes=0-31'});assert r.status_code==206 and len(r.content)==32
  with request('GET',path,stream=True) as r:
   assert r.status_code==200 and item['filename'] in r.headers['Content-Disposition'];size=0;sha=hashlib.sha256()
   for chunk in r.iter_content(1024*1024):size+=len(chunk);sha.update(chunk)
  assert size==item['size'] and sha.hexdigest().upper()==item['sha256'],item['filename']
  assert requests.get(base+path,allow_redirects=False,timeout=15).status_code==302
  print('PASS authenticated download, Range, SHA-256:',item['filename'],flush=True)
finally:
 sql(f"DELETE FROM mail_outbox WHERE invitation_id IN (SELECT id FROM invitations WHERE user_id='{uid}'); DELETE FROM invitations WHERE user_id='{uid}'; DELETE FROM users WHERE id='{uid}' AND email='{email}'; DELETE FROM audit WHERE actor='{email}'")
 assert sql("SELECT count(*) FROM users WHERE email='"+email+"'")=='0'
 print('Temporary ordinary-user QA fixture removed; no emails sent',flush=True)
