Memory status 수정은 구현 완료했습니다.

- status만 기존 .lock을 rb + LOCK\_SH로 열며 파일/디렉터리를 생성하지 않습니다.
- mutation/reconcile/rebuild 등 기존 경로는 a+b + LOCK\_EX를 그대로 유지합니다.
- read-only status, reader/writer 상호 blocking, 미초기화 시 무쓰기 동작 회귀 테스트를 추가했습니다.
- Memory 전체 35개 테스트 PASS, git diff --check PASS.
- 독립 reviewer: blocking finding 없음.
- 독립 verifier: Memory/replay/idempotency/checkpoint 관련 PASS.
- commit/push는 하지 않았습니다.

남은 blocker는 기존 Loop Agent 테스트입니다. tests/test-loop-agent-poc.sh가 RC 2로 실패하며, 현재 테스트가 /tmp/.../run을 사용하지만 Loop 구현은 workspace/.newwork/runs/<run-id>만 허용합니다. 동일 테스트를 수정 전 HEAD 스냅샷에서 별도로 실행해도 똑같이 실패하므로 이번 Memory 변경의 회귀는 아닙니다. 요청 범위상 Loop 코드는 수정하지 않았습니다.

따라서 Memory 수정 자체는 검증됐지만, 요구된 전체 Loop suite가 현재 HEAD에서 통과하지 않아 최종 acceptance는 완료로 표시할 수 없습니다.

IMPLEMENTATION: BLOCKED