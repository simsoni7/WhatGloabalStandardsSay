# CFPB 금융용어집 2024 추가 언어

2026-10-16 확보한 CFPB 공식 금융용어집의 아랍어·타갈로그어·아이티 크레올어 자료입니다. 번역을 생성하지 않고 같은 원문 표 행의 영어와 대상어를 대응했습니다.

- 신규 언어쌍: 4,764개 (아랍어 1,572 / 타갈로그어 1,609 / 아이티 크레올어 1,583). 기존의 추가 언어이며 언어 코드 수를 늘리지 않습니다.
- 후보 6,056행에서 표제 3행, 비금융·문자·대응 품질 문제 1,283행, 기존 자료와 정확히 중복된 6행을 제외했습니다.
- 기존 CFPD·송금 자료를 포함한 26,245개 전체 행과 NFKC·공백·대소문자 정규화 후 (영어, 대상어, 언어)로 중복을 확인했습니다. CFPD·송금 자료와의 중복은 0개입니다. 영어가 같고 외국어 표현이 다른 문맥별 원문은 보존합니다.
- 한국어는 동일 영어 표제의 기존 CFPB 공식 한국어가 단일 값으로 확인될 때만 검색 보조로 재사용합니다. 근거 ID를 보존하며 나머지는 null입니다. 한국어와 신규 외국어의 의미 동치를 승인한 것은 아닙니다.
- Bedrock claude-sonnet-5가 금융 관련성·명백한 오정렬·문자 훼손을 선별했습니다. 판정은 번역 전문가의 검토나 승인이 아닙니다. 모든 행은 generationEligible=false이며 승인 번역으로 쓰지 않습니다.

## 원천자료와 추출

raw/에 공식 PDF 3종과 CFPB 저작권 정책 HTML 원본이 있습니다. sources.json에 URL·원본 SHA·페이지 수를 보존합니다. CFPB 자체 작성 정보의 public-domain 정책에 따라 상업 이용 가능한 core 자료로 구성합니다. 제3자 저작물과 상표에 대한 포괄적 허가를 뜻하지 않으며 CFPB의 WGSS 보증·승인을 암시하지 않습니다.

표의 수평 경계선으로 행을 구분하고 실제 표 열의 clip bbox로 각 셀을 읽습니다. 원문 PDF는 바꾸지 않습니다. 아랍어 presentation form은 NFKC 정규화하고, 정규화 전 글자·물리 페이지·행 번호·행 및 열 좌표를 provenance에 보존합니다.

span origin만으로 열을 나누면 아랍어 3행에서 글자가 영어 칸으로 넘어가는 문제가 있어 전체 추출기를 셀 clip으로 수정했습니다. 변경된 7행(열 분리 3행·presentation 공백 4행)은 입력 SHA를 무효화하고 Bedrock 판정을 다시 받았습니다. cell-clip-corrections.json에 전후 값을 남겼습니다. Tagalog 42쪽 Installment loan의 원문 대상어 셀은 공란이며, 보완 번역을 생성하지 않았습니다.

## 파일

- observed-pairs.json: 원문 후보와 위치. 표제행도 감사용으로 보존합니다.
- automated-review.json: 전체 Bedrock 판정·모델·토큰 사용량.
- excluded-pairs.json: 금융성·문자·대응 품질 제외 행과 사유.
- mechanically-excluded-rows.json: 표제행의 기계적 제외.
- duplicate-pairs.json: 기존 자료와 정확히 중복된 행 및 데이터셋.
- summary.json: 입고·제외·중복·원문 및 라이선스 검토 수치.
- ../../integration-data/terms/0120.json부터 0147.json 및 같은 번호의 provenance: 공개 검색용 신규 청크.

## 재현

Python 3과 pymupdf가 필요합니다. 원본 PDF SHA를 고정 검증합니다. BEDROCK_API_KEY를 환경변수로 제공한 후 아래 명령을 실행합니다. 키와 요청 인증 값은 결과에 저장하지 않습니다.

```sh
python collect_cfpb.py
WGSS_CFPB_VARIANT=haitian python collect_cfpb.py
```

재실행은 같은 원문 스냅샷에 대한 자동 선별 재현입니다. 원문이 바뀌면 새 버전과 증거를 확보하여 별도 배치로 검토해야 합니다.
