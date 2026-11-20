#!/usr/bin/env python3
"""Check actual destinations, including fragments, across all published manuals."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import sys
root=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self,text):super().__init__();self.ids=[];self.links=[];self.feed(text)
 def handle_starttag(self,tag,attributes):
  attrs=dict(attributes)
  if 'id' in attrs:self.ids.append(attrs['id'])
  if tag=='a' and attrs.get('href'):self.links.append(attrs['href'])
files={f'/docs/{p.relative_to(root/"server/manuals").with_suffix("")}':p for p in (root/'server/manuals').rglob('*.html')}
live='--live' in sys.argv
if live:
 import requests
 def fetch(url):
  r=requests.get('https://softwarenextgen.com'+url,timeout=30);assert r.status_code==200,(url,r.status_code);return url,Page(r.text)
 with ThreadPoolExecutor(max_workers=6) as pool:pages=dict(pool.map(fetch,files))
else:
 pages={url:Page(p.read_text()) for url,p in files.items()}
 for url,p in pages.items():
  if url.startswith('/docs/components/'):p.ids.append('live-example')
errors=[];checked=0;preview_paths=set()
for url,p in pages.items():
 for identifier,n in Counter(p.ids).items():
  if n!=1:errors.append((url,'duplicate id',identifier))
 for href in p.links:
  u=urlsplit(href)
  if u.hostname in ('localhost','127.0.0.1','::1'):errors.append((url,'local host',href))
  if u.hostname=='github.com' and ('NextgenReportEngine/blob/' in href or 'NextgenComponents/blob/' in href):errors.append((url,'repository manual',href))
  if u.scheme:continue
  target_url=u.path or url
  if target_url.startswith('/preview/components/'):preview_paths.add(target_url)
  if target_url.startswith('/docs/'):
   checked+=1;target=pages.get(target_url)
   if target is None:errors.append((url,'missing document',href));continue
   if u.fragment and unquote(u.fragment) not in target.ids:errors.append((url,'missing section',href))
  elif not u.path and u.fragment and unquote(u.fragment) not in p.ids:errors.append((url,'missing local section',href))
if live:
 for path in preview_paths:
  r=requests.get('https://softwarenextgen.com'+path,timeout=30);assert r.status_code==200,(path,r.status_code)
assert not errors,'\n'.join(map(str,errors))
print(f'PASS: {len(pages)} manuals, {checked} documentation links and their sections; no local-host or repository-manual links ({"production" if live else "source"})')
