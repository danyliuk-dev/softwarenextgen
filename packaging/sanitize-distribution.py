#!/usr/bin/env python3
"""Remove competitor references from this distribution's user-facing material."""
from pathlib import Path
import re,sys,gzip
for arg in sys.argv[1:]:
 root=Path(arg);count=0
 for p in root.rglob('*'):
  if not p.is_file() or 'node_modules' in p.parts or p.suffix.lower() not in ('.html','.md','.json','.txt','.razor','.js','.css'):continue
  try:s=p.read_text()
  except (UnicodeError,OSError):continue
  if not re.search(r'telerik|stimulsoft',s,re.I):continue
  s=re.sub(r'https?://[^\s<>"\)\]]*(?:telerik|stimulsoft)[^\s<>"\)\]]*','#',s,flags=re.I)
  s=re.sub(r'(?i)telerik|stimulsoft','third-party',s)
  p.write_text(s);count+=1
  for ext in ('.gz','.br'):
   compressed=Path(str(p)+ext)
   if compressed.exists():compressed.unlink()
 print(root,'updated',count,'text files')
