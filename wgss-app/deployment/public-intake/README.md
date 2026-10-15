# 공개 접수·검토 서버

현재 운영 공개 서버의 ESM Worker를 통합 저장소에서 재빌드하는 패키지입니다.

```sh
npm ci
npm run build
npm run validate
```

- `worker/index.js`: `/api/wgss` → 공통 `server/intake.ts`의 `handleIntake`.
- `scripts/build.mjs`: 공통 UI에서 인라인 자산을 생성하고 서버와 묶습니다. `worker/assets.json`, `worker/governance.json`, `dist/`는 생성물이므로 Git에 넣지 않습니다.
- `.openai/hosting.json`: 현재 공개 Site의 프로젝트와 `DB`·`BUCKET` 바인딩 이름. 인증정보가 아닙니다.
- `dist/.openai/drizzle`: 공통 DB 마이그레이션 사본.
- 런타임 변수는 최상위 `.env.example` 참고. 비밀 키를 파일에 저장하거나 커밋하지 않습니다.
- `WGSS_PUBLIC_READER_BASE`: 정적 프런트 주소. 기본값은 공식 EC2 주소입니다.

Worker는 Sites 게이트웨이의 검증된 플랫폼 사용자 헤더를 전제로 합니다. 일반 인터넷 서버에서 임의 헤더를 그대로 신뢰하도록 재현하지 않습니다. 공개 검토는 `WGSS_PUBLIC_REVIEW`의 제한된 액션을 사용합니다.

현재 운영 배포의 서버 핵심 로직은 이 저장소와 동일합니다. 이 패키지는 흩어져 있던 진입점·빌드 코드를 공통 소스에서 재생성하도록 정리한 것으로, 배포 자체를 다시 실행하지는 않습니다.
