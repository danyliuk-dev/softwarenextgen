"""Verify Windows release payloads against the installed SDK and offline sources."""
from pathlib import Path
import struct
root=Path(__file__).resolve().parents[1]
def pe(path):
 with path.open('rb') as f:
  assert f.read(2)==b'MZ',path
  f.seek(0x3c);offset=struct.unpack('<I',f.read(4))[0];f.seek(offset)
  assert f.read(4)==b'PE\0\0',path
  return struct.unpack('<H',f.read(2))[0]
for product,name,server in [('components','NextgenComponents','BlazorGallery'),('reports','Nextgen Reports','NextgenReports.Studio')]:
 output=root/'artifacts/installer-sdk1'/product/'windows';app=output/'win-unpacked';resources=app/'resources'
 assert pe(app/(name+'.exe'))==0x8664
 assert pe(resources/'server'/(server+'.exe'))==0x8664
 for source,target in [(root/'artifacts/installed-sdk'/product/'SDK',resources/'SDK'),(root/'artifacts/offline-docs'/product,resources/'server/wwwroot')]:
  count=0
  for file in source.rglob('*'):
   if not file.is_file():continue
   installed=target/file.relative_to(source);assert installed.read_bytes()==file.read_bytes(),installed;count+=1
   if source.name==product:
    for ext in ['.gz','.br']:assert not Path(str(installed)+ext).exists(),installed
  print('PASS',product,source.name,count,'matching files')
 if product=='reports':
  for name in ['verification','roadmap','getting-started','server-operations','desktop-releases']:
   assert not (resources/'server/wwwroot/guides'/(name+'.html')).exists(),name
 installer=next(output.glob('*-sdk1-win-x64.exe'));assert installer.stat().st_size>100_000_000;assert pe(installer) in [0x14c,0x8664]
 print('PASS Windows PE executables and NSIS artifact:',installer.name)
