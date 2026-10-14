# 다국어 금융용어사전 — r5

영어를 기준으로 대상45개 언어의 원문 관측25,146쌍을 조회합니다. 기본 사전19,140쌍·36언어·9소스와 별도 조건부 참고팩6,006쌍·20언어·3소스를 구분합니다. 영어는 대상 언어 수에서 제외합니다. 중복 표제어의 출처별 레코드도 원문 근거를 보존하므로 숫자는 고유 금융 개념 수가 아닙니다.

검색, 한국어 언어명 필터, 출처·자료종류·이용조건·기본/조건부자료 필터, 통계와 출처 설명만 제공합니다. 검토 입력·판정·메모·승인 기능은 없습니다.

## 보기와 다운로드

공유화면: https://htmlpreview.github.io/?https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261014-r5/index.html

HTML ZIP을 풀어 financial-dictionary.html을 열면 기본 사전을 오프라인 조회할 수 있습니다. 웹 화면은 조건부 JSON을 별도 읽습니다. 오프라인에서는 conditional-community-language-packs.zip을 풀고 community-components/*.json을 화면의 자료 읽기로 선택합니다. 카탈로그 JSON은 선택하지 않습니다. SHA·형식·출처를 확인하고 중복 읽기를 차단합니다. 이 입력은 번역 검토나 승인 작업이 아닙니다.

## 출처와 도입

기존 동결 CFPD10,089쌍은 변경하지 않았습니다. 몽골은행3,644, 네팔은행171, CFPB 송금135, 캐나다정부117, EU CPV1,958, Unicode CLDR743에 CFPB 송금 영수증60 및 Apache OFBiz 회계 원문2,223을 추가했습니다. 원본 PDF/XML/JSON/PO·커밋·동일 키·원문값·라이선스·SHA를 보존하고 독립 AI 대조를 수행했습니다. 원문 관측과 전문가 승인 번역은 다른 필드이며 승인 번역은 모두 null입니다.

기본 상업 조건 확인 자료는15,325쌍입니다. 몽골·네팔 기존 자료3,815쌍은 재배포 권리 미확인으로 해당 상업팩에서 제외합니다. Apache2·Unicode3·MIT·CC BY 등 각 출처의 고지 조건을 유지합니다.

GnuCash1,437(GPL2/3), Mifos community-app3,642(MPL2), Mifos mobile927(MPL2)은 별도 참고팩입니다. 상업 이용은 허용되지만 copyleft·고지·대응 원문 제공 조건이 있습니다. 기본 JSONL/CSV/API와 상업팩에는 섞지 않습니다. 조건부 자료 본문은 기본 HTML에도 내장하지 않습니다.

## 금융 의미의 한계

공식 프로젝트의 동일 키는 올바른 금융 번역을 보장하지 않습니다. Mifos mobile974개 관측 중 Principal→교장/이사, Interest→관심, Outstanding→탁월한 등47개 의미 의심 후보는 도입에서 제외했습니다. 다른 소프트웨어 자료에는 알려진 의미 위험을 주석으로 표시했습니다. 모든 소프트웨어 번역은 기본 자동생성 근거에서 차단합니다. 통과는 원출처 정합성 확인이지 전문가 정확성 승인이나 정답 벤치마크가 아닙니다.

## 재현

scripts/build_dictionary_html.py, export_community_sources.py 및 각 collect_*.py로 재현합니다. 기본 데이터 스냅샷 SHA와 조건부 파일 SHA를 별도 표시합니다. 무료 예약 원출처 모니터는 후보만 수집하며 의미 승인·자동 도입을 하지 않습니다. docs/source-monitoring.md를 참조하세요.
