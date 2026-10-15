# 다국어 금융용어사전 r8

영어 기준 **26,245쌍·47개 대상 언어/지역 표기**를 제공합니다. 기본 자료 20,239쌍과 별도 조건부 참고팩 6,006쌍을 구분합니다. 출처별 원문을 보존하므로 수량은 고유 금융 개념 수와 다릅니다.

## 화면과 다운로드

- [웹사이트](https://simsoni7.github.io/WhatGloabalStandardsSay/)
- [이메일·오프라인용 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261015-r8/financial-dictionary-email.zip): 전체 압축 해제 → HTML 열기 → 출처 JSON 선택에서 `data/`의 JSON을 모두 선택합니다. 별도 `.js` 파일이 없으며 이메일 서비스의 첨부 허용을 보장하지는 않습니다.
- [자동 읽기 오프라인 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261015-r8/financial-dictionary.zip): 전체 압축 해제 후 HTML을 엽니다.
- [기본 데이터](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261015-r8/glossaries-data.zip) · [상업 조건 확인 기본팩](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261015-r8/commercial-language-packs.zip) · [GPL/MPL 참고팩](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261015-r8/conditional-community-language-packs.zip) · [재현 패키지](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261015-r8/what-global-standards-glossary.zip)

## 한국어로 조회

영어 원문의 한국어 표현인 `source_english_korean` 필드를 신설했습니다. 영어 표제어 7,834개 전체에 CFPD 한국어 원문 재사용 2,017개와 새 AI 번역 5,817개를 채웠으며, 이를 원문쌍 26,245개에 연결했습니다. 원래 영어·외국어 원문과 외국어 번역 승인 상태는 변경하지 않습니다. 새 한국어 표현은 금융 전문가 승인 전인 검색·독해 보조입니다.

분담 번역과 독립 AI 검수에서 목록 정렬 밀림 및 금융 의미 오류를 발견해 교정하고 최종 파일 SHA를 고정했습니다. 사람이 승인한 금융 번역 정답이라는 주장은 하지 않습니다.

## 확장 이력

Apache 금융 계정·결제 라벨 894쌍과 말레이시아 정부 MIT 금융통계 지표명 65쌍, 총 959쌍을 추가했습니다. 소프트웨어·지표의 원문 문맥과 생성 제한을 유지하며 일반 은행의 공인 용어집으로 간주하지 않습니다. 기존 CFPD 동결 원문은 변경하지 않았습니다.

기존 후보인 네팔·RBI·CBSL 등의 접근·영어 대응·재사용 권리는 별도로 조사했습니다. 권리 미확인 원문은 새 공개 패키지에서 제외했습니다. 자세한 결과는 후보 목록과 조사 보고서를 참조하세요.

## 검증과 출처

[한국어 표현 설명](KOREAN-SEARCH-AIDS.MD) · [사용 안내](FINANCIAL-DICTIONARY.MD) · [번역 커버리지](korean-label-report.json) · [화면 검증](r8-delivery-verification.jsonl) · [아시아 조사](BATCH7-ASIAN-OFFICIAL.MD)

47개 대상 언어/지역 표기 전수 선택에서 0건 언어가 없었습니다. 한국어 예금 검색과 출처별 경상계정·당좌예금계좌 검색을 확인했습니다. 추가 JSON의 한국어 검색·중복 방지·변조 차단·모바일 표시도 통과했습니다. 외부망 차단 ZIP 구성은 환경 정책상 로컬 HTTP로 제공해 검사했으며 직접 file:// 자동 탐색은 차단됩니다.

무료 예약 원출처 모니터는 별도 `glossary-source-intake` 브랜치에 변경 후보를 게시합니다. 상시 AI 의미 검수나 자동 번역 승인 작업이 아닙니다. 각 출처의 라이선스·고지 조건을 유지하며 전체 패키지에 단일 라이선스를 적용하지 않습니다.


## r8 추가

말레이시아 정부의 금융통계 메타데이터140쌍을 추가했습니다. 말레이어는205쌍이며 다른 언어의 수량은 유지됩니다. 새 영어121개 한국어 표현과 출처별 한국어141행을 보강했습니다. 같은 Current Account라도 네팔은행은 당좌예금계좌, 말레이시아 국제수지는 경상계정으로 구분합니다. 원래 영어·외국어 원문과 승인 상태는 그대로입니다.

70개 자동 테스트 및 외부망 차단 ZIP 구성의47개 언어 전수 조회·이메일 JSON읽기·한국어 문맥 검색을 통과했습니다. 원출처 예약 수집에 말레이시아 정부 저장소도 추가해4개 소스를 감시합니다. 이는 후보 수집·무결성 검사이며 금융 의미 자동 승인은 아닙니다.
