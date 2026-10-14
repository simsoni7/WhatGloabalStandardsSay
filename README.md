# 다국어 금융용어사전

[공유 화면 열기](https://htmlpreview.github.io/?https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/dictionary-20261014-r4/index.html) — 무료 HTMLPreview로 공개 GitHub 원본 HTML을 열며, 화면에서 같은 버전의 데이터를 다운로드할 수 있습니다. GitHub Pages 자체 활성화와는 별개입니다.

## 스키마 v2: 출처 표기와 승인된 번역 분리

통합 JSONL·CSV와 API는 source_english/source_target을 출처의 표기로 보존합니다. alignment_status는 출처 연결이고 equivalence_status는 의미 검토 상태입니다. approved_translation은 모든 레코드에서 null입니다. 원문 인용은 source_quoted_text로 반환하며 승인된 번역처럼 반환하지 않습니다.

원본 cfpd v1 및 수집 원자료는 변경하지 않았습니다. 304번 Interest Rate/Хүү는 원문 정의 불일치 의심으로 표시했고 733/737/3377과 함께 검토 대상으로 보존했습니다. 자동 수정·개념 병합은 하지 않았습니다. [스키마 및 API 변경 안내](INTEGRATION-V2.md) · [전처리 보고서](integration-report.json).



## 권장: 상업 이용 조건 확인 데이터

[상업 조건 확인 언어팩 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/commercial-language-packs.zip): 30개 대상언어, 영어–대상언어 13,042쌍. CFPB 자체제작 공개영역 자료, 캐나다 정부 MIT 자료, EU CC BY 4.0 자료입니다. 각 출처의 저작권·라이선스·출처표시 조건을 보존해야 합니다. 상업 허용이 전문가 번역검수를 뜻하지는 않습니다.

## 전체 자료와 실행 패키지

- [전체 참조 데이터 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/glossaries-data.zip): 32개 대상언어, 16,857쌍. 기존 몽골·네팔 자료는 상업 재배포조건 미확인 상태로 보존되어 있으므로 전체 자료를 상업승인 데이터로 해석하지 마세요.
- [전체 실행 패키지 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/what-global-standards-glossary.zip): DB·참조 API·원본·수집 코드·심사 기록·별도 FinQA 수치추론 벤치마크 포함. 모델 연결과 성능평가는 별도입니다.
- [카탈로그](catalog.json), [상업 전용 카탈로그](commercial-catalog.json), [체크섬](SHA256SUMS). ZIP 파일들과 체크섬을 함께 다운로드해 sha256sum으로 검증할 수 있습니다.

## 병렬 수집 결과

| 출처 | 채택 영어–대상언어 쌍 | 범위 | 조건 |
|---|---:|---|---|
| CFPB | 135 | 아랍어16·아이티 크리올어35·타갈로그어34 및 스페인어·한국어·러시아어·베트남어·중국어 번체 각10; 송금 안내 | CFPB 자체제작 public domain |
| 캐나다 공식 open-data/ckanext-canada | 117 | 프랑스어 재정·계약 라벨 23, 통화명 94 | MIT |
| EU Publications Office OP-TED/eForms-SDK | 1,958 | 금융·보험 서비스 89개 개념 × 22개 대상언어 | CC BY 4.0 |

첫 수집에서2,160쌍과24개 대상언어를 추가했고, 후속으로 CFPB 5언어50쌍을 추가했습니다. 기존 cfpd v1은 동결 상태로 유지했습니다. 필리핀·아랍권 현지 기관은 원문 및 상업조건 미확보로 보류했습니다. 비상업 자료를 복제·번역해서 재도입하지 않았습니다.

[상업 도입 심사·소스별 결과](COMMERCIAL-SOURCE-ADOPTION.md) · [시장조사](LANGUAGE-MARKET-RESEARCH.md)

새 자료는 송금 안내, 공공재정 라벨, 정부조달 분류라는 출처별 문맥을 유지합니다. 일반 금융용어 전반이나 독립 번역평가 정답세트로 해석하지 마세요. FinQA 1,147건은 영어 수치추론 자료로 별도 보존하며 용어 DB에 섞지 않았습니다.

## 의미·문맥 검토 업데이트

390개 충돌 그룹을 분류하고 정의·원문·문맥을 담은 검토 자료를 추가했습니다. 주요 11개 사례의 18개 레코드에 AI 정의 검토를 기록했고, Interest Rate304와 Warrant premium3104는 원문 정의 불일치 의심으로 생성 참고에서 격리했습니다. 모든 일치 자료가 격리 상태라면 모델 호출을 차단합니다. 737/3377은 같은 의미의 표현 변형 후보이며 자동 병합 또는 번역 승인은 하지 않았습니다. 전문가 승인 번역은 여전히0건입니다. [검토 결과와 한계](SEMANTIC-REVIEW.md).

## 금융 개념 정보화와 분업 검수

데이터 진단·금융 개념 정보화·의미 전처리·문맥 평가·독립 검수·통합배포 역할을 분리했습니다. 금융 개념 후보24개(상업 근거 필터 후19개), 추가 의미검토32개/65레코드, 구조 문맥진단26개를 독립 AI검수 후 수용했습니다. 누적 의미결정은43개/83레코드입니다. 금융개념 연결은30개 모두 후보이며 source ID를 바꾸거나 번역승인을 부여하지 않습니다.

`/v1/concepts`로 AI후보개념과 구분질문을 검색하고, `financial_concept_id`와 `use_case`로 명시적 문맥을 선택할 수 있습니다. 이자/이자율 의미선택과 조달 분류의 소비자UI 사용 guard를 제공합니다. 자유문장 문맥분석12사례는 미구현으로 별도기록했고 실제 모델 정확도·전문가 번역승인은 측정하지 않았습니다. 원출처 정의 필드가 없는 상업자료를 AI설명으로 채웠다고 주장하지 않습니다.

[목표·진행계획·에이전트셋](DATASET-DEVELOPMENT-PLAN.md) · [실제 데이터 진단](DATASET-QUALITY-DIAGNOSIS.md) · [금융 정보화 모델](FINANCIAL-INFORMATION-MODEL.md) · [독립 검수 결과](ENRICHMENT-REVIEW.md).

## 조회용 다국어 금융용어사전

[사전 화면 ZIP 다운로드](financial-dictionary.zip) → 압축을 풀고 `financial-dictionary.html`을 브라우저에서 엽니다. 영어–외국어 16,857쌍을 한국어 언어명·출처·자료 종류·이용조건으로 필터링합니다. 검색·정렬·상세 근거·언어별 통계·출처의 신뢰 근거와 수집 방식·확장 후보를 제공합니다.

검토자·판정·메모·검토 기록 입출력 기능은 제거했습니다. 기존 `financial-review.html`과 `financial-review-workbench.zip` 주소도 조회 화면으로 갱신했습니다. GitHub raw는 HTML을 웹페이지로 렌더링하지 않으므로 ZIP을 내려받아 여세요.

[사용 방법](FINANCIAL-DICTIONARY.md) · [언어별 확장 후보 조사](FINANCIAL-DICTIONARY-EXPANSION.md) · [후보 목록 JSON](dictionary-expansion-candidates.json).

이번 업데이트는 CFPB 공식 문맥 표현50쌍을 원문 대조·독립 AI검수 후 추가했습니다. 기존 동결 CFPD는 변경하지 않았습니다. 네팔 RBB8개는 권리 미확인 연구 후보라 공개 사전에 추가하지 않았습니다.

## 크메르어·베트남어·러시아어 추가 수집

Unicode CLDR48.0.0 공식 통화명743쌍(크메르어166·베트남어297·러시아어280)을 추가했습니다. Unicode-3.0이며 저작권·허가 고지를 보존했습니다. 역사통화를 포함한 통화명으로 은행 금융용어 전반은 아닙니다. 크메르어는 이번에 신규 추가되어 전체32개 대상언어16,857쌍입니다. [국가별 실제 조사와 접근 한계](KH-VI-RU-COLLECTION.md).
