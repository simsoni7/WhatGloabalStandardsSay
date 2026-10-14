# 금융 언어팩 다운로드

## 스키마 v2: 출처 표기와 승인된 번역 분리

통합 JSONL·CSV와 API는 source_english/source_target을 출처의 표기로 보존합니다. alignment_status는 출처 연결이고 equivalence_status는 의미 검토 상태입니다. approved_translation은 모든 레코드에서 null입니다. 원문 인용은 source_quoted_text로 반환하며 승인된 번역처럼 반환하지 않습니다.

원본 cfpd v1 및 수집 원자료는 변경하지 않았습니다. 304번 Interest Rate/Хүү는 원문 정의 불일치 의심으로 표시했고 733/737/3377과 함께 검토 대상으로 보존했습니다. 자동 수정·개념 병합은 하지 않았습니다. [스키마 및 API 변경 안내](INTEGRATION-V2.md) · [전처리 보고서](integration-report.json).



## 권장: 상업 이용 조건 확인 데이터

[상업 조건 확인 언어팩 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/commercial-language-packs.zip): 29개 대상언어, 영어–대상언어 12,249쌍. CFPB 자체제작 공개영역 자료, 캐나다 정부 MIT 자료, EU CC BY 4.0 자료입니다. 각 출처의 저작권·라이선스·출처표시 조건을 보존해야 합니다. 상업 허용이 전문가 번역검수를 뜻하지는 않습니다.

## 전체 자료와 실행 패키지

- [전체 참조 데이터 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/glossaries-data.zip): 31개 대상언어, 16,064쌍. 기존 몽골·네팔 자료는 상업 재배포조건 미확인 상태로 보존되어 있으므로 전체 자료를 상업승인 데이터로 해석하지 마세요.
- [전체 실행 패키지 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/what-global-standards-glossary.zip): DB·참조 API·원본·수집 코드·심사 기록·별도 FinQA 수치추론 벤치마크 포함. 모델 연결과 성능평가는 별도입니다.
- [카탈로그](catalog.json), [상업 전용 카탈로그](commercial-catalog.json), [체크섬](SHA256SUMS). ZIP 파일들과 체크섬을 함께 다운로드해 sha256sum으로 검증할 수 있습니다.

## 병렬 수집 결과

| 출처 | 채택 영어–대상언어 쌍 | 범위 | 조건 |
|---|---:|---|---|
| CFPB | 85 | 아랍어 16, 아이티 크리올어 35, 타갈로그어 34; 송금권리 안내 | CFPB 자체제작 public domain |
| 캐나다 공식 open-data/ckanext-canada | 117 | 프랑스어 재정·계약 라벨 23, 통화명 94 | MIT |
| EU Publications Office OP-TED/eForms-SDK | 1,958 | 금융·보험 서비스 89개 개념 × 22개 대상언어 | CC BY 4.0 |

신규 2,160쌍과 24개 대상언어를 추가했습니다. 기존 cfpd v1은 동결 상태로 유지했습니다. 필리핀·아랍권 현지 기관은 원문 및 상업조건 미확보로 보류했습니다. 비상업 자료를 복제·번역해서 재도입하지 않았습니다.

[상업 도입 심사·소스별 결과](COMMERCIAL-SOURCE-ADOPTION.md) · [시장조사](LANGUAGE-MARKET-RESEARCH.md)

새 자료는 송금 안내, 공공재정 라벨, 정부조달 분류라는 출처별 문맥을 유지합니다. 일반 금융용어 전반이나 독립 번역평가 정답세트로 해석하지 마세요. FinQA 1,147건은 영어 수치추론 자료로 별도 보존하며 용어 DB에 섞지 않았습니다.
