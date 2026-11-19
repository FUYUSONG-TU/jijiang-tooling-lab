"""Create relocatable ZIP with manifest; never includes reference photographs or git metadata."""
import json,hashlib,zipfile,argparse
from pathlib import Path
R=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(R.parent/'diamond-35-tool-package.zip'));args=parser.parse_args();out=Path(args.output)
files=[f for f in sorted(R.rglob('*')) if f.is_file()and'__pycache__'not in f.parts and f.name!='manifest.json'and f.suffix not in ['.blend1','.log','.zip','.pyc']]
manifest={'modelVersion':'2.0.0','professionalToolCount':1,'files':[{'path':str(f.relative_to(R)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in files]}
(R/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED)as z:
 for f in files+[R/'manifest.json']:z.write(f,Path('diamond-35')/f.relative_to(R))
with zipfile.ZipFile(out)as z:assert z.testzip()is None
print(json.dumps({'zip':str(out),'bytes':out.stat().st_size,'files':len(files)+1},ensure_ascii=False))
