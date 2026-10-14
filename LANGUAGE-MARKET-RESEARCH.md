# 최신 병렬 수집 결과

신규 상업허용 참고자료 2,160쌍을 채택했습니다. CFPB 85쌍, 캐나다 117쌍, EU CPV 금융·보험서비스 1,958쌍입니다. 신규 대상언어 24개가 추가되어 전체 참조 데이터는 31개 대상언어 16,064쌍입니다. 상업조건 확인 자료 전용 팩은 29개 대상언어 12,249쌍이며, 기존 몽골·네팔은 상업재배포조건 미확인으로 제외했습니다. 상세 심사는 commercial-source-adoption.md를 참고하세요.

아래는 이번 병렬 수집 이전의 시장조사 기록입니다. CFPB CDN은 이번에는 HTTP200으로 원문을 확보했고, 캐나다와 EU는 공식 GitHub 재게시 원자료를 사용했습니다. 이전 기록의 원문 미확보/신규언어0 상태가 현재의 결과는 아닙니다.

---

# 금융 언어팩 및 벤치마크 시장조사

조사일: 2026-10-14 (Asia/Seoul). 조사와 채택은 분리한다. 공식 링크 발견, 원문 확보, 명시적 양언어 대응 확보, 배포 허용 확인을 각각 기록한다. 기존 cfpd v1은 변경하지 않는다.

## 목적별 구분

- 참고 언어팩: 공식 영어–대상언어 대응 표현으로 번역 후보와 출처를 제공한다. 전문가 정답평가 세트가 아니다.
- 번역검수 평가: 독립적으로 검토한 문맥과 번역 정답 및 오류 유형이 필요하다. 참고팩을 그대로 평가하면 정답 검색에 따른 데이터 누수가 발생한다.
- 금융 이해 보조평가: 문서 분류, 숫자 추론, 감성, 개체명 평가다. 번역 품질 점수로 해석하지 않는다.

## 조사 결과

| 자료 | 언어와 목적 | 원자료 확보 | 이용조건 | 도입 판단 |
|---|---|---|---|---|
| CFPB 송금권리 안내 fact sheet | 영어와 아랍어·아이티 크리올어·타갈로그 등. 공식 소비자 금융 안내 참고문장 | 공식 게시문과 원PDF 링크 확보. PDF CDN proxy403으로 내용은 미확보 | 공식 website privacy policy는 CFPB-created information public domain, 재사용 허용, 출처 인용 권장. 외부저작물/상표 예외 존재 | 새 3언어 우선 후보, PDF와 실제 대응문장 확보 전 수용 보류 |
| CFPB 공식 사이트 소스 저장소 | ar/ht/tl locale 파일 | 고정 commit 원본 PO 확보 | TERMS CC0, third-party exceptions | 파일에는 언어명만 번역되어 있음. 금융 쌍이 없으므로 채택 거절 |
| MultiFin | 다국어 금융 헤드라인 분류. 번역 정답쌍 아님 | 저자 공식 README 확보, 데이터 Dropbox proxy403 | 저자 README 명시 CC BY-NC 4.0 | 연구용 보조평가 후보. 상업 서비스용 참고팩 불가. 원데이터 미확보로 채택 보류 |
| FinQA | 영어 금융보고서 수치 추론 QA | 공식 test.json **1,147건**, README와 MIT LICENSE 확보 | 저장소 MIT, 원본 license 보존. 원자료 기업보고서 출처 함께 보존 | 수치 추론 보조평가로 관리 검토 요청. 새언어 추가/번역 정답으로 사용 불가 |
| FLUE/FLANG | 영어 금융 감성·헤드라인·NER·관계추출·QA 평가 묶음 | 공식 README 및 Apache LICENSE 확보. 구성 데이터는 미확보 | 저장소 Apache-2.0. 개별 외부 데이터의 별도 조건 적용 | 데이터별 조건 및 원자료 확보 전 보류. 번역평가와 분리 |
| PIXIU/FLARE | 금융 NLP 평가 묶음과 모델 | 공식 README 확보 | 코드 MIT지만 데이터·모델은 각각 자체 license라는 명시 | 데이터 확보 없이 구성 설명만 연구 자료. MultiFin을 Public이라 쓴 집계표보다 원저자 BY-NC 조건을 우선 |

FinQA를 확보했다는 것은 평가를 실행하거나 모델 정확도를 검증했다는 뜻이 아니다. 공개 test 정답은 모델 학습·검색 참고 자료에 합치지 않아야 한다. 공개 시험 세트의 기존 모델 노출 가능성도 결과 해석에 명시한다.

## 원자료와 증거

CFPB 공식 발표:
https://www.consumerfinance.gov/archive/blog/you-have-rights-and-protections-when-you-send-money-abroad/

이 발표가 직접 나열한 동형 fact sheet:
- English: https://files.consumerfinance.gov/f/documents/cfpb_helping-consumers-understand-remittance-transfers.pdf
- Arabic: https://files.consumerfinance.gov/f/documents/cfpb_helping-consumers-understand-remittance-transfers_ar.pdf
- Haitian Creole: https://files.consumerfinance.gov/f/documents/cfpb_helping-consumers-understand-remittance-transfers_ht.pdf
- Tagalog: https://files.consumerfinance.gov/f/documents/cfpb_helping-consumers-understand-remittance-transfers_tl.pdf

이용조건: https://www.consumerfinance.gov/privacy/website-privacy-policy/ 에서 “Information created by the CFPB is in the public domain and you may reproduce, publish, or otherwise use it without the Bureau’s permission.”을 직접 확인했다. 로고 등 상표 사용으로 기관의 승인을 암시해서는 안 된다.

