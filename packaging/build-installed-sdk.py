#!/usr/bin/env python3
"""Build redistributable SDKs in an isolated staging tree, never in product checkouts."""
import argparse, json, shutil, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=root/'artifacts/installed-sdk');p.add_argument('--product',choices=['components','reports']);a=p.parse_args()
for product,repo,projects,version,flutter in [
 ('components','NextgenComponents',['NextgenComponents.Blazor'],'0.74.1','nextgen_components'),
 ('reports','NextgenReportEngine',['NextgenReports.Client','NextgenReports.Blazor'],'0.2.1','nextgen_reports')]:
 if a.product and product!=a.product:continue
 source=root.parent/repo;stage=a.output/product/'build';sdk=a.output/product/'SDK';stage.mkdir(parents=True,exist_ok=True)
 shutil.copy2(source/'Directory.Build.props',stage/'Directory.Build.props')
 for project in projects:
  shutil.copytree(source/'src'/project,stage/'src'/project,dirs_exist_ok=True,ignore=shutil.ignore_patterns('bin','obj'))
 for project in projects:
  subprocess.run(['dotnet','pack',str(stage/'src'/project/(project+'.csproj')),'-c','Release','-o',str(sdk/'NuGet'),'-p:PackageVersion='+version,'-p:Version='+version],check=True)
  for old in (sdk/'NuGet').glob(project+'.*.nupkg'):
   if old.name!=project+'.'+version+'.nupkg':old.unlink()
 shutil.copytree(source/'packages'/flutter,sdk/'Flutter'/flutter,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.dart_tool','build','.git','pubspec.lock'))
 if product=='reports':
  (sdk/'tools').mkdir(exist_ok=True)
  for name in ['report-tool.py','import-delimited.py','import-xlsx.py','http-source-fixture.py']:
   shutil.copy2(source/'scripts'/name,sdk/'tools'/name)
  shutil.copytree(source/'samples',sdk/'samples',dirs_exist_ok=True)
  shutil.copy2(source/'THIRD-PARTY-NOTICES.md',sdk/'THIRD-PARTY-NOTICES.md')
 (sdk/'Flutter'/flutter/'README.md').write_text('# '+flutter+'\n\nCopy this directory into your application vendor folder and add a path dependency in pubspec.yaml. Run flutter pub get in your application. See https://softwarenextgen.com/docs/'+product+('/flutter-integration' if product=='reports' else '/manual/getting-started')+' or the installed offline manual for complete examples.\n')
 (sdk/'README.txt').write_text('Installed SDK\n\nNuGet/: local package feed for .NET 10 applications.\nFlutter/'+flutter+'/: copy into your application vendor folder and add a path dependency.\nSee the installed Developer guide / Getting started manual for complete setup.\nNo product repository or library build is required.\n')
 (sdk/'manifest.json').write_text(json.dumps({'product':product,'version':version,'packages':[f.name for f in (sdk/'NuGet').glob('*.nupkg')],'flutter':flutter},indent=2))
 print('Prepared',sdk)
