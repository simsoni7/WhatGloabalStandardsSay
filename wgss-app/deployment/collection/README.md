# 정기 자료수집

EC2의 `wgss-collection.timer`가 매일 **03·09·15·21시(한국시간)**에
`wgss-collection.service`를 실행합니다. 터미널·Codex 세션을 닫거나 서버가
재부팅되어도 예약을 유지하며, 놓친 예약은 부팅 후 한 번 실행합니다.
기존 Sites의 비활성 예약은 다시 켜지 않습니다.

## 수집과 반영

- 금융사: 설정된 공식 도메인 16곳을 순환합니다. 회차당 4개 시작 URL과,
  Bedrock이 실제 페이지에서 고른 같은 금융사 링크를 최대 1단계 조사합니다.
  새 브라우저에서 공개 GET만 사용하고 로그인·입력·거래·쿠키 동의는 하지 않습니다.
  캡처 이미지·가시 문구·최종 URL·시점·해시를 보존합니다.
- 언어팩: Unicode CLDR 통화명과 Apache OFBiz 회계 UI 원문을 번갈아 조사합니다.
  CLDR 35개 언어, OFBiz 16개 언어를 각각 순환합니다. 언어 2개에서 최대 18쌍씩
  새 후보를 추출하며 동일 통화 코드·XML 키로 원문을 대응합니다.
  매 실행 시 공식 저장소의 최신 커밋을 조회한 뒤 **고정 SHA URL**에서 읽습니다.
  LICENSE·NOTICE와 원천 파일 해시를 함께 보관합니다.
- AI: 기존 Bedrock 게이트웨이의 `claude-sonnet-5`를 사용합니다.
  동시 호출 2개, 회차당 최대 12개입니다. 모델은 분류·품질 검사를 담당합니다.
  없는 문구나 번역을 만들지 않습니다. 응답 키 누락·중복·잘림은 실패 처리합니다.
- 접수: 회차당 화면 2건·용어 6건까지 중앙 접수 API로 보냅니다.
  남은 후보는 SQLite 큐에서 보존하며 다음 회차에 전송합니다.
  시간당 자동 접수는 최대 9건으로 제한하고, 429·통신 실패 시 다음에 재시도합니다.
  제안 토큰과 파일 ID를 재사용하므로 중복 제안·사진을 만들지 않습니다.
- 게시: 관리 화면의 **제안 검토**에서 사람이 확인하고 승인합니다.
  검토 전 수집 후보는 공개 화면·소개 페이지 수치에 포함하지 않습니다.
  승인된 화면·용어는 기존 API 집계로 소개 페이지에 반영됩니다.

공식 웹의 전체를 무제한 검색하거나 금융업무의 완료를 검증하는 배치는 아닙니다.
접근 제한·오류·빈 화면·본문을 가리는 동의 창은 후보에서 제외합니다.
금융사별 실패가 있어도 다른 금융사와 언어팩 조사를 계속합니다.
언어팩 대기열이 120건 이상이면 신규 추출을 쉬고 기존 후보부터 전송합니다.

## 실행 환경

소스: `/home/ubuntu/wgss-github/wgss-app/`

- Python 가상환경: `/home/ubuntu/wgss-collection-runtime/.venv`
- 큐·원문·캡처·회차 결과: `/home/ubuntu/wgss-collection-state/` (저장소 밖)
- Bedrock 키: `/etc/credstore.encrypted/wgss-bedrock`
  (`systemd-creds` 호스트 암호화, 서비스 `LoadCredentialEncrypted`로만 읽음)
- 공개 상태: [collection-status.json](https://3.36.58.188/collection-status.json)
  — 시점·다음 예약·시도/성공/제외·모델 호출·검토 접수·오류 코드만 공개합니다.
  키·제안 토큰·원문·사용자 사진은 포함하지 않습니다.

실행 중 상태가 25분을 넘으면 systemd가 종료합니다. 종료 후 처리기는 시간 초과도
상태 파일에 실패로 남깁니다. 일부 출처 실패는 `partial`로 표시하며 다음 예약은
유지합니다. 다음 예약 시각과 결과 시각이 실제 현재 시점과 맞는지 함께 확인합니다.

## 설치·운영

Python venv와 Chromium 실행용 OS 라이브러리를 준비합니다. 위 경로를 사용하는
현재 EC2에서는 `BEDROCK_API_KEY`가 설치 프로세스 환경에 있는 상태로 실행합니다.
다른 서버는 서비스 파일의 경로·사용자와 nginx 상태 URL 설정을 조정합니다.

```sh
bash deployment/collection/install.sh
systemctl list-timers wgss-collection.timer --all
systemctl show wgss-collection.service -p ActiveState -p Result -p ExecMainStatus
journalctl -u wgss-collection.service -n 20 --no-pager
```

수동 1회 실행: `sudo systemctl start wgss-collection.service`

예약 중단: `sudo systemctl disable --now wgss-collection.timer`

키 갱신: 새 키를 설치 환경변수로 전달한 뒤 설치 스크립트를 재실행합니다.
키를 명령행 인자·Git·로그·일반 설정 파일에 적지 않습니다.

공개 상태 경로는 `deployment/ec2/nginx-https.conf`에 있습니다.
실행 상태 파일은 프런트 빌드 폴더 밖에 두므로 프런트 재배포에 지워지지 않습니다.
설정은 `config.json`, 수집기는 `scripts/collection_batch.py`입니다.

```sh
python3 -m unittest discover -s tests -p test_collection_batch.py -v
```
