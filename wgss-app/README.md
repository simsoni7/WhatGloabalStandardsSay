# WGSS — 통합 소스코드와 데이터

이 폴더는 WGSS의 프런트엔드, 백엔드, DB 구조, 배포 설정과 금융사 화면·다국어 언어팩을 모은 다운로드 단위입니다.

- 서비스: https://3.36.58.188/WhatGloabalStandardsSay/wgss/
- 소스: https://github.com/simsoni7/WhatGloabalStandardsSay/tree/wgss-integration/wgss-app
- ZIP: https://github.com/simsoni7/WhatGloabalStandardsSay/archive/refs/heads/wgss-integration.zip

ZIP을 풀고 `WhatGloabalStandardsSay-wgss-integration/wgss-app/`를 사용합니다. 저장소의 기본 브랜치는 기존 용어집 배포본입니다. 위 소스·ZIP 링크는 통합 브랜치를 직접 가리킵니다.

## 포함 내용

| 경로 | 내용 |
|---|---|
| `integration-ui/` | 화면 검색, 용어, 회사별 기능, 제안·검토·승인 UI |
| `server/` | 공개 접수, 검토·승인, AI 분석, 버전, 게시 반영, 조사 작업 API |
| `db/`, `drizzle/` | DB 테이블 정의와 SQL 마이그레이션 |
| `integration-data/` | 화면·문구·금융업무·회사별 기능 목록, 언어팩 행, 원천 근거 |
| `public/assets/` | 공개 수집·제공 승인된 금융사 화면 이미지 |
| `deployment/public-intake/` | 실제 공개 접수 서버의 Worker 진입점, 바인딩, 재현 빌드 |
| `deployment/ec2/` | 프런트 nginx, 80/443 설정, TLS 발급·갱신, 빌드·서비스 설정 |
| `app/`, `build/`, `components/`, `hooks/`, `vendor/`, `lib/` | Sites native 앱과 UI 지원 코드 |
| `scripts/`, `tests/` | 수집·분류·빌드 도구와 검증 |
| `SOURCE_DATA_MANIFEST.json` | 포함 파일 SHA-256과 데이터 범위 |

화면 사례 183건, 화면 문구 1,730건, 전체 원천 언어팩 26,245쌍과 출처·원문 대응 근거가 포함됩니다. 상업적 이용 조건을 충족하는 공개 검색 데이터는 16,424쌍으로 제한합니다. 원천 관측 자료의 포함이 재사용 권리의 일괄 허용을 뜻하지 않습니다. 각 언어팩의 라이선스·NOTICE·출처를 보존합니다. 금융사 스크린샷도 각 금융사의 화면이며 WGSS가 저작권을 부여하는 자료는 아닙니다.

공개 화면 및 문구에서 참조하는 서로 다른 이미지 188장을 파일로 포함합니다. 이미지와 각 언어팩·원천 근거 파일의 SHA-256을 검증할 수 있습니다.

## 다운로드 데이터 검증

Python 3 표준 라이브러리만 사용합니다. Git 설치나 실행 서버가 필요하지 않습니다.

```sh
cd wgss-app
python3 scripts/verify_source_data.py
```

이 명령은 파일 목록·해시, 화면 이미지, 언어팩 행·출처 파일을 확인합니다. 운영 로그와 미승인 제보는 포함하지 않습니다.

## 프런트엔드 빌드

Node 22.16 이상을 사용합니다. 정적 프런트 빌드에는 npm 설치가 필요하지 않습니다.

```sh
node scripts/build-github-pages.mjs /tmp/wgss-public
node tests/public-commercial-policy.mjs /tmp/wgss-public
```

생성된 `/tmp/wgss-public`을 `/WhatGloabalStandardsSay/wgss/` 경로에 게시합니다. 환경 변수 `WGSS_PUBLIC_BASE`로 게시 경로, `WGSS_INTAKE_BASE`로 중앙 API 주소를 바꿀 수 있습니다. 현재 EC2는 이 정적 프런트를 제공하며, 조회·제안·공개 검토는 중앙 API에 연결됩니다. 승인된 자료·버전은 API에서 즉시 읽고, API에 연결할 수 없으면 동봉된 승인 스냅샷을 사용합니다.

EC2 배포는 `deployment/ec2/README.md`를 참고합니다. 인증서와 개인키는 새 환경에서 발급하거나 별도로 이전해야 합니다.

## 공개 접수·검토 백엔드 빌드

```sh
cd deployment/public-intake
npm ci
npm run build
npm run validate
```

Worker는 공통 `server/`와 `integration-ui/`를 직접 사용합니다. 복사된 서버 소스를 따로 유지하지 않습니다. 빌드된 `dist/`를 Sites ESM Worker로 배포하고 `DB`(D1), `BUCKET`(R2) 바인딩을 연결합니다. `.openai/drizzle`의 SQL을 순서대로 적용합니다. 실제 API 키·런타임 환경값은 호스팅 환경에 설정합니다. `.env.example`에는 변수 이름과 공개 검토 설정만 있습니다.

현재 운영 설정은 `WGSS_PUBLIC_REVIEW=true`입니다. 제안 조회, AI 자동 추천, 검토·승인, 버전 생성은 로그인 없이 가능합니다. 전역 설정·비밀정보·임의 작업 실행은 공개 검토 권한에 포함되지 않습니다. 신규 제보 업로드는 제보별 capability token으로 연결합니다. 플랫폼 인증 헤더는 Sites의 검증된 게이트웨이에서만 사용합니다.

`app/api/wgss/route.ts`는 native 앱용 `handleRequest` 경로입니다. 현재 공개 접수 서버의 실제 경로는 `deployment/public-intake/worker/index.js`의 `handleIntake`입니다. 두 진입점을 혼동하지 마세요.

## Native 앱 빌드

```sh
npm run install:ci
python3 scripts/prepare_fullstack_public.py sync
npm run build
```

기존 `.openai/hosting.json`은 native Site 프로젝트 설정입니다. 새 호스팅에서는 해당 프로젝트와 DB·버킷 바인딩을 준비합니다. 공개 접수 전용 배포는 앞 절의 별도 패키지를 사용합니다.

## 운영 데이터와 제외 항목

금융사 화면·목록·언어팩은 소스에 포함합니다. API 키, 실제 `.env`·`.dev.vars`, 인증서 개인키, 운영 로그, 미승인 사용자 사진·제보는 포함하지 않습니다. D1의 실시간 접수·승인·변경 이력과 R2의 신규 업로드는 운영 저장소에 있습니다. 이 ZIP은 새 환경을 구성할 수 있는 소스와 공개 데이터이며, 운영 DB·버킷의 시점 백업은 별도 작업입니다.

정기 시장조사는 URL 변경 감지와 실행 로직을 포함하지만, 현재 운영 예약은 활성화하지 않았습니다. 실행 대상을 등록하고 주기를 설정해야 자동 실행됩니다.

### 화면 문구 보강

문구가 1개 이하였던 원본 이미지 66장을 이미지 해시와 연결해 재분석했습니다. 기존 736건을 보존하고 Bedrock 기반 문자 추출 994건을 추가했습니다. `integration-data/screen-text-transcriptions.json`에 이미지 해시·추출 방법·모델을 기록합니다. 화면의 최신성이나 번역 검증을 뜻하지 않습니다.

재적용: `python3 scripts/enrich_screen_text.py --apply`. 새 추출은 Pillow 설치 후 `BEDROCK_API_KEY` 환경변수와 `--collect`를 사용합니다. 원본 이미지와 수집일은 변경하지 않습니다.
