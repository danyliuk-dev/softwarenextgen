import os,subprocess,json,datetime
from pathlib import Path
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
args=['-h',d['Host'],'-U',d['Username'],'-d',d['Database']]
def sql(q):return subprocess.check_output(['psql','-X','-v','ON_ERROR_STOP=1',*args,'-Atc',q],env=env,text=True).strip()
rows=json.loads(Path('/tmp/releases-remote020.json').read_text());assert len(rows)==3 and all(r['product']=='remote' and r['storage_name'].startswith('remote/0.2.0/portal-20261117/') for r in rows)
quote=lambda s:"'"+str(s).replace("'","''")+"'"
ids=','.join(quote(r['id']) for r in rows)
backup=Path('/root/nextgensoftware-remote020-backup');backup.mkdir(mode=0o700,exist_ok=False)
with (backup/'releases.sql').open('wb') as f:subprocess.run(['pg_dump',*args,'--table=public.releases','--no-owner','--no-acl'],env=env,stdout=f,check=True)
original=sql("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='releases'::regclass AND conname='releases_product_check'")
assert 'components' in original and 'reports' in original and 'remote' not in original,original
assert sql("SELECT count(*) FROM releases WHERE product='remote'")=='0'
(backup/'constraint.txt').write_text(original)
statements=['BEGIN;','ALTER TABLE releases DROP CONSTRAINT releases_product_check;',"ALTER TABLE releases ADD CONSTRAINT releases_product_check CHECK(product IN ('components','reports','remote')); "]
for r in rows:
 cols=['id','product','version','platform','filename','storage_name','size','sha256','notes']
 statements.append('INSERT INTO releases('+','.join(cols)+',published) VALUES('+','.join(quote(r[c]) for c in cols)+',false);')
statements.append('COMMIT;')
subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1',*args],input='\n'.join(statements),text=True,env=env,check=True,stdout=subprocess.DEVNULL)
assert sql('SELECT count(*) FROM releases WHERE id IN ('+ids+") AND product='remote' AND NOT published")=='3'
print('Backed up release table; allowed Remote product; inserted three hidden release rows. Existing releases preserved.')
