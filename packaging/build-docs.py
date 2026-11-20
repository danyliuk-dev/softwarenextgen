#!/usr/bin/env python3
import json,re,html
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
from markdown_it import MarkdownIt
from doc_links import normalize_links
from code_blocks import render_code_blocks
root=Path(__file__).resolve().parents[1]
repos={'components':root.parent/'NextgenComponents','reports':root.parent/'NextgenReportEngine'}
output=root/'server/manuals'
for product,repo in repos.items():
    sources=[repo/'README.md']
    if product=='components': sources+=sorted((repo/'docs/manual').rglob('*.md'))
    else: sources+=[p for p in sorted((repo/'docs').glob('*.md')) if p.stem not in {'verification','roadmap','desktop-releases','server-operations'}]
    sources+=[root/'docs/installing.md']
    mapping={p.resolve():('overview' if p==repo/'README.md' else 'installation' if p==root/'docs/installing.md' else str(p.relative_to(repo/'docs').with_suffix('')).replace('README','index')) for p in sources}
    dest=output/product;dest.mkdir(parents=True,exist_ok=True);index=[]
    for source in sources:
        content=source.read_text()
        if product=='components' and source==repo/'README.md':content=(root/'docs/components-overview.md').read_text()
        # Distribution manuals describe installed products. Keep repository build
        # instructions out of public/offline guides on every regeneration.
        override=root/'docs/products'/product/(mapping[source.resolve()]+'.md')
        if override.exists():content=override.read_text()
        content=content.replace('API declarations are generated from current source. Curated examples and behavior live in `scripts/manual_content.py`; regenerate with `python3 scripts/generate_manual.py`.', 'Use the installed SDK and the Getting started guide to add this component to your application.')
        content=content.replace('this is not Telerik API, theme or pixel compatibility.','API and theme compatibility with other libraries is not claimed.')
        content=content.replace("preserving Nextgen's selection emphasis rather than copying Telerik defaults.","preserving Nextgen's selection emphasis.")
        content=re.sub(r'https?://[^\s)<>]*?(?:telerik|stimulsoft)[^\s)<>]*','#',content,flags=re.I)
        content=re.sub(r'(?i)telerik|stimulsoft','third-party',content)
        md=MarkdownIt('commonmark',{'html':False}).enable('table');tokens=md.parse(content);slug=mapping[source.resolve()];seen={}
        for i,t in enumerate(tokens):
            if t.type=='heading_open':
                text=tokens[i+1].content;anchor=re.sub(r'[^\w\s-]','',text.lower());anchor=re.sub(r'\s+','-',anchor);n=seen.get(anchor,0);seen[anchor]=n+1;t.attrSet('id',anchor+(f'-{n}' if n else ''))
            if t.children:
                disabled=[]
                for child in t.children:
                    if child.type=='link_open':
                        href=child.attrGet('href') or '';u=urlsplit(href);valid=True
                        if not u.scheme and u.path and not u.path.startswith('/docs/'):
                            target=(source.parent/unquote(u.path)).resolve()
                            if target in mapping:child.attrSet('href','/docs/'+product+'/'+mapping[target]+('#'+u.fragment if u.fragment else ''))
                            else:valid=False
                        elif u.scheme and u.scheme not in ('https','http','mailto'):valid=False
                        disabled.append(not valid)
                        if not valid:child.tag='span';child.attrs={}
                    elif child.type=='link_close' and disabled and disabled.pop():child.tag='span'
                    elif child.type=='image':child.type='text';child.content='[Illustration: '+child.content+']';child.children=None
        title=next((tokens[i+1].content for i,t in enumerate(tokens[:-1]) if t.type=='heading_open'),'Documentation')
        title=re.sub(r'[`*_]','',title)
        rendered=md.renderer.render(tokens,md.options,{})
        if '<h1>' in content and source.name=='report-authoring-manual.md':
            class SafeManual(HTMLParser):
                allowed=set('a p h1 h2 h3 h4 h5 h6 div section ul ol li table thead tbody tr th td pre code strong em span br hr blockquote details summary dl dt dd kbd sup'.split())
                def __init__(self):super().__init__(convert_charrefs=True);self.output=[];self.skip=0
                def handle_starttag(self,tag,attrs):
                    if tag in ('script','style'):self.skip+=1;return
                    if self.skip or tag not in self.allowed:return
                    clean=[]
                    for key,value in attrs:
                        if key in ('id','class'):clean.append((key,value))
                        if tag=='a' and key=='href':
                            u=urlsplit(value)
                            if value.startswith('#'):clean.append((key,value))
                            elif not u.scheme and u.path.startswith('/docs/'):
                                clean.append((key,value))
                            elif not u.scheme:
                                target=(source.parent/unquote(u.path)).resolve()
                                if target in mapping:clean.append((key,'/docs/'+product+'/'+mapping[target]+('#'+u.fragment if u.fragment else '')))
                            elif u.scheme=='https' and u.hostname not in ('127.0.0.1','localhost'):clean.append((key,value))
                    self.output.append('<'+tag+''.join(' '+k+'="'+html.escape(v or '',quote=True)+'"' for k,v in clean)+'>')
                def handle_endtag(self,tag):
                    if tag in ('script','style'):self.skip=max(0,self.skip-1);return
                    if not self.skip and tag in self.allowed:self.output.append('</'+tag+'>')
                def handle_data(self,data):
                    if not self.skip:self.output.append(html.escape(data))
            parser=SafeManual();parser.feed(content);rendered=''.join(parser.output)
            title=html.unescape(re.sub('<[^>]+>','',re.search(r'<h1>(.*?)</h1>',content,re.S)[1]))
        path=dest/(slug+'.html');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(render_code_blocks(normalize_links(rendered,product)))
        index.append({'Title':title,'Path':slug})
    (dest/'index.json').write_text(json.dumps(index,indent=2))
    print(product,len(index),'documents')

# Preserve the Remote distribution guides on every documentation rebuild.
import subprocess,sys
subprocess.run([sys.executable,str(root/'packaging/build-remote-docs.py')],check=True)
