import os,subprocess,json
from pathlib import Path
settings=dict(l.split('=',1) for l in Path('/etc/nextgensoftware/app.env').read_text().splitlines() if '=' in l)
d=dict(x.split('=',1) for x in settings['ConnectionStrings__Nextgen'].strip('"').split(';') if '=' in x)
env=dict(os.environ,PGPASSWORD=d['Password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
rows=json.loads(Path('/tmp/releases-remote020.json').read_text());assert len(rows)==3
ids=','.join("'"+str(__import__('uuid').UUID(r['id']))+"'" for r in rows)
q="UPDATE releases SET published=true WHERE product='remote' AND id IN ("+ids+"); SELECT count(*) FROM releases WHERE product='remote' AND published AND id IN ("+ids+");"
r=subprocess.check_output(['psql','-X','-v','ON_ERROR_STOP=1','-h',d['Host'],'-U',d['Username'],'-d',d['Database'],'-Atc',q],env=env,text=True);assert r.strip().endswith('3');print('Three Remote download records published')
