"""Convert offline/repository manual links to their public website destinations."""
import html,re
from urllib.parse import urlsplit,parse_qs,unquote

def normalize_links(content,product):
 def link(match):
  href=html.unescape(match['href']);label=match['label'];u=urlsplit(href)
  if u.hostname in ('127.0.0.1','localhost','::1'):
   if product!='components':raise ValueError('Unmapped local documentation link: '+href)
   if u.port==5180 and re.fullmatch(r'/preview/Ng[A-Za-z0-9]+',u.path):
    name=u.path.rsplit('/',1)[1];href='/docs/components/manual/'+name+'#live-example'
   elif u.port==5180 and u.path in ('/virtual-data','/remote-range','/grouped-range'):
    href='/preview/components'+u.path
   elif u.port==5181:
    query=parse_qs(u.query,keep_blank_values=True)
    if 'preview' in query:
     name=query['preview'][0]
     if not re.fullmatch(r'Ng[A-Za-z0-9]+',name):raise ValueError(href)
     href='/docs/components/manual/'+name+'#flutter-example';label='Flutter example code'
    elif 'virtual-data' in query:href='/docs/components/manual/virtual-data#flutter';label='Flutter implementation'
    elif 'remote-range' in query:href='/docs/components/manual/remote-ranges#flutter-example';label='Flutter implementation'
    elif 'grouped-range' in query:href='/docs/components/manual/grouped-remote-ranges#flutter-example';label='Flutter implementation'
    else:raise ValueError('Unmapped Flutter link: '+href)
   else:raise ValueError('Unmapped local documentation link: '+href)
  elif u.hostname=='github.com':
   matchrepo=re.fullmatch(r'/[^/]+/(NextgenReportEngine|NextgenComponents)/blob/[^/]+/(.+\.md)',unquote(u.path))
   if matchrepo:
    target_product='reports' if matchrepo[1]=='NextgenReportEngine' else 'components';path=matchrepo[2]
    slug='overview' if path=='README.md' else path.removeprefix('docs/').removesuffix('.md').replace('README','index')
    href='/docs/'+target_product+'/'+slug+('#'+u.fragment if u.fragment else '')
  if href=='/docs/components/overview#run':href='/docs/components/manual/getting-started#run-the-included-applications'
  return '<a href="'+html.escape(href,quote=True)+'">'+label+'</a>'
 content=re.sub(r'<a\s+href=["\'](?P<href>[^"\']*)["\'][^>]*>(?P<label>.*?)</a>',link,content,flags=re.S)
 if product=='components':
  content=content.replace('The documentation launcher embeds these running examples here. Choose a framework, interact with the component, and compare it with the exact code below. Use Reload example to restore the initial state.', 'The live Blazor preview is embedded above. Use Reset to restore its initial state. Flutter implementation code is provided below; run the Flutter gallery from the installed developer workspace.')
 if product=='reports':content=content.replace('<a>Return to Studio</a>','<span>Open the installed Studio to edit your report.</span>')
 return content
