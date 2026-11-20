#!/usr/bin/env python3
import json,hashlib,requests,os
from pathlib import Path
qa=json.loads(Path('/root/nextgen-qa.json').read_text());items=json.loads(Path('/tmp/nextgen-releases.json').read_text())
s=requests.Session();s.cookies.update(qa['cookies']);s.headers['X-Forwarded-Proto']='https'
for item in items:
 if os.environ.get('VERIFY_PRODUCT') and item['product']!=os.environ['VERIFY_PRODUCT']:continue
 url='http://127.0.0.1:5338/download/'+item['id']
 r=s.get(url,headers={'Range':'bytes=0-31'},allow_redirects=False,timeout=30);assert r.status_code==206,(item['filename'],r.status_code);assert len(r.content)==32
 with s.get(url,stream=True,allow_redirects=False,timeout=120) as r:
  assert r.status_code==200,(item['filename'],r.status_code);assert 'attachment' in r.headers.get('Content-Disposition','')
  h=hashlib.sha256();size=0
  for data in r.iter_content(1024*1024):h.update(data);size+=len(data)
 assert size==item['size'],item['filename'];assert h.hexdigest().upper()==item['sha256'],item['filename']
 r=requests.get(url,allow_redirects=False);assert r.status_code==302
 print('PASS private download + Range + full SHA-256:',item['filename'],size,flush=True)
