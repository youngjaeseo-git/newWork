기존 패치 검증 완료. 소스 수정은 하지 않았습니다.

- status: .lock을 rb + LOCK\_SH로 열고, mutation은 a+b + LOCK\_EX 유지 확인.
- 4개 lock acceptance test: 모두 PASS.
- 테스트 시작 시 LOOP\_AGENT\_POC\_TASK\_ID, ...OPEN\_EVENT, ...RUN\_DIR unset 확인. 명시적 task-bound 테스트는 별도로 값을 설정해 정상 동작 확인.
- 상속 환경변수를 의도적으로 넣고 실행한 ./run.sh test: Loop 테스트 PASS, Memory 테스트 35개 전부 OK.
- 이 Loop 테스트는 fake Codex 기반 테스트이며 실제 모델 E2E로 간주하지 않음.
- 최종 git diff --exit-code: clean.
- 현재 HEAD: 137226b.
- 기존 untracked production-readonly-status-verification-\* 3개만 그대로 존재하며 새 artifact는 남기지 않음.
- 별도 legacy-init 변경은 포함하지 않음.

Reviewer/verifier의 독립 단계에서는 같은 계약을 별도로 재검증하면 됩니다.

IMPLEMENTATION: COMPLETE