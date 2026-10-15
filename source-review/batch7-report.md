# Batch 7 독립 원문·권리·금융 의미 검수

금융 전문가 승인 또는 번역 동치 확정은 수행하지 않았습니다. `human_review=false`, `semantic_approval=false`, `approved_translation=null`을 유지합니다.

## Apache OFBiz 추가 모듈

고정 커밋 `b8b72d556e829d4a0818f8a4fed57e0750efcacb`의 AccountingEntityLabels, CommonEntityLabels, CommonUiLabels, PartyUiLabels 네 XML과 LICENSE·NOTICE 총 6개 원자료 SHA를 독립 대조했습니다. 제출 931개 모두 같은 property key의 실제 영어·대상 언어 원문 값과 정확히 일치했습니다. 원문 바이트와 trim된 표기 차이도 확인했습니다.

수집자가 이미 제외한 조합과 별개로 독립 검수에서 37개를 추가 제외하여 **894개·17개 언어**만 출처 참고 관측으로 수용합니다. 제외 ID·원문·이유는 decisions.json에 보존합니다. 대표적으로 일본어 invoice가 inventory로, 태국어 long-term liability가 receivable로, money order가 일반 금융 목록으로 번역된 오류가 있습니다. 프랑스어 outgoing payment와 payment due, 네덜란드어 income tax와 payroll tax, 포르투갈어 prepayment와 general payment의 범위 혼동도 제외했습니다.

수용 자료도 커뮤니티 ERP UI 번역이며 금융기관 공인 용어집이 아닙니다. 모든 자료를 `generation_policy_block_all=true`로 자동 생성 참고에서 제외합니다. 이 정책은 수용 자료 전체가 오역이라는 뜻이 아니며, 금융 전문가 검토 이전의 문맥 제한입니다.

Apache-2.0 상업 이용 조건에 따라 LICENSE·NOTICE 및 추출 변경 고지를 함께 유지해야 합니다. 기본 원문 사전의 출처별 별도 팩으로 도입할 수 있습니다. 원문 JSONL 해시와 수용 ID 894개를 고정했으며 미수용 ID 37개는 통합하면 안 됩니다.

## 네팔·FDIC 공식 후보 재확인

최종 15개 공식 URL 중 네팔 6페이지 raw SHA를 모두 독립 확인했습니다. FDIC 9개 경로는 HTTP/CONNECT 403으로 원문과 권리를 검증하지 못했습니다. 네팔 기관·은행은 명시적 상업 재배포 허가가 확보되지 않았고 일부 All Rights Reserved 고지가 있어 **채택 0개**입니다. NRB HTML의 CC 2.0은 Iatek LLC 캐러셀 CSS 주석에만 붙어 있으며 금융 본문 라이선스로 확대 해석하지 않습니다.

## 아시아 공식 데이터

말레이시아 정부 data-gov-my/datagovmy-meta 저장소 고정 커밋 `a34682cf22a1da9de5520a27f5f3fc5f7c86b06f`의 MIT 허가와 저작권을 직접 HTTPS 취득하여 바이트 대조했습니다. 일반 BNM 웹사이트 약관이 아니라 해당 MIT 저장소의 로컬라이제이션 JSON만 채택합니다. 원문 20개 JSON과 LICENSE의 SHA를 대조하고 영어·말레이어 65개 동일 JSON 키를 전수 확인했습니다. 외화예금 라벨의 선행공백도 raw/source 필드에 보존하며 표시용 trim과 구분합니다.

금리, 통화량, 준비금, 가계부채, 전자결제, 은퇴 및 소득세 지표 라벨 **65개**를 말레이시아 통계 대시보드 문맥의 참고 관측으로 수용합니다. 원문 Interbank Giro는 영어·말레이어에 동일한 고유 명칭이 있어 그대로 보존합니다. 의미 전수 점검에서 추가 특정 오류를 발견하지 못했으나 전문 번역 승인 또는 포괄 금융 용어 동치를 뜻하지 않습니다. 전체 자동 생성은 정책상 제외하고 전문가 승인은 0개를 유지합니다.

기타 8개 아시아 기관의 일반 홈페이지·용어집 공개 접근과 권리 허용은 별개입니다. 일반 웹페이지의 권리를 해당 MIT 코드/메타데이터 저장소로 덮어쓰지 않습니다.

## 최종 결과

Apache 894개와 말레이시아 65개, 합계 **959개**만 해시와 수용 ID로 고정하여 채택합니다. 이 단계 독립 검수 추가 제외는 37개이며 수집 단계의 선행 제외와 별도입니다. 금융 전문가 승인 0개입니다.
