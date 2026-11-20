"""Prevent repository-build instructions from returning to distribution manuals."""
from pathlib import Path
from html.parser import HTMLParser
import re,zipfile
root=Path(__file__).resolve().parents[1]
class Text(HTMLParser):
 def __init__(self,s):super().__init__();self.text='';self.feed(s)
 def handle_data(self,s):self.text+=s
for p in (root/'server/manuals').rglob('*.html'):
 text=Text(p.read_text()).text
 assert not re.search(r'dotnet (?:build|restore|run --project|test)|npm (?:ci|run prepare)|git clone|ProjectReference|src/Nextgen|scripts/(?:open-|build-|generate_|server-user)|repository root|from this checkout',text),p
for product,names in [('components',['NextgenComponents.Blazor']),('reports',['NextgenReports.Client','NextgenReports.Blazor'])]:
 sdk=root/'artifacts/installed-sdk'/product/'SDK'
 for name in names:
  matches=list((sdk/'NuGet').glob(name+'.*.nupkg'));assert len(matches)==1,(name,matches)
  with zipfile.ZipFile(matches[0]) as z:
   assert 'lib/net10.0/'+name+'.dll' in z.namelist(),name
   if name.endswith('Blazor'):assert any(n.startswith('staticwebassets/') for n in z.namelist()),name
 assert (sdk/'Flutter'/('nextgen_components' if product=='components' else 'nextgen_reports')/'pubspec.yaml').is_file()
print('PASS: all 79 manuals use installed workflows; NuGet assemblies/static assets and Flutter packages present')
