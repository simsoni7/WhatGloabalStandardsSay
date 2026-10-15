# EC2 프런트 배포

공식 접속: https://3.36.58.188/WhatGloabalStandardsSay/wgss/

EC2의 nginx가 정적 프런트를 HTTPS 443으로 제공합니다. HTTP 80은 HTTPS로 전환하며 ACME 검증 경로는 유지합니다. 백엔드 API·D1·R2는 중앙 Sites 서버에 연결합니다.

```sh
WGSS_SOURCE_DIR=/path/to/wgss-app WGSS_NODE_BIN=/path/to/node ./build.sh
./start-https.sh
```

`start-https.sh`는 기존 TLS 인증서를 사용합니다. 새로운 서버는 Docker 설치와 외부 80/443 접근을 준비하고, 호스트 경로·IP를 맞춘 뒤 `bootstrap-tls.sh`로 인증서를 발급합니다. `wgss-ip-renew.service`·`.timer`는 갱신 자동화용입니다. 서비스의 절대 경로는 설치 위치에 맞게 수정합니다.

현재 제안 검토·자료 목록·변경 이력은 프런트의 `#admin`에서 로그인 없이 중앙 공개 검토 API를 사용합니다. 익명 API 프록시는 임의 인증·플랫폼 신원 헤더를 제거합니다.

`ASSESSMENT.md`는 최초 배포 당시 검증 기록입니다. 그 문서의 로그인·관리 화면 리디렉션 설명은 이후 공개 검토 개편으로 변경되었습니다. 현재 동작은 이 README와 통합 README를 기준으로 합니다.

인증서·개인키·ACME 계정·로그는 소스에 포함하지 않습니다. 일반적인 새 호스트에서는 IP·도메인·문서 루트·컨테이너 마운트·허용 프런트 origin을 바꿔야 합니다.
