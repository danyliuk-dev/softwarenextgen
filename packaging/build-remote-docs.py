#!/usr/bin/env python3
"""Render the public and offline Nextgen Remote user guides."""
from pathlib import Path
import json,re,html
from markdown_it import MarkdownIt
root=Path(__file__).resolve().parents[1]
public=root/'server/manuals/remote';offline=root/'artifacts/remote-020/offline-docs'
public.mkdir(parents=True,exist_ok=True);offline.mkdir(parents=True,exist_ok=True)
index=[]
for slug in ['overview','installation','getting-started','permissions']:
    md=MarkdownIt('commonmark',{'html':False});tokens=md.parse((root/'docs/products/remote'/(slug+'.md')).read_text())
    for i,t in enumerate(tokens):
        if t.type=='heading_open':t.attrSet('id',re.sub(r'\s+','-',re.sub(r'[^\w\s-]','',tokens[i+1].content.lower())))
    title=tokens[1].content;body=md.renderer.render(tokens,md.options,{})
    (public/(slug+'.html')).write_text(body);index.append({'Title':title,'Path':slug})
    local=re.sub(r'/docs/remote/([a-z-]+)',r'\1.html',body).replace('href="/products/remote','href="https://softwarenextgen.com/products/remote')
    nav=' · '.join('<a href="'+x+'.html">'+html.escape(y)+'</a>' for x,y in [('overview','Overview'),('installation','Install'),('getting-started','Connect'),('permissions','Permissions')])
    (offline/(slug+'.html')).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{max-width:850px;margin:40px auto;padding:0 22px;font:16px/1.7 system-ui;color:#263d37}a{color:#295e52}nav{border-bottom:1px solid #ddd;padding-bottom:20px}h1{line-height:1.2}code{overflow-wrap:anywhere}</style><nav>'+nav+'</nav><main>'+local+'</main></html>')
(public/'index.json').write_text(json.dumps(index,indent=2)+'\n')
(offline/'index.html').write_text((offline/'overview.html').read_text())
print('Rendered four Remote public guides and offline HTML manual')
