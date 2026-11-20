#!/usr/bin/env python3
import json,os,subprocess
from pathlib import Path
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
def quote(s):return "'"+str(s).replace("'","''")+"'"
rows=json.loads(Path('/tmp/nextgen-releases.json').read_text())
for r in rows:
 keys=['id','product','version','platform','filename','storage_name','size','sha256','notes']
 query='INSERT INTO releases('+','.join(keys)+') VALUES('+','.join(quote(r[k]) for k in keys)+') ON CONFLICT(storage_name) DO UPDATE SET sha256=excluded.sha256,size=excluded.size,notes=excluded.notes;'
 subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database'],'-c',query],env=env,check=True,stdout=subprocess.DEVNULL)
print('Registered',len(rows),'private installers')
