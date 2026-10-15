"""Build the offline HTML/JSON handoff without external JavaScript files."""
from pathlib import Path
import zipfile,json
ROOT=Path(__file__).resolve().parents[1]
BLOCKED=set('ade adp apk appx appxbundle bat cab chm cmd com cpl diagcab diagcfg diagpkg dll dmg ex ex_ exe hta img ins iso isp jar jnlp js jse lib lnk mde mjs msc msi msix msixbundle msp mst nsh pif ps1 scr sct shb sys vb vbe vbs vhd vxd wsc wsf wsh xll'.split())
def build():
 original=ROOT/'dist/financial-dictionary.zip';out=ROOT/'dist/financial-dictionary-email.zip'
 with zipfile.ZipFile(original) as src,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dst:
  html=src.read('financial-dictionary.html').decode()
  marker='async function loadCommunity(){'
  assert html.count(marker)==1
  html=html.replace('"offline_bundle":true','"offline_bundle":true,"email_manual":true',1)
  html=html.replace(marker,marker+"if(DATA.email_manual){$('layerStatus').textContent='이메일 전달용 오프라인 화면입니다. 출처 JSON 선택 버튼을 누르고 data 폴더의 JSON 3개를 모두 선택하세요. 기본 36언어에서 전체 45언어로 확장됩니다.';return;}",1)
  html=html.replace("$('loadCommunity').onclick=loadCommunity;","$('loadCommunity').textContent='출처 JSON 선택 (3개 모두)';$('loadCommunity').onclick=()=>$('importSource').click();")
  dst.writestr('financial-dictionary.html',html)
  for name in src.namelist():
   if name in ['financial-dictionary.html','README.md','OFFLINE-BUNDLE.md'] or name.startswith('community/') or Path(name).suffix.lower().lstrip('.') in BLOCKED:continue
   dst.writestr(name,src.read(name))
  catalog=json.loads((ROOT/'dist/community/catalog.json').read_text())
  for c in catalog['components']:dst.write(ROOT/'dist/community'/c['file'],'data/'+c['file'])
  dst.writestr('README.md','# 오프라인 이메일 전달용 금융용어사전\n\nZIP 전체를 풀고 financial-dictionary.html을 엽니다. 출처 JSON 선택 버튼에서 data 폴더의 JSON 3개를 모두 선택하면25,146쌍·45언어를 인터넷 없이 조회합니다. 선택 전에는 기본19,140쌍·36언어만 제공됩니다. 자료는 브라우저에서만 읽고 전송하지 않습니다. 별도 .js 파일이 없으며, 각 원출처의 라이선스와 대응 소스는 community-components/에 보존합니다. 메일 서비스의 실제 허용 여부는 보장하지 않습니다.\n')
  dst.writestr('START-HERE.txt','1. Extract the entire ZIP.\n2. Open financial-dictionary.html in a browser.\n3. Click the source JSON selection button and select all THREE JSON files in data/.\n4. All 25,146 observations / 45 target languages are available without internet.\n\nWithout importing, the 19,140 core rows / 36 languages remain available. File reading happens in your browser; no upload or account is needed. Each source retains its original license; corresponding source and notices are under community-components/. No separate .js files are included. Email acceptance remains subject to the provider and organization policy.\n')
 with zipfile.ZipFile(out) as z:assert not any(Path(n).suffix.lower().lstrip('.') in BLOCKED for n in z.namelist());assert z.testzip() is None
 print(out)
if __name__=='__main__':build()
