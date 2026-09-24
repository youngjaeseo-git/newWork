# Loop Agent 최소 PoC

목표는 기존 `CLAUDE.md`의 원칙을 바꾸지 않고 다음 역할 분리를 실제 실행 가능한 형태로 검증하는 것이다.

`planner → implementer → reviewer → verifier`

## 실행 모델

- planner: `read-only` — 현재 상태를 읽고 계획과 acceptance check를 작성한다.
- implementer: `workspace-write` — planner 결과를 입력으로 받아 최소 변경을 구현한다.
- reviewer: `read-only` — 구현 결과와 diff를 독립 검토한다. `VERDICT: FAIL`이면 feedback을 implementer에 전달해 제한 횟수만큼 재작업한다.
- verifier: `read-only` — 실제 결과를 독립 검증하고 acceptance check를 실행한다. `VERDICT: PASS`가 아니면 실패한다.
- 각 역할은 별도 `codex exec --ephemeral` 세션으로 실행한다.
- verifier에도 planner 출력을 전달해 계획한 acceptance check를 독립적으로 확인하게 한다.
- 역할별 최종 답변과 로그는 run artifact 디렉터리에 남는다.
- 재작업 시 `implementer-N.md`, `reviewer-N.md`로 시도별 결과를 보존하고, `implementer.md`, `reviewer.md`는 최신 결과를 가리킨다.
- reviewer 재작업은 기본 최대 2회이며 `LOOP_AGENT_POC_MAX_RETRIES`로 조정할 수 있다. 최대 횟수를 넘으면 실패한다.
- verifier FAIL은 자동 재작업하지 않고 즉시 실패한다.
- `summary.txt`에 시작/종료 시각, 소요 시간, 역할별 실행 횟수, reviewer retry 횟수, 최종 상태와 실패 단계/이유를 기록한다.
- 같은 artifact 디렉터리를 재사용하더라도 실행 시작 시 네 역할의 이전 output/log를 모두 지운다.
- PoC 자체는 commit/push를 수행하지 않는다.

## 사용법

```bash
./run.sh loop-poc "할 일을 자연어로 작성"
./run.sh loop-poc "할 일" /path/to/workspace
./run.sh test
```

실제 실행에는 로컬 `codex` CLI 인증/네트워크가 필요하다. 테스트는 가짜 Codex backend를 주입해 오케스트레이션 순서와 sandbox 경계를 외부 네트워크 없이 검증한다.

## 현재 범위

최소 PoC 범위를 유지하며 reviewer feedback에 의한 제한 재작업만 지원한다. planner 재계획이나 verifier FAIL 자동 복구, 역할의 동적 추가/일반화는 하지 않는다.
