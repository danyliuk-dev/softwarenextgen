import sys,json,base64,time
from pathlib import Path
sys.path.insert(0,'/tmp/nextgen-licensing/python')
import requests,websocket
page=next(t for t in requests.get('http://127.0.0.1:9350/json/list').json() if t['type']=='page')
ws=websocket.create_connection(page['webSocketDebuggerUrl'],suppress_origin=True);n=0
def send(method,params={}):
 global n;n+=1;ws.send(json.dumps(dict(id=n,method=method,params=params)))
 while True:
  r=json.loads(ws.recv())
  if r.get('id')==n:
   assert 'error' not in r,r;return r.get('result',{})
send('Network.enable');send('Network.setExtraHTTPHeaders',{'headers':{'X-Forwarded-Proto':'https'}})
for name,value in json.loads(Path('/tmp/nextgen-licensing/browser-cookies.json').read_text()).items():send('Network.setCookie',dict(name=name,value=value,url='http://127.0.0.1:15339',path='/',secure=True,httpOnly=True))
def evaluate(js):return send('Runtime.evaluate',{'expression':js,'returnByValue':True})['result'].get('value')
def wait():time.sleep(.6)
def shot(name):Path('/tmp/nextgen-licensing/'+name+'.png').write_bytes(base64.b64decode(send('Page.captureScreenshot',{'format':'png'})['data']))
send('Emulation.setDeviceMetricsOverride',dict(width=1280,height=900,deviceScaleFactor=1,mobile=False))
send('Page.navigate',{'url':'http://127.0.0.1:15339/admin/licenses'});wait()
assert evaluate("document.querySelectorAll('.license-tabs a').length")==3
assert not evaluate("document.querySelector('.license-create').open")
evaluate("document.querySelector('.license-create summary').click()")
evaluate("""(()=>{const f=document.querySelector('form[action="/admin/licenses/customer"]');for(const [k,v] of Object.entries({first:'Browser',last:'License QA',kind:'organization',organization:'Synthetic Visual Test',email:'visual-license@example.invalid'})){f.elements[k].value=v;f.elements[k].dispatchEvent(new Event('change',{bubbles:true}));}f.requestSubmit();})()""");wait()
assert evaluate("document.body.innerText.includes('visual-license@example.invalid')")
assert not evaluate("document.querySelector('.license-create').open")
shot('compact-clients')
evaluate("[...document.querySelectorAll('.license-tabs a')].find(a=>a.href.includes('view=licenses')).click()");wait()
evaluate("document.querySelector('.license-create summary').click()")
evaluate("""(()=>{const f=document.querySelector('form[action="/admin/licenses/create"]');f.elements.user.value=[...f.elements.user.options].find(o=>o.textContent==='visual-license@example.invalid').value;f.elements.product.value='remote';f.elements.edition.value='Visual QA';f.elements.seats.value='2';f.requestSubmit();})()""");wait()
evaluate("[...document.querySelectorAll('tr')].find(r=>r.innerText.includes('visual-license@example.invalid')).querySelector('a').click()");wait()
assert evaluate("document.querySelector('h1').textContent")=='Edit license'
shot('compact-license-edit')
evaluate("""(()=>{const f=document.querySelector('form[action="/admin/licenses/change"]');f.elements.status.value='suspended';f.elements.seats.value='4';f.elements.expires.value='2027-12-31';f.requestSubmit();})()""");wait()
assert evaluate("[...document.querySelectorAll('tr')].find(r=>r.innerText.includes('visual-license@example.invalid')).innerText.includes('suspended')")
evaluate("document.querySelector('input[name=q]').value='visual-license@example.invalid';document.querySelector('.license-search').requestSubmit()");wait()
assert evaluate("document.querySelectorAll('tbody tr').length")==1
assert evaluate("document.querySelector('tbody').innerText.includes('2027-12-31')")
shot('compact-licenses')
send('Emulation.setDeviceMetricsOverride',dict(width=390,height=844,deviceScaleFactor=1,mobile=True));wait()
assert not evaluate('document.documentElement.scrollWidth>innerWidth')
shot('compact-mobile')
print('PASS visible Chrome: collapsed forms, Clients/Licenses/Devices tabs, registration, issuance, separate editing, saved status/limit/expiry, search, responsive layout')
ws.close()
