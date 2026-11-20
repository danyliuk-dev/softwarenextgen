#!/usr/bin/env python3
"""Download pinned portable tools into this workspace and verify SHA-256."""
from pathlib import Path
import hashlib,json,subprocess,tarfile,zipfile
root=Path(__file__).resolve().parents[1];lock=json.loads((root/'packaging/windows-toolchain.lock.json').read_text());dest=root/'artifacts/toolchain';downloads=dest/'downloads';downloads.mkdir(parents=True,exist_ok=True)
items=[('node-'+lock['node']+'-linux-x64.tar.xz','https://nodejs.org/dist/'+lock['node']+'/',lock['nodeLinuxX64Sha256']),('electron-v'+lock['electron']+'-win32-x64.zip','https://github.com/electron/electron/releases/download/v'+lock['electron']+'/',lock['electronWindowsX64Sha256'])]
for name,base,expected in items:
 file=downloads/name
 if not file.exists():subprocess.run(['curl','-fL','--retry','3',base+name,'-o',str(file)],check=True)
 assert hashlib.file_digest(file.open('rb'),'sha256').hexdigest()==expected,'Checksum mismatch: '+name
 if name.endswith('.tar.xz'):
  with tarfile.open(file) as archive:archive.extractall(dest,filter='data')
 else:
  with zipfile.ZipFile(file) as archive:archive.extractall(dest/'electron-win32-x64')
 print('Verified and extracted',name)
print('Portable tools ready. System Wine is installed separately by setup-windows-host.sh.')
