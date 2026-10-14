# Batch 6 독립 검수

Mifos mobile 공식 저장소의 commit `18a6499ffef39c1cfac69be4a8fdbef84485e536` 및 실제 MPL-2.0 LICENSE와 18개 XML 파일 header/원문 byte를 대조했습니다. 총 974개 동일 Android key 관측 중 **927개**를 조건부 참고용으로 수용하고 **47개**는 금융 의미 의심으로 제외했습니다.

principal→director/owner/school principal, interest→general interest/interest rate, balance→equilibrium, beneficiary→heir, nominal→ordinary 등의 실제 다의어 오류가 있습니다. 원문은 수정하지 않았습니다. 검수 JSON에는 제외 ID와 각 근거가 있습니다.

전체 수용 관측도 `generation_block_ids`에 포함합니다. 금융 전문가 승인 0이며, 소프트웨어 공식 저장소라는 사실은 번역 품질의 보장이 아닙니다. 원문 key 일치, 입력 SHA, XML raw 값, fallback, placeholder, native script, 원문 commit byte 검사는 통과했습니다.

MPL 소스와 추출 고지를 함께 제공하는 별도 팩만 허용합니다. Apache/MIT 중심 기본팩에 섞어 라이선스를 덮어쓰면 안 됩니다.

추가로 outstanding balance를 extraordinary/excellent balance로 옮긴 인도네시아어·러시아어·크메르어 3개를 제외했습니다.
