#!/usr/bin/env python3
import base64,hashlib,hmac,struct,time,uuid,secrets,subprocess,os,re,json
from pathlib import Path
import requests
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
def sql(q):return subprocess.check_output(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database'],'-Atc',q],env=env,text=True).strip()
def seed(email,role):
 uid=str(uuid.uuid4());token=secrets.token_hex(32).upper();sql(f"INSERT INTO users(id,email,role,generation) VALUES('{uid}','{email}','{role}','{uuid.uuid4()}'); INSERT INTO invitations(id,user_id,token_hash,expires_at) VALUES('{uuid.uuid4()}','{uid}','{hashlib.sha256(token.encode()).hexdigest().upper()}',now()+interval '48 hours')");return uid,token
if sql("SELECT count(*) FROM users WHERE email='admin@softwarenextgen.com'")=='0':
 _,token=seed('admin@softwarenextgen.com','admin');p=Path('/root/nextgen-admin-setup.url');p.write_text('https://softwarenextgen.com/accept#'+token);p.chmod(0o600)
qa='qa-portal-20261028@example.invalid'
assert sql("SELECT count(*) FROM users WHERE email='"+qa+"'")=='0','QA fixture already exists'
uid,token=seed(qa,'admin');password='QA-'+secrets.token_hex(24)
s=requests.Session();s.headers['X-Forwarded-Proto']='https'
def get(path):
 for c in s.cookies:c.secure=False
 return s.get('http://127.0.0.1:5338'+path,allow_redirects=False)
def post(path,data):
 for c in s.cookies:c.secure=False
 return s.post('http://127.0.0.1:5338'+path,data=data,allow_redirects=False)
def csrf(r):return re.search("name='__RequestVerificationToken' value='([^']+)'",r.text)[1]
def totp(key):
 digest=hmac.new(base64.b32decode(key),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15;return str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
r=get('/accept');r=post('/accept',{'__RequestVerificationToken':csrf(r),'token':token,'password':password,'confirm':password});assert r.status_code==302,r.status_code
assert get('/account').status_code==302
r=get('/enroll');key=re.search("id='setup-key'>([A-Z2-7]+)",r.text)[1];r=post('/enroll',{'__RequestVerificationToken':csrf(r),'code':totp(key)});assert r.status_code==200
recovery=re.search("id='recovery-codes'>([^<]+)",r.text)[1].splitlines()
for path in ['/products','/products/components','/products/reports','/docs/components/overview','/docs/reports/report-authoring-manual','/admin','/admin/releases','/account']:assert get(path).status_code==200,path
recipient=os.environ.get('NEXTGEN_TEST_RECIPIENT','')
assert not recipient or re.fullmatch(r'[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+',recipient)
if recipient and sql("SELECT count(*) FROM users WHERE email='"+recipient+"'")=='0':
 r=get('/admin');r=post('/admin/invite',{'__RequestVerificationToken':csrf(r),'email':recipient});assert r.status_code==302
p=Path('/root/nextgen-qa.json');p.write_text(json.dumps({'id':uid,'email':qa,'password':password,'key':key,'recovery':recovery,'cookies':requests.utils.dict_from_cookiejar(s.cookies)}));p.chmod(0o600)
print('PASS: production password onboarding, mandatory MFA, protected manuals, admin pages. Test invitation queued for requested recipient. Owner setup prepared separately.')
