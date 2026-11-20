from pathlib import Path
from html.parser import HTMLParser
import sys,re,json
from markdown_it import MarkdownIt
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'packaging'))
from code_blocks import render_code_blocks,format_source
class Code(HTMLParser):
 def __init__(self,source):super().__init__();self.blocks=[];self.active=False;self.pre=False;self.feed(source)
 def handle_starttag(self,tag,attrs):
  if tag=='pre':self.pre=True;self.active=True;self.blocks.append('')
  if tag=='code' and self.pre:self.active=True
 def handle_endtag(self,tag):
  if tag=='code':self.active=False
  if tag=='pre':self.pre=False;self.active=False
 def handle_data(self,data):
  if self.active:self.blocks[-1]+=data
count=0;languages=set()
for p in (root/'server/manuals').rglob('*.html'):
 source=p.read_text();blocks=Code(source).blocks;count+=len(blocks)
 assert source.count('data-code-example')==len(blocks)==len(re.findall(r'<pre\b',source)),p
 assert render_code_blocks(source)==source,('not idempotent',p)
 languages.update(re.findall(r'<code class="language-([^\"]+)"',source))
 baseline=root/'artifacts/site-1.0.5/manuals'/p.relative_to(root/'server/manuals')
 override=root/"docs/products"/p.relative_to(root/"server/manuals").with_suffix(".md")
 if p.parent.name=='manual' and p.parent.parent.name=='components' and not override.exists():
  # API declarations evolve with each library release. Compare with the current
  # Markdown source, not the declarations captured in a historical website build.
  current=root.parent/'NextgenComponents/docs/manual'/p.with_suffix('.md').name
  text=re.sub(r'(?i)telerik|stimulsoft','third-party',current.read_text())
  fences=[t for t in MarkdownIt('commonmark').parse(text) if t.type=='fence']
  expected=[format_source(t.content,t.info.strip()) for t in fences]
  assert blocks==expected,(p,'current manual code changed during rendering')
 elif baseline.exists() and not override.exists() and p.name!="installation.html":
  original=Code(baseline.read_text()).blocks
  assert len(original)==len(blocks),p
  for before,after in zip(original,blocks):
   if before.strip('\n').replace('\r\n','\n')!=after:
    assert json.loads(before)==json.loads(after),(p,'code changed')
assert {'razor','dart','csharp','ts','json','bash','sql'}<=languages
sample='<pre><code class="language-html">&lt;script&gt;alert(&quot;test&quot;)&lt;/script&gt;</code></pre>'
rendered=render_code_blocks(sample);assert '<script>' not in rendered;assert Code(rendered).blocks==Code(sample).blocks
print(f'PASS: {count} code blocks; {len(languages)} language labels; content preserved; highlighting is idempotent and HTML remains escaped')
