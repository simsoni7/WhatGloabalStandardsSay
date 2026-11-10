# 서버 교체와 복구

통합 소스: `wgss-integration` 브랜치의 `wgss-app/`.

## 저장소에 보존하는 것

- 프런트·백엔드·수집기 소스와 의존성 잠금 파일, DB 마이그레이션, nginx·systemd 설정.
- 기본 금융사 자료와 언어팩, 승인된 전체 변경분, 등록 회사 목록, 공개된 화면 버전과 정확한 이미지 파일.
- `source-data/runtime-backup/manifest.json`: 백업 시각, 종류별 변경분 수, 이미지 SHA-256.
- `source-data/runtime-backup/publications.json.gz`: 공개 API의 승인 자료 및 화면 버전.

GitHub Actions가 15분 간격으로 확인하고, 승인 데이터가 달라졌을 때만 `wgss-integration`에 커밋·푸시합니다. EC2와 독립적으로 실행합니다. 예약 작업은 GitHub에서 지연될 수 있으므로 실제 마지막 성공 시각과 manifest를 확인합니다. 워크플로 파일은 저장소 기본 브랜치 `glossary-distribution`에도 동일하게 유지합니다. 기본 브랜치를 바꿀 때 새 기본 브랜치에 이 파일이 있는지 확인합니다.

원본 미가림 사진·미승인 제안·운영 로그·개인키·토큰은 공개 Git 백업 대상이 아닙니다. 승인된 데이터의 최신 상태와 공개 화면 버전은 복원할 수 있지만, 접수 중인 제안 및 내부 감사 로그 전체를 담은 DB 덤프는 아닙니다.

## 새 서버에서 공개 자료 조회 복구

Node.js 22 및 Python 3를 준비합니다.

```sh
git clone --branch wgss-integration https://github.com/simsoni7/WhatGloabalStandardsSay.git
cd WhatGloabalStandardsSay/wgss-app
python3 scripts/backup_public_data.py --verify-only
python3 scripts/verify_source_data.py
WGSS_OFFLINE=1 node scripts/build-github-pages.mjs /tmp/wgss-restored
```

`/tmp/wgss-restored/`를 웹서버의 `/WhatGloabalStandardsSay/wgss/` 경로로 제공합니다. 이 모드는 기존 EC2 및 기존 백엔드가 없어도 검색·조회할 수 있습니다. 승인된 추가 이미지도 로컬 파일로 제공합니다. 제안·검토·승인은 읽기 전용 복구 모드에서 실행하지 않습니다.

백엔드를 유지하고 EC2만 교체하는 경우에는 `WGSS_OFFLINE`을 생략해 빌드하고, `deployment/ec2/README.md`에 따라 nginx와 새 IP·도메인의 인증서를 준비합니다. 기존 TLS 개인키의 재사용은 필요하지 않습니다. 새 조회 origin을 백엔드의 `WGSS_PUBLIC_FRONTEND_ORIGINS`에 추가합니다.

## 수집 작업 재설치

1. Node/Python/Docker 및 Chromium 시스템 의존성을 설치합니다.
2. `deployment/collection/install.sh`, `.service`, `.timer`에 남은 `/home/ubuntu` 경로를 새 경로로 맞춥니다.
3. `BEDROCK_API_KEY`를 새 서버의 설치 프로세스 환경에서 설정하고 `deployment/collection/install.sh`를 실행합니다. 비밀 값은 Git에 저장하지 않습니다. 기존 호스트에서 암호화한 systemd 자격증명은 복사해서 재사용하지 않습니다.
4. `systemctl list-timers wgss-collection.timer --all`과 첫 실제 완료 결과를 확인합니다. 기존 서버의 타이머를 중지해 두 곳에서 동시 수집하지 않게 합니다.

로컬 후보 큐는 공개 Git에 옮기지 않습니다. 수집기는 기본 자료와 현재 공개 승인 자료로 중복을 확인하므로 새 서버에서도 이미 게시한 원문 쌍·이미지를 다시 게시하지 않습니다. 미승인 수집 후보는 재수집하거나 별도의 비공개 경로로 이전합니다.

## 백엔드까지 교체할 때

`deployment/public-intake/`에 공통 서버를 빌드하는 패키지가 있고 `drizzle/`에 DB 스키마가 있습니다. 현재 중앙 Sites의 D1·R2는 EC2와 별도 자원입니다. EC2 교체만으로 이 DB와 사진이 사라지는 구조는 아닙니다.

백엔드 교체에는 새 DB·파일 저장소, 새로운 배포 설정 및 런타임 비밀 설정이 필요합니다. `.env.example`의 변수 이름을 사용하고, 새 API 주소를 프런트의 `WGSS_INTAKE_BASE`와 수집기 `deployment/collection/config.json`에 반영합니다. 읽기용 백업은 전체 운영 DB 덤프가 아니므로 기존 제안·승인 이력까지 그대로 이전하려면 중앙 D1·R2를 별도로 비공개 내보내기/가져오기 해야 합니다. 공개 조회는 그동안 위 복구 모드로 유지할 수 있습니다.
