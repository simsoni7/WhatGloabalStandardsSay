"""Build the offline HTML/JSON handoff without external JavaScript files."""
from pathlib import Path
import zipfile,json
ROOT=Path(__file__).resolve().parents[1]
BLOCKED=set('ade adp apk appx appxbundle bat cab chm cmd com cpl diagcab diagcfg diagpkg dll dmg ex ex_ exe hta img ins iso isp jar jnlp js jse lib lnk mde mjs msc msi msix msixbundle msp mst nsh pif ps1 scr sct shb sys vb vbe vbs vhd vxd wsc wsf wsh xll'.split())
def build():
 original=ROOT/'dist/financial-dictionary.zip';out=ROOT/'dist/financial-dictionary-email.zip'
 catalog=json.loads((ROOT/'dist/community/catalog.json').read_text())
 core=[json.loads(line) for line in (ROOT/'dist/data/glossary_entries.jsonl').read_text().splitlines()]
 component_count=len(catalog['components']);core_count=len(core);total_count=core_count+catalog['entry_count']
 languages=set(r['target_language'] for r in core);base_languages=len(languages);all_languages=len(languages|set(catalog['counts_by_language']))
 with zipfile.ZipFile(original) as src,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dst:
  html=src.read('financial-dictionary.html').decode()
  marker='async function loadCommunity(){'
  assert html.count(marker)==1
  html=html.replace('"offline_bundle":true','"offline_bundle":true,"email_manual":true',1)
  manual_notice=f'이메일 전달용 오프라인 화면입니다. 출처 JSON 선택 버튼을 누르고 data 폴더의 JSON {component_count}개를 모두 선택하세요. 기본 {base_languages}언어에서 전체 {all_languages}언어로 확장됩니다. 한국어 표현으로도 검색할 수 있습니다.'
  html=html.replace(marker,marker+"if(DATA.email_manual){$('layerStatus').textContent="+json.dumps(manual_notice,ensure_ascii=False)+";return;}",1)
  html=html.replace("$('loadCommunity').onclick=loadCommunity;","$('loadCommunity').textContent="+json.dumps(f'출처 JSON 선택 ({component_count}개 모두)',ensure_ascii=False)+";$('loadCommunity').onclick=()=>$('importSource').click();")
  dst.writestr('financial-dictionary.html',html)
  for name in src.namelist():
   if name in ['financial-dictionary.html','README.md','OFFLINE-BUNDLE.md'] or name.startswith('community/') or Path(name).suffix.lower().lstrip('.') in BLOCKED:continue
   dst.writestr(name,src.read(name))
  catalog=json.loads((ROOT/'dist/community/catalog.json').read_text())
  for c in catalog['components']:dst.write(ROOT/'dist/community'/c['file'],'data/'+c['file'])
  dst.writestr('README.md',f'# 오프라인 이메일 전달용 금융용어사전\n\nZIP 전체를 풀고 financial-dictionary.html을 엽니다. 출처 JSON 선택 버튼에서 data 폴더의 JSON {component_count}개를 모두 선택하면 {total_count:,}쌍·{all_languages}언어를 인터넷 없이 조회합니다. 선택 전에는 기본 {core_count:,}쌍·{base_languages}언어만 제공됩니다. 한국어 표현·영어·외국어로 검색할 수 있습니다. 한국어 표현은 영어 원문의 이해·검색을 돕는 별도 보조 번역이며 외국어 번역의 승인 결과가 아닙니다. 자료는 브라우저에서만 읽고 전송하지 않습니다. 별도 .js 파일이 없으며, 각 원출처의 라이선스와 대응 소스는 community-components/에 보존합니다. 메일 서비스의 실제 허용 여부는 보장하지 않습니다.\n')
  dst.writestr('START-HERE.txt',f'1. Extract the entire ZIP.\n2. Open financial-dictionary.html in a browser.\n3. Click the source JSON selection button and select all {component_count} JSON files in data/.\n4. All {total_count:,} observations / {all_languages} target languages are available without internet.\n5. Search using Korean expressions, English, or target-language text. Korean expressions are separate reading/search aids, not approval of the original translations.\n\nWithout importing, the {core_count:,} core rows / {base_languages} languages remain available. File reading happens in your browser; no upload or account is needed. Each source retains its original license; corresponding source and notices are under community-components/. No separate .js files are included. Email acceptance remains subject to the provider and organization policy.\n')

 with zipfile.ZipFile(out) as z:assert not any(Path(n).suffix.lower().lstrip('.') in BLOCKED for n in z.namelist());assert z.testzip() is None
 print(out)
if __name__=='__main__':build()
