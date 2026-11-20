from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
overlay=root/'artifacts/offline-docs/components'
for rid in ['linux-x64','win-x64','osx-arm64']:
 server=root/'artifacts/batch073/servers'/rid
 deps=json.loads((server/'BlazorGallery.deps.json').read_text())
 assert 'NextgenComponents.Blazor/0.73.0' in deps['libraries'],rid
 count=0
 for source in overlay.rglob('*'):
  if not source.is_file():continue
  target=server/'wwwroot'/source.relative_to(overlay)
  assert target.read_bytes()==source.read_bytes(),target
  assert not Path(str(target)+'.br').exists() and not Path(str(target)+'.gz').exists(),target
  count+=1
 print('PASS',rid,'library 0.73.0;',count,'identical offline files; stale compressed overlays absent')
sdk=root/'artifacts/installed-sdk/components/SDK'
assert json.loads((sdk/'manifest.json').read_text())['version']=='0.73.0'
assert [p.name for p in (sdk/'NuGet').glob('NextgenComponents.Blazor.*.nupkg')]==['NextgenComponents.Blazor.0.73.0.nupkg']
assert 'version: 0.73.0' in (sdk/'Flutter/nextgen_components/pubspec.yaml').read_text()
print('PASS .NET and Flutter SDK versions match, no obsolete NuGet package')
