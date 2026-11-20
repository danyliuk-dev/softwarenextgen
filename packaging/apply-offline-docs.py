from pathlib import Path
import sys,shutil,json
source=Path(sys.argv[1]);target=Path(sys.argv[2])
for p in source.rglob('*'):
 if not p.is_file():continue
 dst=target/p.relative_to(source);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
 for ext in ['.br','.gz']:
  old=Path(str(dst)+ext)
  if old.exists():old.unlink()
print('Applied documentation overlay:',source,'to',target)

# Old source-tree manuals are not part of the installed documentation catalog.
revision=source/'offline-docs/revision.json'
if revision.exists() and json.loads(revision.read_text()).get('product')=='reports':
 for old in ['verification','roadmap','getting-started','server-operations','desktop-releases']:
  for suffix in ['.html','.html.br','.html.gz']:
   (target/'guides'/(old+suffix)).unlink(missing_ok=True)
 print('Removed legacy source-build manuals from installed Reports webroot')
