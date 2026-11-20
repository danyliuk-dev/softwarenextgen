"""Inspect the actual Linux installer payload, including SDK and offline manuals."""
from pathlib import Path
import tempfile,subprocess,hashlib,json
root=Path(__file__).resolve().parents[1]
for product in ['components','reports']:
 installer=next((root/'artifacts/installer-sdk1'/product/'installers').glob('*.AppImage'))
 with tempfile.TemporaryDirectory(prefix='nextgen-installer-check-') as work:
  subprocess.run([str(installer),'--appimage-extract'],cwd=work,stdout=subprocess.DEVNULL,check=True)
  resources=Path(work)/'squashfs-root/resources'
  if product=='reports':
   for name in ['verification','roadmap','getting-started','server-operations','desktop-releases']:
    assert not (resources/'server/wwwroot/guides'/(name+'.html')).exists(),name
  for source in (root/'artifacts/installed-sdk'/product/'SDK').rglob('*'):
   if not source.is_file():continue
   target=resources/'SDK'/source.relative_to(root/'artifacts/installed-sdk'/product/'SDK')
   assert target.is_file(),target
   if source.name=="README.txt":assert target.read_bytes().startswith(source.read_bytes()),target
   else:assert source.read_bytes()==target.read_bytes(),target
  overlay=root/'artifacts/offline-docs'/product
  for source in overlay.rglob('*'):
   if not source.is_file():continue
   target=resources/'server/wwwroot'/source.relative_to(overlay)
   if source.name=="README.txt":assert target.read_bytes().startswith(source.read_bytes()),target
   else:assert source.read_bytes()==target.read_bytes(),target
   assert not Path(str(target)+'.br').exists(),target
   assert not Path(str(target)+'.gz').exists(),target
  print('PASS installer payload:',installer.name,'SDK matches; all offline files match; no stale compressed copies')
