# 캄보디아·베트남어·러시아어 추가 수집 — 2026-10-14

직전 CFPB50쌍 수집 뒤 상시 백그라운드 작업은 실행하지 않았습니다. 이번 요청에서17개 URL을 실제 조회하고 공식 원자료를 추가 수집했습니다.

| 대상 | 현재 수록 | 이번 추가 | 출처·자료 범위 |
|---|---:|---:|---|
| 크메르어(캄보디아) | 166 | 166 | Unicode CLDR 공식 통화명 |
| 베트남어 | 2,325 | 297 | 기존 CFPB2,028 + CLDR 통화명297 |
| 러시아어 | 2,308 | 280 | 기존 CFPB2,028 + CLDR 통화명280 |

신규743쌍은 공식 [Unicode CLDR JSON](https://github.com/unicode-org/cldr-json/tree/48.0.0)의 영어와 대상 언어 displayName을 동일 통화코드로 연결했습니다. 고정 커밋4d06be52b51bb2f75688d0abe55c52a66afed790과 원본 파일 해시·키·문자열을 전수 대조했습니다. [Unicode-3.0 원문](https://github.com/unicode-org/cldr-json/blob/4d06be52b51bb2f75688d0abe55c52a66afed790/LICENSE)은 상업 사용·배포·판매를 허용하며 저작권·허가 고지를 유지해야 합니다. 고지를 HTML·다운로드 ZIP에 보존했습니다.

이 자료는 역사통화를 포함한 통화명이며, 예금·대출·금리·담보·보험 등 은행 금융용어 전반을 확보한 것은 아닙니다. 현재 유효한 통화코드 목록이 아니며 러시아어 숫자별 격변화 등도 기본 displayName만으로 처리할 수 없습니다. 제외6개는 미상통화 XXX3, 시험통화 XTS2, 크메르어 ESP 이름 누락1입니다. 독립 AI 원문 검수 통과가 전문가 번역 승인이라는 뜻은 아닙니다.

## 현지 금융기관 접근 결과

- 캄보디아 [National Bank of Cambodia](https://www.nbc.gov.kh/): 홈페이지와 English/Khmer 경로 모두 CloudFront HTTP403 응답. [ACLEDA](https://www.acledabank.com.kh/)·[ABA](https://www.ababank.com/)는 환경 CONNECT403. 은행 상품·KYC·송금·신용 용어의 원문과 상업 재사용 조건은 아직 확인하지 못했습니다.
- 베트남 [SBV](https://www.sbv.gov.vn/), [Vietcombank](https://www.vietcombank.com.vn/), [BIDV](https://www.bidv.com.vn/), [VietinBank](https://www.vietinbank.vn/): 환경 CONNECT403. 영어/베트남어 양식·금융교육·계좌/대출 자료를 후속 탐색할 기관 후보입니다. 실제 병행 자료와 권리 허용을 확인한 결과가 아닙니다.
- 러시아 [Bank of Russia](https://www.cbr.ru/eng/), [Fincult](https://fincult.info/), [Sberbank](https://www.sberbank.ru/), [VTB](https://www.vtb.ru/): 환경 CONNECT403. 용어집·소비자 금융교육·공식 양식의 영어 대응과 재사용 조건은 추가 확인 대상입니다.

접속 차단은 자료가 없다는 뜻이 아닙니다. 정상 HTTPS 접근에 필요한 도메인은 기존 목록을 유지한 환경 설정 초안에 추가했습니다. 초안 저장만으로 런타임 변경이 적용되지는 않습니다. 외부 저작물의 재표현을 통해 이용 조건을 우회하지 않습니다.

## 다른 확보 자료와 다음 범위

CFPB 공식 목록에서 연결된 베트남어·러시아어 ‘해외 송금’ 소비자 안내 PDF2개와 대응 영어판1개도 실제 확보했습니다. Author는CFPB이고12/2021 자료입니다. 베트남어 원본에 미번역 영어 줄·문자 오타가 관찰되어 위치만으로 자동 정렬하지 않습니다. 이3개 문서의 새 용어쌍은 아직 수록하지 않았으며 은행 현지 자료와 구분합니다.

다음 확보 목표는 국가별 실무 용어입니다. 캄보디아는 KYC·해외송금·계좌·대출 양식, 베트남은 계좌·예금·대출·수수료, 러시아는 금리·이자·수수료·담보·소비자 신용 표현을 우선합니다. 상업 이용 허용과 명시적인 영어 대조를 모두 확인한 자료만 별도 소스팩으로 채택합니다. UI지원 언어 수가 추가돼도 확보한 분야의 한계는 유지합니다.
