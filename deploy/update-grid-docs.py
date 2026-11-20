#!/usr/bin/env python3
"""Atomically replace the three authorized installer records; retain download IDs."""
import json,os,subprocess
from pathlib import Path
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
rows=json.loads(Path('/tmp/nextgen-releases-grid1.json').read_text());assert len(rows)==3
quote=lambda s:"'"+str(s).replace("'","''")+"'"
statements=['BEGIN;']
for r in rows:
 assert r['product']=='components'
 assert '/grid-20261029.2/' in r['storage_name'] and len(r['sha256'])==64
 updates=','.join(k+'='+quote(r[k]) for k in ['filename','storage_name','size','sha256','notes'])
 condition=' AND '.join(k+'='+quote(r[k]) for k in ['id','product','platform'])+' AND storage_name='+quote(r['previous_storage_name'])+' AND sha256='+quote(r['previous_sha256'])
 statements.append("DO $$ DECLARE changed integer; BEGIN UPDATE releases SET "+updates+" WHERE "+condition+"; GET DIAGNOSTICS changed = ROW_COUNT; IF changed <> 1 THEN RAISE EXCEPTION 'Installer record changed; no updates applied'; END IF; END $$;")
statements.append('COMMIT;')
subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database']],input='\n'.join(statements),text=True,env=env,check=True,stdout=subprocess.DEVNULL)
print('Updated three installer records atomically; existing download IDs retained')
