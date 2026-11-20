#!/usr/bin/env python3
import json,os,subprocess,uuid,requests,re,time,base64,hmac,hashlib,struct
from pathlib import Path
qa=json.loads(Path('/root/nextgen-qa.json').read_text())
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l);d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
def sql(q):return subprocess.check_output(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database'],'-Atc',q],env=env,text=True).strip()
assert qa['email']=='qa-portal-20261028@example.invalid'
sql("UPDATE users SET role='user',generation='"+str(uuid.uuid4())+"' WHERE id='"+qa['id']+"'")
s=requests.Session();s.cookies.update(qa['cookies']);s.headers['X-Forwarded-Proto']='https'
assert s.get('http://127.0.0.1:5338/account',allow_redirects=False).status_code==302,'Old role session survived'
s=requests.Session();s.headers['X-Forwarded-Proto']='https'
def get(p):
 for c in s.cookies:c.secure=False
 return s.get('http://127.0.0.1:5338'+p,allow_redirects=False)
def post(p,data):
 for c in s.cookies:c.secure=False
 return s.post('http://127.0.0.1:5338'+p,data=data,allow_redirects=False)
def csrf(r):return re.search("name='__RequestVerificationToken' value='([^']+)'",r.text)[1]
r=get('/login');assert post('/login',{'__RequestVerificationToken':csrf(r),'email':qa['email'],'password':qa['password']}).status_code==302
assert get('/account').status_code==302
r=get('/verify');digest=hmac.new(base64.b32decode(qa['key']),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=digest[-1]&15;code=str((struct.unpack('>I',digest[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
assert post('/verify',{'__RequestVerificationToken':csrf(r),'code':code}).status_code==302
assert get('/products').status_code==200
r=get('/admin');assert r.status_code==302 and '/forbidden' in r.headers['Location']
for item in json.loads(Path('/tmp/nextgen-releases.json').read_text()):
 for cookie in s.cookies:cookie.secure=False
 r=s.get('http://127.0.0.1:5338/download/'+item['id'],headers={'Range':'bytes=0-31'},allow_redirects=False);assert r.status_code==206 and len(r.content)==32
print('PASS: ordinary user password + MFA, all four downloads, admin denied, old privileged session invalidated')
# Delete only this synthetic QA fixture and its dependent records.
sql("DELETE FROM mail_outbox WHERE invitation_id IN (SELECT id FROM invitations WHERE user_id='"+qa['id']+"'); DELETE FROM invitations WHERE user_id='"+qa['id']+"'; DELETE FROM users WHERE id='"+qa['id']+"' AND email='"+qa['email']+"'; DELETE FROM audit WHERE actor='"+qa['email']+"'")
assert sql("SELECT count(*) FROM users WHERE email='"+qa['email']+"'")=='0'
assert get('/account').status_code==302
Path('/root/nextgen-qa.json').unlink()
print('PASS: synthetic QA account removed, deleted account session rejected; owner and requested invite account preserved')
