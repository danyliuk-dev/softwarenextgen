#!/usr/bin/env python3
import shutil,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1];stage=root/'artifacts/components-source';web=stage/'examples/BlazorGallery/wwwroot';web.mkdir(parents=True,exist_ok=True)
shutil.copytree(root.parent/'NextgenComponents/examples/flutter_gallery/build/web',web/'flutter',dirs_exist_ok=True)
p=web/'flutter/index.html';s=p.read_text();s=re.sub(r'<base href="[^"]*"', '<base href="/flutter/index.html"',s);p.write_text(s)
from importlib.machinery import SourceFileLoader
SourceFileLoader('offline_docs',str(root/'packaging/build-offline-docs.py')).load_module().build('components',web)
shutil.copytree(root/'artifacts/installed-sdk/components/SDK',stage/'artifacts/installed-sdk/SDK',dirs_exist_ok=True)
desktop=stage/'desktop';desktop.mkdir(exist_ok=True)
(desktop/'package.json').write_text(json.dumps({'name':'nextgen-components-desktop','productName':'NextgenComponents','version':'0.74.1','private':True,'description':'Blazor and Flutter components, demos and offline manuals','author':'Software Next Generation','main':'main.cjs','devDependencies':{'electron':'44.10.0','electron-builder':'26.18.0'}},indent=2))
shutil.copy(root/'packaging/components-main.cjs',desktop/'main.cjs');shutil.copy(root/'packaging/components-builder.cjs',desktop/'electron-builder.cjs');shutil.copy(root/'packaging/components-icon.png',desktop/'icon.png')
print('Component desktop source prepared')
