# 영어 원문의 한국어 표현

`source_english`를 기준으로 한국 담당자의 조회·이해를 돕는 `source_english_korean` 필드를 추가했습니다. 영어 원문과 외국어 원문인 `source_target`은 변경하지 않습니다. 영어 표기의 공백·유니코드·대소문자만 정규화한 키로 표제어별 한국어 표현을 재사용합니다. 같은 표기를 연결하는 것은 출처 간 금융 개념·외국어 의미를 통합하거나 승인하는 작업이 아닙니다.

기존 CFPD 영어–한국어 원문이 있는 표제어는 한국어 원문을 재사용하고 `source_korean_reused` 및 원본 evidence ID를 남깁니다. 나머지는 분담 번역 에이전트가 실제 한국어 표현을 작성하고 독립 AI 검수 에이전트가 금융 의미와 행 대응을 점검했습니다. 상태는 `ai_translated_unreviewed`입니다. 여기서 unreviewed는 금융 전문가·사람의 승인 전이라는 뜻이며 AI 점검이 전문가 검수를 대체하지 않습니다. 자동 문구 치환이나 외국어에서의 역번역으로 빈칸을 메우지 않습니다.

```json
{
  "source_english": "Interest Rate",
  "source_english_korean": "이자율",
  "source_target": "원출처의 외국어 표현",
  "korean_expression": {
    "status": "source_korean_reused",
    "scope": "english_label_reading_and_search_aid",
    "human_approved": false,
    "target_equivalence_approval": false
  },
  "approved_translation": null
}
```

원문 외국어가 금리 대신 이자를 뜻하더라도 한국어 표시는 영어 원문을 설명합니다. 이를 이유로 해당 외국어를 정확한 번역으로 판정하지 않으며 기존 의미 위험과 생성 제한을 유지합니다. 모호한 일반 단어에는 해당 출처 문맥과 한국어 표현의 note를 함께 확인하세요.

화면에는 '영어 원문의 한국어 표현' 열과 설명을 표시합니다. 한국어·영어·외국어를 모두 검색하며, 기본 자료와 조건부 JSON 자료를 읽은 뒤의 검색 동작도 동일합니다. CSV에는 한국어 필드와 `korean_expression_json`을, JSONL에는 구조화 메타데이터를 포함합니다.

## 생성·검수 기록

`datasets/enrichment/korean_english_labels.jsonl`은 표제어별 한국어 표현, `korean_label_report.json`은 재사용/신규 번역 수·입력 SHA·누락 여부를 기록합니다. 번역 초안에서 발생한 목록 정렬 밀림과 금융 용어 오해는 배포 전 독립 대조에서 발견해 교정합니다. 최종 검수 보고서와 SHA를 보존합니다. 사람이 승인한 외국어 번역 수와 한국어 보조 표현의 수는 별개입니다.

## 오프라인

일반 ZIP은 전체 압축 해제 후 별도 파일을 자동 읽습니다. 이메일용 ZIP은 실행 파일 확장자의 별도 JavaScript 없이 HTML과 JSON을 제공하므로, HTML을 열고 동봉된 data/의 JSON을 모두 선택합니다. 읽은 자료의 한국어 표현도 인터넷 없이 검색할 수 있습니다. 공급자별 첨부 허용 여부는 별도 정책입니다.


## 출처별 문맥 구분

동일 영어라도 뜻이 다른 경우 `korean_record_overrides.jsonl`의 원문 evidence ID별 한국어 표현을 우선합니다. 예를 들어 네팔은행 상품의 Current Account(당좌예금계좌)와 국제수지 통계의 Current Account(경상계정·경상수지)는 영어 문자열만으로 같은 한국어로 표시하지 않습니다. 이 별도 보강은 원래 영어·외국어 원문을 수정하거나 승인하는 작업이 아닙니다.
