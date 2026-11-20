#!/usr/bin/env python3
from pathlib import Path
import re,json
root=Path(__file__).resolve().parents[1]
for product in ('components','reports'):
 directory=root/'server/manuals'/product;index=json.loads((directory/'index.json').read_text());paths={x['Path'] for x in index}
 for item in index:
  source=directory/(item['Path']+'.html');text=source.read_text();assert not re.search('telerik|stimulsoft',text,re.I),source
  for target in re.findall(r'href="/docs/'+product+r'/([^"#]+)',text):assert target in paths,(source,target)
 print(product,len(index),'manuals: all internal links resolve; prohibited mentions absent')
for sample in ('sales','charts'):
 directory=root/'server/previews/reports'/sample;assert (directory/'sample.pdf').is_file();assert list(directory.glob('page-*.png'))
print('Report preview assets present')
components=[d['Path'].split('/')[-1] for d in json.loads((root/'server/manuals/components/index.json').read_text()) if d['Path'].startswith('manual/Ng')]
categories=re.findall(r'"(Ng\w+)"',(root/'server/ComponentCatalog.cs').read_text())
assert len(categories)==len(set(categories)) and set(categories)==set(components),'Every component must have exactly one category'
for component in components:
 image=root/'server/wwwroot/images/components'/(component+'.svg')
 assert image.is_file() and image.stat().st_size>100,component+' icon missing'
print('All components have a category and schematic icon')
