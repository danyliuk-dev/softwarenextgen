#!/usr/bin/env python3
"""Apply a verified docs/SDK overlay to a copied, unpacked native app."""
from pathlib import Path
import argparse,shutil,subprocess
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('product',choices=['components','reports']);p.add_argument('resources',type=Path);a=p.parse_args()
assert (a.resources/'server').is_dir(),a.resources
sdk=a.resources/'SDK'
if sdk.exists():shutil.rmtree(sdk)
shutil.copytree(root/'artifacts/installed-sdk'/a.product/'SDK',sdk)
subprocess.run(['python3',str(root/'packaging/apply-offline-docs.py'),str(root/'artifacts/offline-docs'/a.product),str(a.resources/'server/wwwroot')],check=True)
# Retain the SDK manual entry point, without obsolete repository Markdown copies.
(sdk/'README.txt').write_text((sdk/'README.txt').read_text()+'\nOffline manuals are available in the application Help / Workspace menu.\n')
