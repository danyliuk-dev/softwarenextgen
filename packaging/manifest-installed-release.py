#!/usr/bin/env python3
"""Prepare six installer records with hashes and guarded prior-release metadata."""
from pathlib import Path
import hashlib,json,uuid
root=Path(__file__).resolve().parents[1];old=json.loads((root/'deploy/releases-current.json').read_text());rows=[]
for product,version,name in [('components','0.70.0','NextgenComponents'),('reports','0.2.1','Nextgen-Reports')]:
 for platform,rid,file in [('Linux x64','linux-x64',root/f'artifacts/installer-sdk1/{product}/installers/{name}-{version}-sdk1-linux-x86_64.AppImage'),('macOS Apple Silicon','osx-arm64',root/f'artifacts/installer-sdk1/{name}-{version}-sdk1-mac-arm64.dmg'),('Windows x64','win-x64',root/f'artifacts/installer-sdk1/{product}/windows/{name}-{version}-sdk1-win-x64.exe')]:
  assert file.stat().st_size>100_000_000,file
  previous=next((r for r in old if r['product']==product and r['platform']==platform),None)
  notes='Documentation revision 2026.10.29.1: installed application workflows, local SDK packages and offline manuals. '
  notes+='Includes Blazor NuGet and Flutter SDK.' if product=='components' else 'Includes .NET client and Blazor viewer NuGets, Flutter client/viewer SDK, Python tools and report samples.'
  if platform=='macOS Apple Silicon':notes+=' Apple Silicon only. Ad-hoc signed; no Developer ID notarization.'
  if platform=='Windows x64':notes+=' Current-user installer. Authenticode signing is not configured.'
  row=dict(id=previous['id'] if previous else str(uuid.uuid5(uuid.NAMESPACE_URL,'https://softwarenextgen.com/releases/'+product+'/'+version+'/windows-x64')),product=product,version=version,platform=platform,filename=file.name,storage_name=f'{product}/{version}/sdk-20261029.1/'+('final/' if product=='reports' else '')+f'{rid}/{file.name}',size=file.stat().st_size,sha256=hashlib.file_digest(file.open('rb'),'sha256').hexdigest().upper(),notes=notes)
  if previous:row.update(previous_storage_name=previous['storage_name'],previous_sha256=previous['sha256'])
  rows.append(row)
(root/'deploy/releases-sdk-20261029.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Prepared six guarded release records; production is unchanged')
