#!/usr/bin/env python3
"""Isolated DB integration: invite, administrator MFA, replay, recovery, RBAC and revocation."""
import base64,hashlib,hmac,struct,time,uuid,subprocess,re,secrets
import requests
BASE='http://127.0.0.1:5337'
def sql(q):return subprocess.check_output(['psql','-h','/tmp/nextgen-test-sock','-p','55461','-d','nextgen_test','-Atc',q],text=True).strip()
def session():
 s=requests.Session();s.headers['X-Forwarded-Proto']='https';return s
def get(s,path):
 for c in s.cookies:c.secure=False
 return s.get(BASE+path,allow_redirects=False)
def post(s,path,data):
 for c in s.cookies:c.secure=False
 return s.post(BASE+path,data=data,allow_redirects=False)
def csrf(r):return re.search("name='__RequestVerificationToken' value='([^']+)'",r.text)[1]
def totp(key,offset=0):
 step=int(time.time())//30+offset;d=hmac.new(base64.b32decode(key),struct.pack('>Q',step),hashlib.sha1).digest();o=d[-1]&15;return str((struct.unpack('>I',d[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
def seed(email,role):
 uid=str(uuid.uuid4());token=secrets.token_hex(32).upper();sql(f"INSERT INTO users(id,email,role,generation) VALUES('{uid}','{email}','{role}','{uuid.uuid4()}'); INSERT INTO invitations(id,user_id,token_hash,expires_at) VALUES('{uuid.uuid4()}','{uid}','{hashlib.sha256(token.encode()).hexdigest().upper()}',now()+interval '1 hour')")
 return uid,token
password='QA-only-'+secrets.token_hex(12)
sql('TRUNCATE mail_outbox,invitations,audit,releases,users CASCADE')
admin,at=seed('qa-admin@example.invalid','admin');uid,ut=seed('qa-user@example.invalid','user')
a=session();u=session();anon=session()
assert get(anon,'/products').status_code==200
assert get(anon,'/docs/components/overview').status_code==200
assert get(anon,'/download/'+str(uuid.uuid4())).status_code==302
assert post(anon,'/login',{'email':'x','password':'x'}).status_code==400

def enroll(s,token):
 r=get(s,'/accept');r=post(s,'/accept',{'__RequestVerificationToken':csrf(r),'token':token,'password':password,'confirm':password});assert r.status_code==302,r.text
 assert get(s,'/account').status_code==302,'Password-only session gained access'
 r=get(s,'/enroll');assert r.status_code==200,r.text
 key=re.search("id='setup-key'>([A-Z2-7]+)",r.text)[1]
 r=post(s,'/enroll',{'__RequestVerificationToken':csrf(r),'code':totp(key)});assert r.status_code==200,r.text
 codes=re.search("id='recovery-codes'>([^<]+)",r.text)[1].splitlines();assert len(codes)==10
 assert get(s,'/products').status_code==200
 return key,codes
ak,ac=enroll(a,at)
r=get(u,'/accept');r=post(u,'/accept',{'__RequestVerificationToken':csrf(r),'token':ut,'password':password,'confirm':password});assert r.status_code==302 and r.headers['Location']=='/products'
assert get(u,'/account').status_code==200
assert get(a,'/admin').status_code==200
assert get(u,'/admin').status_code==302
assert '/forbidden' in get(u,'/admin').headers['Location']
assert get(u,'/docs/components/overview').status_code==200
assert get(u,'/docs/reports/report-authoring-manual').status_code==200
r=get(anon,'/accept');assert post(anon,'/accept',{'__RequestVerificationToken':csrf(r),'token':ut,'password':password,'confirm':password}).status_code==400
r=get(u,'/products');assert post(u,'/logout',{'__RequestVerificationToken':csrf(r)}).status_code==302
r=get(u,'/login');assert post(u,'/login',{'__RequestVerificationToken':csrf(r),'email':'qa-user@example.invalid','password':password}).status_code==302
assert get(u,'/account').status_code==200,'Customer password login failed'
r=get(a,'/products');assert post(a,'/logout',{'__RequestVerificationToken':csrf(r)}).status_code==302
r=get(a,'/login');assert post(a,'/login',{'__RequestVerificationToken':csrf(r),'email':'qa-admin@example.invalid','password':password}).headers['Location']=='/verify'
r=get(a,'/verify');assert post(a,'/verify',{'__RequestVerificationToken':csrf(r),'code':totp(ak)}).status_code==400,'TOTP replay accepted'
r=get(a,'/verify');assert post(a,'/verify',{'__RequestVerificationToken':csrf(r),'code':ac[0]}).status_code==302
assert sql(f"SELECT cardinality(recovery) FROM users WHERE id='{admin}'")=='9'
r=get(a,'/admin');assert post(a,'/admin/invite',{'__RequestVerificationToken':csrf(r),'email':'qa-invite@example.invalid'}).status_code==302
assert sql("SELECT count(*) FROM mail_outbox WHERE recipient='qa-invite@example.invalid'")=='1'
r=get(a,'/admin');assert post(a,f'/admin/users/{uid}/toggle',{'__RequestVerificationToken':csrf(r)}).status_code==302
assert get(u,'/account').status_code==302,'Blocked user retained session'
# An expired invitation cannot be redeemed.
xid,xt=seed('qa-expired@example.invalid','user');sql(f"UPDATE invitations SET expires_at=now()-interval '1 minute' WHERE user_id='{xid}'")
r=get(anon,'/accept');assert post(anon,'/accept',{'__RequestVerificationToken':csrf(r),'token':xt,'password':password,'confirm':password}).status_code==400
assert sql("SELECT count(*) FROM users WHERE email='qa-expired@example.invalid' AND password_hash=''")=='1'
print('PASS: protected pages, CSRF, invitation single use/expiry, administrator MFA, customer password login, TOTP replay, recovery consumption, admin role, mail queue, session revocation')
