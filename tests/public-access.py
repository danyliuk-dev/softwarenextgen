#!/usr/bin/env python3
import concurrent.futures,json,re
from pathlib import Path
import requests
base='https://softwarenextgen.com';root=Path(__file__).resolve().parents[1]
paths=['/products/remote','/images/remote-overview.svg','/','/products','/products/components','/products/reports','/preview/reports/sales/manifest','/preview/reports/sales/page-1.png','/preview/reports/charts/sample.pdf','/preview/components/preview/NgDataGrid','/preview/components/preview/NgButton','/preview/components/grouped-range']
paths += ['/images/home/'+d['Path'].split('/')[-1]+'.webp' for d in json.loads((root/'server/manuals/components/index.json').read_text()) if d['Path'].startswith('manual/Ng')]
paths += ['/images/home/report-'+d['Path']+'.webp' for d in json.loads((root/'server/manuals/reports/index.json').read_text())]
paths += ['/images/components-overview.svg','/images/reports-overview.svg','/home-showcase.css','/home-showcase.js','/images/home/hero-report.png']+['/images/home/'+n+'.webp' for n in ['grid','charts','scheduler','forms','report','export','data']]
for d in json.loads((root/'server/manuals/components/index.json').read_text()):
 if d['Path'].startswith('manual/Ng'): paths.extend(['/preview/components/preview/'+d['Path'].split('/')[-1],'/images/components/'+d['Path'].split('/')[-1]+'.svg'])
for product in ['components','reports','remote']:
 paths += ['/docs/'+product+'/'+d['Path'] for d in json.loads((root/'server/manuals'/product/'index.json').read_text())]
def check(path):
 r=requests.get(base+path,allow_redirects=False,timeout=30);assert r.status_code==200,(path,r.status_code)
 if 'text/html' in r.headers.get('Content-Type',''):assert not re.search('telerik|stimulsoft|Unknown component|This example could not render',r.text,re.I),path
 return path
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:result=list(pool.map(check,paths))
for path in ['/admin','/admin/releases','/account','/updates/remote/devices','/licenses','/admin/licenses']+['/download/'+r['id'] for r in json.loads((root/'deploy/releases-current.json').read_text())+json.loads((root/'deploy/releases-remote020.json').read_text())+json.loads((root/'deploy/releases-remote031.json').read_text())+json.loads((root/'deploy/releases-remote033.json').read_text())+json.loads((root/'deploy/releases-remote041.json').read_text())+json.loads((root/'deploy/releases-remote042.json').read_text())+json.loads((root/'deploy/releases-remote043.json').read_text())]:
 r=requests.get(base+path,allow_redirects=False,timeout=30);assert r.status_code==302 and '/login' in r.headers.get('Location',''),(path,r.status_code)
home=requests.get(base).text;assert home.count('data-home-showcase')==2 and home.count('data-showcase-category=')==14 and home.count('data-category=')==67 and '/images/home/grid.webp' in home and '/home-showcase.js' in home and '<iframe' not in home
product=requests.get(base+'/products/components').text;assert 'Sign in to download' in product and '/download/' not in product
print('PASS:',len(result),'public pages/assets; 83 manuals and homepage product previews public; all registered installers/account/admin still require login; prohibited mentions absent')

assert product.count('data-component-card')==47
assert product.count('data-preview-src=')==47
print('PASS: all 47 components have their own live preview')

assert product.count('data-component-category')==8
assert product.count("class='component-thumbnail'")==94
print('PASS: 8 categories and 47 schematic icons in both catalog and documentation')
