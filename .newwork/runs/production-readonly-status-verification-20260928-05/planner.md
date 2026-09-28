계획:

- Implementer는 legacy-init 제외, 4개 lock 테스트(status read-only, uninitialized no-create, writer↔reader blocking)를 실행한다.
- 부모 LOOP\_AGENT\_POC\_\* 3개를 주입해 ./run.sh test; 테스트 진입부 unset 격리를 확인한다.
- 기준 계약: status=rb+LOCK\_SH, mutation=a+b+LOCK\_EX.
- Acceptance: 현재-run 로그 PASS, source/test SHA-256 불변, tracked diff 없음.
- Reviewer/verifier는 현재-run 로그와 코드/hash를 독립 대조한다. read-only sandbox에서 temp-dir 테스트 재실행 금지.
- 위험: 이전 run03/04 로그 재사용, prior run artifacts를 새 증거로 오인.

IMPLEMENTATION: COMPLETE