"""Retain legacy reproducibility and prepare full-stack static assets; never modify original data."""
from pathlib import Path
import shutil,sys
R=Path(__file__).resolve().parents[1]
mode=sys.argv[1] if len(sys.argv)>1 else 'sync'
if mode=='legacy-tests':
 # Existing financial gates intentionally consume dist/*. This compatibility surface
 # is disposable build output copied from the preserved, byte-identical source assets.
 for p in (R/'public').iterdir():
  if p.name in ('integration-data','workspace','legacy','favicon.svg'):continue
  dest=R/'dist'/p.name
  if p.is_dir():shutil.copytree(p,dest,dirs_exist_ok=True)
  elif p.is_file():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 shutil.copy2(R/'public/legacy/index.html',R/'dist/index.html')
 (R/'dist/package.json').write_text('{"type":"commonjs"}\n')
elif mode=='sync':
 for name in ('index.html','styles.css','app.js','publications.js','about.js','about.css','dictionary.js','dictionary.css','operations.js','operations.css','operations-plan.json'):
  dest=R/'public/workspace'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'integration-ui'/name,dest)
 shutil.copytree(R/'integration-data',R/'public/integration-data',dirs_exist_ok=True)
else:raise SystemExit('Use sync or legacy-tests')
print('full-stack asset preparation:',mode)
