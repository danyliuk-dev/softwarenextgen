#!/usr/bin/env python3
"""Build portable, fully local manuals from the website's verified content."""
import argparse,json,re,html,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]

def build(product,dest):
 revision='2026.10.31.2' if product=='components' else '2026.10.29.1'
 dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);assets=dest/'offline-docs';assets.mkdir(exist_ok=True)
 for name in ['site.css','fonts.css','brand.svg'] :shutil.copy(root/'server/wwwroot'/name,assets/name)
 css=(assets/'site.css').read_text().replace("url('/fonts.css')","url('/offline-docs/fonts.css')")
 (assets/'site.css').write_text(css)
 js=(root/'server/wwwroot/site.js').read_text().replace("'/preview/reports/'","'/offline-docs/reports/'").replace("'/manifest'","'/manifest.json'")
 (assets/'site.js').write_text(js)
 if product=='components':shutil.copytree(root/'server/wwwroot/images/components',assets/'icons',dirs_exist_ok=True)
 else:
  shutil.copytree(root/'server/wwwroot/report-examples',dest/'report-examples',dirs_exist_ok=True)
  shutil.copytree(root/'server/previews/reports',assets/'reports',dirs_exist_ok=True)
  for sample in ['sales','charts']:
   directory=assets/'reports'/sample;(directory/'manifest.json').write_text(json.dumps({'pages':sorted(p.name for p in directory.glob('page-*.png'))}))
 docs=json.loads((root/'server/manuals'/product/'index.json').read_text())
 def url(slug):
  if product=='components':return '/manual/'+slug+'.html'
  return {'report-authoring-manual':'/manual.html','developer-guide':'/developer-guide.html'}.get(slug,'/guides/'+slug+'.html')
 categories=[]
 if product=='components':
  source=(root/'server/ComponentCatalog.cs').read_text()
  categories=[(html.unescape(name),re.findall(r'"([^"]+)"',names)) for name,names in re.findall(r'\("([^"]+)", \[(.*?)\]\)',source)]
 def category(doc):
  name=doc['Path'].split('/')[-1]
  return next((label for label,names in categories if name in names),'Guides & getting started')
 def thumb(doc):
  name=doc['Path'].split('/')[-1]
  return f'<img class="component-thumbnail" src="/offline-docs/icons/{name}.svg" alt="" width="64" height="64" loading="lazy">' if product=='components' and name.startswith('Ng') else ''
 def links(current=None):
  groups=['Guides & getting started']+[g[0] for g in categories] if categories else ['Report Engine guides']
  result=''
  for group in groups:
   selected=[d for d in docs if not categories or category(d)==group]
   order=next((names for label,names in categories if label==group),[])
   if order:selected.sort(key=lambda d:order.index(d['Path'].split('/')[-1]))
   result+='<section class="doc-category"><h3>'+html.escape(group)+'</h3><div class="doc-list">'
   for d in selected:
    active=' aria-current="page"' if d['Path']==current else ''
    result+=f'<a href="{url(d["Path"])}"{active}>'+thumb(d)+'<span class="doc-link-title">'+html.escape(d['Title'])+'</span></a>'
   result+='</div></section>'
  return result
 title='NextgenComponents' if product=='components' else 'NextgenReportEngine'
 home='/workspace.html' if product=='components' else '/'
 def shell(heading,body):
  return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(heading)+' · '+title+'</title><link rel="stylesheet" href="/offline-docs/site.css"><script src="/offline-docs/site.js" defer></script></head><body><header><a class="brand" href="'+home+'"><img src="/offline-docs/brand.svg" width="34" height="34" alt="">'+title+'</a><nav><a href="'+home+'">Workspace</a><a href="'+url('overview')+'">Documentation</a></nav></header><main class="workspace"><div class="page-heading"><span class="eyebrow">OFFLINE DOCUMENTATION</span><h1>'+html.escape(heading)+'</h1></div>'+body+'</main><footer>Documentation revision '+revision+' · Included with your application</footer></body></html>'
 def rewrite(m):
  href=html.unescape(m[1])
  prefix='/docs/'+product+'/'
  if href.startswith(prefix):
   parts=href[len(prefix):].split('#',1);href=url(parts[0])+('#'+parts[1] if len(parts)>1 else '')
  elif href.startswith('/preview/components/'):href=href.replace('/preview/components/','/',1)
  return 'href="'+html.escape(href,quote=True)+'"'
 for d in docs:
  slug=d['Path'];content=(root/'server/manuals'/product/(slug+'.html')).read_text()
  content=re.sub(r'href="([^"]*)"',rewrite,content)
  preview=''
  name=slug.split('/')[-1]
  if product=='components' and name.startswith('Ng'):
   content=content.replace('Flutter example code</a>','Flutter example code</a>')
   preview=f'<section id="live-example" class="preview-panel"><div class="preview-toolbar"><strong>Live Blazor example</strong><a href="/preview/{name}">Open example ↗</a><a href="/flutter/index.html?preview={name}">Flutter gallery ↗</a><button type="button" data-reload-preview>Reset</button></div><iframe class="component-frame" src="/preview/{name}" title="{name} live preview" loading="lazy"></iframe></section>'
  elif product=='components' and slug=='manual/grouped-remote-ranges':
   preview='<section id="live-example" class="preview-panel"><div class="preview-toolbar"><strong>Grouped remote ranges · 10,000 synthetic records</strong><a href="/grouped-range">Open example ↗</a><a href="/flutter/index.html?grouped-range">Flutter gallery ↗</a><button type="button" data-reload-preview>Reset</button></div><iframe class="component-frame" src="/grouped-range" title="Grouped remote ranges live preview" loading="lazy"></iframe></section>'
  elif product=='reports':
   preview='<section class="preview-panel topic-preview"><div class="preview-toolbar"><strong>'+html.escape(d['Title'])+' — example</strong><a href="/report-examples/index.html?topic='+slug+'">Open example ↗</a></div><iframe class="report-topic-frame" src="/report-examples/index.html?topic='+slug+'" title="'+html.escape(d['Title'],quote=True)+' working example" loading="lazy"></iframe></section>'
  content=re.sub(r'<h1([^>]*)>.*?</h1>',r'<span\1></span>',content,count=1,flags=re.S)
  page=shell(d['Title'],'<div class="docs-layout"><aside class="docs-nav"><a class="back-link" href="'+home+'">← '+title+'</a>'+links(slug)+'</aside><article class="prose">'+preview+content+'</article></div>')
  target=dest/url(slug).lstrip('/');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(page)
 if product=='components':
  page=shell('Build your next interface.','<p class="lede">Blazor and Flutter components, working examples and offline documentation.</p><div class="actions"><a class="button" href="/">Blazor gallery →</a><a class="button secondary" href="/flutter/index.html">Flutter gallery →</a></div><section><h2>Documentation & manuals</h2>'+links()+'</section>')
  (dest/'workspace.html').write_text(page)
 else:shutil.copy(dest/'guides/index.html',dest/'guides/README.html')
 (assets/'revision.json').write_text(json.dumps({'revision':revision,'product':product,'manuals':len(docs),'codeBlocks':sum((root/'server/manuals'/product/(d['Path']+'.html')).read_text().count('data-code-example') for d in docs)},indent=2))
 print(product,len(docs),'offline manuals built in',dest)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--product',choices=['components','reports'],required=True);p.add_argument('--webroot',required=True);a=p.parse_args();build(a.product,a.webroot)
