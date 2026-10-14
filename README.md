# 금융 용어집 다운로드

이 브랜치는 금융 용어집 배포 전용입니다. 원본 출처와 검수 상태를 보존한 데이터와 실행 패키지를 제공합니다.

## 다운로드

- [데이터 전용 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/glossaries-data.zip): 다른 AI 에이전트의 검색·번역·검수 참조용
- [실행 패키지 ZIP](https://raw.githubusercontent.com/simsoni7/WhatGloabalStandardsSay/glossary-distribution/what-global-standards-glossary.zip): Python 참조 API와 원본·출처 포함
- [카탈로그](catalog.json) · [체크섬](SHA256SUMS) · [실행 패키지 검증 기록](delivery.json)

데이터 ZIP을 풀면 JSONL·CSV·카탈로그·사용 안내가 제공됩니다. 실행 패키지는 압축을 풀고 내부 `RUN.md`를 확인하세요. 체크섬 검증은 내려받은 두 ZIP과 SHA256SUMS를 같은 폴더에 두고 `sha256sum -c SHA256SUMS`로 실행합니다.

## 데이터 범위와 활용

기본 조회 허용 레코드는 13,904개입니다: cfpd용어집 v1 10,089개, Mongolbank 후보 3,644개, Nepalbank 후보 171개. Nepalbank에는 기존 표제어 60개, AI 보조 정렬 검토 용례 6개, 신규 공식 양식 병기 항목 105개가 포함됩니다. 신규 항목은 AI가 원본 화면과 대조했으며 전문가 검수는 아닙니다. 양식 문맥을 확인하세요. 영어–외국어 쌍과 출처·검수 상태를 함께 사용해야 합니다.

AI에는 목표 언어, 사용 국가, 금융 상품·상황을 전달하고 카탈로그 및 레코드의 근거를 검색하도록 하세요. 모델 생성 표현을 출처의 공식 번역으로 바꾸지 마세요. 전체 전문가 검수와 원본 사이트 전체 수집 여부가 확정된 자료는 아닙니다.

실행 패키지의 참조 조회·용어 번역·출처 비교는 무료로 동작합니다. 자유 문장 생성·문맥 검수는 별도 모델 연결이 필요하며 실제 모델 검증은 완료되지 않았습니다. 이 다운로드 배포는 상시 API 호스팅이 아닙니다.

## 원문 기관

- CFPB: https://www.consumerfinance.gov/
- 몽골은행 용어집: https://toli.mongolbank.mn/ 및 https://etoli.mn/
- Nepal Bank: https://nepalbank.com.np/

원문 기관이 이 배포를 승인했다는 의미는 아닙니다. 원문의 사용 조건과 각 레코드의 출처를 확인하세요.

네팔어 보강 내역과 원본 출처: [NEPAL-UPDATE.md](NEPAL-UPDATE.md).

## 금융 언어팩·벤치마크 시장조사 (2026-10-14)

[시장조사](LANGUAGE-MARKET-RESEARCH.md)와 [데이터 관리 검토](LANGUAGE-PACK-ADOPTION.md)를 통해 FinQA 공식 공개 test 1,147건을 별도 수치추론 벤치마크로 채택했습니다. 두 ZIP의 `benchmarks/finqa/` 또는 `datasets/language_packs/finqa_numerical_reasoning/`에서 원본·정답·MIT 라이선스를 확인하세요. 참조 DB에는 섞지 않았으며 모델 성능평가는 실행하지 않았습니다.

새 대상언어는 이번에 추가되지 않았습니다. 아랍어·아이티 크리올어·타갈로그 CFPB 공식 안내 후보는 원본 CDN 접속 차단으로 보류했습니다. MultiFin은 원자료 미확보 및 비상업 이용 조건 때문에 도입하지 않았습니다. 참고용 영어–외국어 쌍은 기존 7개 대상언어 13,904건입니다.
