계획:

- Implementer: 기존 코드 무수정 상태에서 지정된 4개 lock 테스트만 실행하고, parent LOOP\_AGENT\_POC\_\* 3개 환경변수를 주입한 채 ./run.sh test 실행. legacy init 제외.
- 확인 대상: status는 기존 .lock을 rb + LOCK\_SH, mutation은 a+b + LOCK\_EX; loop 테스트 시작 시 3개 inherited 변수를 즉시 unset하고 bound-path 케이스에서만 재설정.
- Acceptance: 4 tests PASS, 전체 test PASS, git diff --exit-code 성공, source/test SHA-256 불변, commit/push 없음.
- Reviewer/verifier: implementer의 실제 로그를 독립 검토하고 소스 계약과 대조. read-only 환경에서는 temp-dir 필요 테스트를 재실행하지 않음.
- 위험: 이전 ...-03은 reviewer 출력 뒤 공백 때문에 verifier 0회로 종료됨. 이번에는 최종 프로토콜 줄 뒤 아무 문자도 두지 않아야 함.

IMPLEMENTATION: COMPLETE