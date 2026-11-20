#!/usr/bin/env python3
"""Run once as root on dmewebapp with a temporary Cloud SQL provisioner."""
import json,os,secrets,subprocess
from pathlib import Path
config=json.loads(Path('/tmp/nextgen-provision.json').read_text())
env=dict(os.environ,PGPASSWORD=config['provisioner_password'],PGSSLMODE='require',LC_ALL='C.UTF-8')
def psql(query,db='postgres'):
 return subprocess.run(['psql','-X','-v','ON_ERROR_STOP=1','-h','172.25.0.3','-U',config['provisioner'],'-d',db],input=query,text=True,env=env,check=True,capture_output=True)
password=config['app_password']
if '1' not in psql("SELECT 1 FROM pg_roles WHERE rolname='nextgen_software_app'").stdout:
 psql("CREATE ROLE nextgen_software_app LOGIN PASSWORD '"+password+"' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;")
psql('GRANT nextgen_software_app TO '+config['provisioner']+';')
psql('CREATE DATABASE nextgen_software OWNER nextgen_software_app;')
psql('REVOKE ALL ON DATABASE nextgen_software FROM PUBLIC; GRANT CONNECT ON DATABASE nextgen_software TO nextgen_software_app;')
psql('REVOKE ALL ON SCHEMA public FROM PUBLIC; GRANT USAGE,CREATE ON SCHEMA public TO nextgen_software_app;','nextgen_software')
subprocess.run(['useradd','--system','--home','/var/lib/nextgensoftware','--shell','/usr/sbin/nologin','nextgensoftware'],check=True)
for path in ['/etc/nextgensoftware','/var/lib/nextgensoftware/keys','/opt/nextgensoftware/releases']:
 Path(path).mkdir(parents=True,exist_ok=True)
subprocess.run(['chown','-R','nextgensoftware:nextgensoftware','/var/lib/nextgensoftware'],check=True)
mail={}
for line in Path('/etc/dme-landing/app.env').read_text().splitlines():
 if line.startswith('Mail__'):k,v=line.split('=',1);mail[k]=v
settings={'ConnectionStrings__Nextgen':'"Host=172.25.0.3;Database=nextgen_software;Username=nextgen_software_app;Password='+password+';SSL Mode=Require;Maximum Pool Size=10"','ASPNETCORE_URLS':'"http://127.0.0.1:5338"','AllowedHosts':'"softwarenextgen.com;www.softwarenextgen.com;localhost;127.0.0.1"','KeysPath':'"/var/lib/nextgensoftware/keys"','ReleasesBucket':'"causal-armor-506513-a7-nextgensoftware-installers"','Mail__Sender':'"support@dmeclinic.com"','Logging__LogLevel__Default':'"Warning"',**mail}
p=Path('/etc/nextgensoftware/app.env');p.write_text('\n'.join(k+'='+v for k,v in settings.items())+'\n');p.chmod(0o600)
print('Created isolated database/role and service configuration. No existing database changed.')
