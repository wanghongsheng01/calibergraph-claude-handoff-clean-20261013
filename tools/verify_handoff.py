"""Offline integrity and syntax audit only. Never import or run experiment code."""
import argparse,ast,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args();root=a.root.resolve()
manifest=root/'MANIFEST.sha256';errors=[];checked=0
for line in manifest.read_text().splitlines():
 h,n=line.split('  ',1);f=root/n
 if Path(n).is_absolute() or '..' in Path(n).parts:errors.append(['unsafe',n]);continue
 if not f.is_file():errors.append(['missing',n]);continue
 if hashlib.sha256(f.read_bytes()).hexdigest()!=h:errors.append(['hash',n])
 checked+=1
syntax=[]
for f in root.rglob('*.py'):
 try:ast.parse(f.read_text(),filename=str(f))
 except (SyntaxError,UnicodeDecodeError) as e:syntax.append([str(f.relative_to(root)),str(e)])
print(json.dumps({'checked':checked,'errors':errors,'syntax_errors':syntax,'SQL_or_solver_executed':False},indent=2))
raise SystemExit(bool(errors or syntax))
