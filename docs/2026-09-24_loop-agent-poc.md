# Loop Agent 최소 PoC

목표는 기존 `CLAUDE.md`의 원칙을 바꾸지 않고 다음 역할 분리를 실제 실행 가능한 형태로 검증하는 것이다.

`planner → implementer → reviewer → verifier`

## 실행 모델

- planner: `read-only` — 현재 상태를 읽고 계획과 acceptance check를 작성한다.
- implementer: `workspace-write` — planner 결과를 입력으로 받아 최소 변경을 구현한다.
- reviewer: `read-only` — 구현 결과와 diff를 독립 검토한다. `VERDICT: PASS`가 아니면 중단한다.
- verifier: `read-only` — 실제 결과를 독립 검증하고 acceptance check를 실행한다. `VERDICT: PASS`가 아니면 실패한다.
- 각 역할은 별도 `codex exec --ephemeral` 세션으로 실행한다.
- verifier에도 planner 출력을 전달해 계획한 acceptance check를 독립적으로 확인하게 한다.
- 역할별 최종 답변과 로그는 run artifact 디렉터리에 남는다.
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

최소 PoC이므로 reviewer가 FAIL이면 자동 수정 루프를 돌리지 않고 멈춘다. 다음 단계에서 필요하면 `reviewer FAIL → implementer 재수정 → reviewer 재검토`를 제한 횟수로 추가할 수 있다.
