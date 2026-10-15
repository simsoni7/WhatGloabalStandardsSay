"""Build static direct entry documents with content-addressed shared browser assets."""
import hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist';runtime=D/'runtime-v40';runtime.mkdir(exist_ok=True)
html=(R/'templates/page-shell.html').read_text();refs={}
scripts=re.findall(r'<script[^>]+src="([a-z-]+\.js)"[^>]*>',html)
assert scripts and scripts[0]=='route-entry.js', 'Route entry must initialize before application startup'
assert all('defer' in tag for tag in re.findall(r'<script[^>]+src=[^>]+>',html)), 'Ordered startup requires deferred scripts'
for name in re.findall(r'(?:src|href)="([a-z-]+\.(?:js|css))"',html):
 source=D/name;body=source.read_bytes();filename=f'{source.stem}-{hashlib.sha256(body).hexdigest()[:12]}{source.suffix}';(runtime/filename).write_bytes(body);refs[name]='runtime-v40/'+filename
for name,target in refs.items():html=html.replace('"'+name+'"','"'+target+'"')
# Retain old addressed assets so a previously loaded entry document remains usable.
for name in ['index.html','public-screens.html','company-capabilities.html','company-dictionary.html','references.html','manage.html','reference-compare.html','work-catalog.html','reference-flow.html']:(D/name).write_text(html)
print({'direct_pages':8,'content_addressed_assets':len(refs)})
