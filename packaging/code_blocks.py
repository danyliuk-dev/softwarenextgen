"""Render readable, self-contained code examples without a client-side CDN."""
import html,json,re
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexer import Lexer
from pygments.token import Text

class RazorLexer(Lexer):
    name='Razor'
    def get_tokens_unprocessed(self,text):
        # HTML markup and C# code/directives use their respective lexers.
        csharp=get_lexer_by_name('csharp',stripnl=False,ensurenl=False)
        markup=get_lexer_by_name('html',stripnl=False,ensurenl=False)
        position=0
        for match in re.finditer(r'(?m)^\s*@(code\s*\{|functions\s*\{|using\b[^\n]*|inject\b[^\n]*|page\b[^\n]*|namespace\b[^\n]*|inherits\b[^\n]*|implements\b[^\n]*)',text):
            if match.start()<position:continue
            for offset,kind,value in markup.get_tokens_unprocessed(text[position:match.start()]):yield position+offset,kind,value
            end=match.end()
            if re.match(r'\s*@(code|functions)\s*\{',match[0]):
                # Balance braces using C# punctuation only, excluding strings/comments.
                depth=0
                for offset,kind,value in csharp.get_tokens_unprocessed(text[match.start():]):
                    if str(kind).startswith('Token.Punctuation'):
                        depth+=value.count('{')-value.count('}')
                        if depth==0 and '}' in value:end=match.start()+offset+len(value);break
                else:end=len(text)
            for offset,kind,value in csharp.get_tokens_unprocessed(text[match.start():end]):yield match.start()+offset,kind,value
            position=end
        for offset,kind,value in markup.get_tokens_unprocessed(text[position:]):yield position+offset,kind,value

LABELS={'razor':'Razor / Blazor','csharp':'C#','dart':'Dart / Flutter','ts':'TypeScript','json':'JSON','bash':'Bash','sh':'Shell','yaml':'YAML','html':'HTML','sql':'SQL','text':'Text'}
formatter=HtmlFormatter(nowrap=True)

def format_source(source,language):
    source=source.replace('\r\n','\n').strip('\n')
    if language=='json':
        try:source=json.dumps(json.loads(source),indent=2,ensure_ascii=False)
        except (ValueError,TypeError):pass
    return source

def render_code_blocks(content):
    # Unwrap our own output before regeneration so the build is idempotent.
    content=re.sub(r'<figure class="code-example".*?<pre[^>]*>(<code.*?</code>)</pre></figure>',r'<pre>\1</pre>',content,flags=re.S)
    def bare(match):
        body=match[1]
        if re.match(r"\s*<code\b",body):return match[0]
        plain=html.unescape(body).lstrip()
        language='text'
        if plain.startswith(('{','[')):
            try:json.loads(plain);language='json'
            except ValueError:pass
        elif re.search(r'(?:export )?function \w+\(',plain):language='ts'
        elif re.search(r'(?m)^(?:npm |dotnet |NEXTGEN_.*=)',plain):language='bash'
        return '<pre><code class="language-'+language+'">'+body+'</code></pre>'
    content=re.sub(r'<pre[^>]*>(.*?)</pre>',bare,content,flags=re.S)
    def render(match):
        language=re.search(r'language-([\w+-]+)',match['attrs']);language=language[1] if language else 'text'
        source=html.unescape(re.sub(r'</?span\b[^>]*>','',match['source']))
        source=format_source(source,language)
        lexer=RazorLexer(stripnl=False,ensurenl=False) if language=='razor' else get_lexer_by_name(language,stripnl=False,ensurenl=False)
        colored=highlight(source,lexer,formatter).rstrip('\n')
        lines=colored.split('\n')
        numbered='\n'.join('<span class="code-line" data-line="'+str(i+1)+'">'+line+'</span>' for i,line in enumerate(lines))
        label=LABELS.get(language,language)
        return '<figure class="code-example" data-code-example><figcaption><span class="code-language">'+html.escape(label)+'</span><div class="code-actions"><button type="button" data-code-wrap aria-pressed="false">Wrap lines</button><button type="button" data-code-copy>Copy code</button><span class="sr-only" data-code-status aria-live="polite"></span></div></figcaption><pre tabindex="0" aria-label="'+html.escape(label)+' code example"><code class="language-'+language+'">'+numbered+'</code></pre></figure>'
    return re.sub(r'<pre[^>]*>\s*<code(?P<attrs>[^>]*)>(?P<source>.*?)</code>\s*</pre>',render,content,flags=re.S)
