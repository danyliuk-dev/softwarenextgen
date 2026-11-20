from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote,urljoin
import json,sys
root=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self,s):super().__init__();self.ids=[];self.links=[];self.assets=[];self.feed(s)
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if t=='a' and a.get('href'):self.links.append(a['href'])
  if t in ['script','img','link']:
   value=a.get('src') or a.get('href')
   if value:self.assets.append(value)
for product in ['components','reports']:
 webroot=root/'artifacts/offline-docs'/product
 pages={'/'+str(p.relative_to(webroot)):Page(p.read_text()) for p in webroot.rglob('*.html') if 'report-examples' not in p.parts}
 count=0
 for path,page in pages.items():
  for asset in page.assets:
   u=urlsplit(asset);assert not u.scheme and not u.netloc,(path,'non-local asset',asset);assert (webroot/urlsplit(urljoin(path,asset)).path.lstrip('/')).is_file(),asset
  for link in page.links:
   u=urlsplit(link)
   if u.scheme:
    assert u.hostname not in ('127.0.0.1','localhost'),(path,link);continue
   if u.path.startswith(('/preview/','/flutter/')) or u.path in ('/','/virtual-data','/remote-range','/grouped-range'):continue
   target=u.path or path
   assert not target.startswith('/docs/'),(path,'website link',link)
   if target.startswith('/report-examples/'):
    assert (webroot/target.lstrip('/')).is_file();continue
   if target.endswith('.pdf'):assert (webroot/target.lstrip('/')).is_file();continue
   assert target in pages,(path,link)
   if u.fragment:assert unquote(u.fragment) in pages[target].ids,(path,link)
   count+=1
 print('PASS offline',product,len(pages),'HTML pages,',count,'local document links, all assets bundled')
