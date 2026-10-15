# 무료 소스 모니터링과 검토 대기열

`.github/workflows/glossary-source-monitor.yml`은 GitHub Actions에서 매일 UTC 02:23 및 수동 실행으로 Apache OFBiz, GnuCash, Mifos 원본을 확인합니다. 워크플로 파일 또는 수집 스크립트 변경 시에도 실행됩니다. 공개 저장소의 표준 호스팅 실행기를 사용하며 별도 유료 수집 서비스나 AI API를 호출하지 않습니다. GitHub 계정의 Actions 정책에 따라 실행 가능 여부가 달라집니다.

`research → audit → publish-progress` 세 작업은 소스 수집, 결정적 무결성 검사, 결과 게시입니다. **이 작업들은 상시 AI 에이전트나 금융 전문가의 의미 검수가 아닙니다.** 원본 키의 의미나 번역 정확도를 자동 승인하지 않습니다. 원본 변경은 검토 후보가 될 뿐 기본 용어집에 자동 도입하지 않습니다.

현재 검토된 기준 커밋과 최신 HEAD를 비교하고 커밋 고정 raw GitHub 파일, 원문 전체, 라이선스, NOTICE 및 SHA-256을 보존합니다. JSON/XML 구문과 PO 기본 구조 및 바이트 무결성을 검사합니다. 라이선스·NOTICE 변경, 누락 또는 수집 오류는 차단 상태로 기록합니다. 모든 후보는 `semantic_approval=false`, `adoption_allowed=false`입니다. Apache 출처 표시 및 GPL/MPL 원문·저작권·대응 소스 의무는 계속 적용됩니다.

결과는 기본 배포 브랜치와 구분된 `glossary-source-intake` 브랜치의 `automation/progress.json`, `intake.json`, `snapshots/`에 게시합니다. 이 모니터링 전용 브랜치는 최신 실행 결과로 교체하며 실행별 기록은 14일간 Actions 아티팩트에 남습니다. 기존 용어집·확정 데이터·HTML 배포는 수정하지 않습니다.

워크플로가 저장소의 **기본 브랜치**에 있어야 정기 실행됩니다. Actions 허용 및 `GITHUB_TOKEN`의 contents 쓰기 권한이 필요합니다. 실행 여부는 저장소 Actions 탭에서 확인해야 하며, 설정 파일이 존재한다는 사실만으로 실행 중이라고 말해서는 안 됩니다. 외부 사이트 접근 제한을 회피하거나 TLS 검증을 해제하지 않습니다.

로컬 재현:

```sh
python3 scripts/monitor_glossary_sources.py research --output /tmp/glossary-intake
python3 scripts/monitor_glossary_sources.py audit --output /tmp/glossary-intake
```


r8부터 말레이시아 정부 datagovmy-meta의 MIT 금융통계 원문도 기준 커밋과 함께 감시합니다. 한국 시간 매일 오전11시23분(UTC02:23) 예약이며, 원문 수집·무결성 확인을 수행할 뿐 AI 의미 검수·자동 채택은 하지 않습니다.
