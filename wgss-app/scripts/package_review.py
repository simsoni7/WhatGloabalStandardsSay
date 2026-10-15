from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1];D=R/'dist/data';report=json.loads((D/'validation-report.json').read_text());version='.'.join(report['version'].split('.')[:2])
lines=[f'# WGSS v{version} 검증 결과','',f"실행: {report['run_at']}",'','## 자동 검사',f"- 데이터 구조: {report['schema_passed']}/{report['schema_checks']}",f"- 경계 상황: {report['boundary_passed']}/{report['boundary_checks']}",f"- 검색 후보: {report['search_passed']}/{report['search_checks']}",f"- 조건 호환: {report['compatibility_passed']}/{report['compatibility_checks']}",f"- 화면 설계 경계: {report.get('design_passed',0)}/{report.get('design_checks',0)}"]
iso=json.loads((D/'iso-validation-report.json').read_text());lines += [f"- ISO 원본·연결 검사: {iso['checks']}개 / {iso['status']}"]
b=report.get('browser',{});mb=report.get('model_browser',{});lines += [f"- 업무 개념 브라우저: {mb.get('checks',0)}개 / {mb.get('status','not_run')}"]
gw=report.get('bedrock',{});models=', '.join(gw.get('tested_models',[])) or '없음'
wb=report.get('workbench_browser',{})
lines += [f"- 실제 브라우저: {b.get('checks',0)}개 / {b.get('status','not_run')}",f"- 화면 설계 브라우저: {wb.get('checks',0)}개 / {wb.get('status','not_run')}",f"- 브라우저 WebMCP: {b.get('native_webmcp','not_run')}",'','## 아직 측정하지 않은 것','- 독립 검토자 분류 일치율','- 현지 금융 전문가 검토','- 기존 업무 대비 작업 시간 절감','- 실제 금융 앱의 화면 및 버전 일치','','## 모델 검토',f"Frontier Chat Completions 연결 상태: {gw.get('status','not_run')}. 성공 호출 {gw.get('successful_calls',0)}회. 확인 모델: {models}.",'Sonnet 분류와 Opus 경계 검토는 AI 보조 검토이며 독립 사람 검토가 아니다. 출력은 자동 적용하지 않는다. 키는 저장하거나 출력하지 않았다.','','## 해석 제한','위 수치는 작성자가 구성한 회귀·구조·동작 시험의 통과 수다. 시장 전체 정확도, 독립 검증, 금융 규제 적합성, 업무 시간 절감의 증거가 아니다.']
(R/'docs/validation-report.md').write_text('\n'.join(lines)+'\n')
package=D/f'wgss-design-v{version}.zip'
files=[R/'README.md',*sorted((R/'docs').glob('*.md')),*sorted(D.glob('*.json')),*sorted((R/'dist').glob('*.html')),*sorted((R/'dist').glob('*.css')),*sorted((R/'dist').glob('*.js')),*sorted((R/'research').glob('*.csv')),*sorted((R/'research').glob('agent-*')),*sorted((R/'research').glob('v04-*.md')),*sorted((R/'research').glob('v04-*.json')),R/'research/bedrock-status.json',*sorted((R/'scripts').glob('*.py')),*sorted((R/'tests').glob('*'))]
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
 for f in files:
  if f.is_file():z.write(f,str(f.relative_to(R)))
print(f'Packaged {len(files)} files; {package.stat().st_size} bytes')
