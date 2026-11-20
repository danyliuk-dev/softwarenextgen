#!/usr/bin/env python3
"""Apply the reviewed six-installer release atomically; retain existing IDs."""
import json,os,re,subprocess
from pathlib import Path
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
rows=json.loads(Path('/tmp/nextgen-releases-sdk1.json').read_text())
assert len(rows)==6 and len({(r['product'],r['platform']) for r in rows})==6
quote=lambda s:"'"+str(s).replace("'","''")+"'"
statements=['BEGIN;','LOCK TABLE releases IN SHARE ROW EXCLUSIVE MODE;']
keys=['id','product','version','platform','filename','storage_name','size','sha256','notes']
for r in rows:
 assert '/sdk-20261029.1/' in r['storage_name'] and re.fullmatch('[A-F0-9]{64}',r['sha256']) and int(r['size'])>100_000_000
 assert r['product'] in ['components','reports'] and r['platform'] in ['Linux x64','macOS Apple Silicon','Windows x64']
 if 'previous_storage_name' in r:
  updates=','.join(k+'='+quote(r[k]) for k in keys if k not in ['id','product','platform'])
  condition=' AND '.join(k+'='+quote(r[k]) for k in ['id','product','platform'])+' AND storage_name='+quote(r['previous_storage_name'])+' AND sha256='+quote(r['previous_sha256'])
  statements.append("DO $$ DECLARE changed integer; BEGIN UPDATE releases SET "+updates+" WHERE "+condition+"; GET DIAGNOSTICS changed = ROW_COUNT; IF changed <> 1 THEN RAISE EXCEPTION 'Installer record changed; transaction aborted'; END IF; END $$;")
 else:
  assert r['platform']=='Windows x64'
  statements.append("DO $$ BEGIN IF EXISTS(SELECT 1 FROM releases WHERE product="+quote(r['product'])+" AND platform='Windows x64') THEN RAISE EXCEPTION 'Windows release already exists; review before replacing'; END IF; END $$;")
  statements.append('INSERT INTO releases('+','.join(keys)+') VALUES('+','.join(quote(r[k]) for k in keys)+');')
statements.append('COMMIT;')
subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database']],input='\n'.join(statements),text=True,env=env,check=True,stdout=subprocess.DEVNULL)
print('Updated four releases and added two Windows installers atomically')