공식 소스 저장소: https://github.com/cfpb/cfgov-refresh 고정 commit `d5ceb1ee8d8d827dab1252239de0b22e9de278e6`. locale PO 파일의 미번역 msgstr를 번역 데이터로 오인하지 않는다.

연구 자료:
- MultiFin 저자 저장소: https://github.com/RasmusKaer/MultiFin — EACL 2023 paper `2023.findings-eacl.66` 링크와 BY-NC 조건 명시.
- FinQA: https://github.com/czyssrs/FinQA — EMNLP 2021, 금융보고서 기반 수치 추론.
- FLUE/FLANG: https://github.com/SALT-NLP/FLANG — EMNLP 2022, 5종 금융 이해 평가.
- PIXIU: https://github.com/ChanceFocus/PIXIU — 데이터마다 자체 조건 확인 필요.

원문 파일·URL·SHA256 및 상태는 `datasets/research_candidates/cfpb_remittance/acquisition.json`과 `datasets/research_candidates/financial_benchmarks/acquisition.json`에 보존했다.

## 추가 공식 금융기관 접근 진단

캐나다 금융소비자청 canada.ca, 프랑스 중앙은행 banque-france.fr, 필리핀 중앙은행 bsp.gov.ph, 사우디 중앙은행 sama.gov.sa, 미국 FDIC fdic.gov를 정상 HTTPS로 조회했으나 모두 환경 proxy CONNECT403이다. 접근 차단은 자료가 없다는 뜻이 아니다. 보안 우회는 하지 않았다.

CFPB /language/ar/, /language/ht/, /language/tl/은 현재 홈페이지로 리다이렉트되므로 이를 실제 번역페이지 수집으로 계산하지 않았다. 공식 저장소의 테스트용 “translated page” fixture도 실제 금융 번역 데이터가 아니므로 제외했다.

## 관리 피드백에 따른 재조사 및 다음 우선순위

자료 관리 에이전트는 명시적 대응과 원자료 확보 없는 후보를 거절했다. 이에 CFPB 링크 확인에서 공식 GitHub locale 조사로 전환했으나 금융본문이 없어 제외했다. 연구 평가를 허용한 추가 지시에 따라 FinQA 실데이터를 확보했다. MultiFin은 원저자 license를 확인해 상업 활용 후보에서 연구전용 후보로 변경했다.

1. 허용 도메인 변경이 실제 환경에 적용되면 CFPB PDF 4개를 확보하고 같은 조항·제목·수치로 대응 확인한다. 이를 통해 3새언어 소규모 문장팩을 만들 수 있다.
2. 프랑스어는 캐나다 금융소비자청의 영어/프랑스어 동형 glossary와 병행교육자료를 우선한다. 기관 페이지의 대응과 재사용 조건을 직접 확인해야 한다.
3. 아랍어는 CFPB 확보 이후 해당 지역의 중앙은행 자료를 추가하여 미국 송금 제도와 지역 은행 표현을 구분한다.
4. 타갈로그는 필리핀 중앙은행 금융교육 영어/필리핀어 자료를 추가 검토한다. Filipino/Tagalog 표기는 원 발행기관 표기를 유지한다.
5. 독립 번역검수 벤치마크는 참고팩과 겹치지 않는 문맥, 숫자·수수료·조건·관할 오류를 포함하고 원어민 검토 후 고정한다. 이번 공개자료 조사만으로 번역 정답 벤치마크가 완성됐다고 주장하지 않는다.

## 관리 후속 검토 및 용어 인프라 후보

자료 관리 에이전트가 FinQA test 1,147건을 `accepted_benchmark`으로 채택했다. 별도 입력/정답을 분리하며, 신규 대상 언어와 영어–외국어 쌍 추가는 **0건**이다. 14건의 빈 자연어 answer는 추론 program/execution 정답을 보존하고 상태를 표시한다.

MultiFin 저자 원본 저장소를 고정 commit `8b0c5a5d1de0d2fd884729ef9de03e7d44d80a98`로 실제 clone하여 전체 추적 파일을 확인했다. 저장소에는 README.md만 있고 데이터·샘플 파일이 없다. Dropbox 원자료가 차단돼 연구용 실데이터 도입도 보류다.

다음 공식 다국어 용어 인프라 후보도 확인했다.

| 후보 | 금융 언어팩 관점 | 현재 검증 상태 |
|---|---|---|
| [EU IATE](https://iate.europa.eu/) | EU 기관 용어에서 금융·경제 분야의 개념 ID별 다국어 명칭과 신뢰도·문맥을 함께 선별하는 방향 | 공식 사이트 proxy403. 실제 레코드·언어 범위·재배포 조건 미확인, 도입 보류 |
| [캐나다 TERMIUM Plus](https://www.btb.termiumplus.gc.ca/) | 금융 용어 영어–프랑스어를 중심으로 출처·분야·용례를 확인하는 방향 | 공식 사이트 proxy403. 실제 레코드·재배포 조건 미확인, 도입 보류 |
| [EU Publications Office EuroVoc](https://op.europa.eu/en/web/eu-vocabularies/th-dataset/-/resource/dataset/eurovoc) | 같은 SKOS 개념의 다국어 label 중 금융·경제 분류를 선별할 수 있는 후보. 전문 소비자 금융사전과 범위 차이 존재 | 공식 사이트 proxy403. GitHub 검색의 비공식 복제본은 원자료/조건 확인 없이 도입하지 않음 |

이번 환경에서 정상 HTTPS 접근이 가능한 공식 새언어 원자료를 더 찾았지만, 실제 영어–새언어 금융 쌍 확보에는 이르지 못했다. 차단 기록이나 README 확보를 수록 데이터 증가로 계산하지 않는다.
