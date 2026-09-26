# newWork v2 Phase 1–2 migration plan

> 마지막 업데이트: 2026-09-26

## 범위와 기준

원본 설계는 [newwork-v2-spec.md](newwork-v2-spec.md)이다. 이 문서는 현재 `claude/loving-newton-BjOEj`의 `d02bf32`를 기준으로 기존 파일과 v2 기억 구조의 역할을 매핑한다. 기존 파일은 이번 단계에서 삭제하거나 일괄 변환하지 않는다. `origin/claude/loving-newton-BjOEj`보다 로컬 커밋이 2개 앞서 있고, 원격 최신 상태는 별도로 확인하지 않았다.

현재 저장소에는 템플릿과 `docs/decision-log.md`가 있으나, 루트의 실제 `plan.md`, `todo.md`, `work.md`, `history.md`는 없다. `scripts/loop-agent-poc.sh`에는 이미 reviewer 제한 재시도와 telemetry가 있다. v2 Phase 2는 이 기존 PoC를 호출하거나 수정하지 않는다.

## 중복과 전환 결정

| 기존 | 겹치는 v2 역할 | 처리 | 전환 방법 |
|---|---|---|---|
| `brainstorming.md` 양식 | 초기 입력 원본 | 유지 | 사용자 발화를 가공하지 않은 원본으로 둔다. |
| `plan.md` 양식 | `PLAN.md`와 일부 겹침 | 유지, 향후 통합 | 기존 프로젝트는 그대로 사용. 새 프로젝트의 계획 파일명과 구조는 Phase 3 전에 결정한다. 현 단계에서 자동 변경하지 않는다. |
| `todo.md` 양식 | `STATE.open_tasks`와 중복 | 자동생성 후보 | v2가 실제 프로젝트에 적용되면 STATE에서 대시보드를 생성한다. 지금은 템플릿을 보존한다. |
| `work.md` 양식 | `events.jsonl`과 중복 | 자동생성 후보 | 원장은 event로 두고 사람이 읽는 체크리스트는 파생 뷰로 검토한다. 기존 체크박스는 자동 이관하지 않는다. |
| `history.md` 양식 | `events.jsonl`과 중복 | 유지 후 통합 후보 | 주간 서술은 사건 원장과 다르다. 후속 단계에서 event 요약으로 대체 가능한지 판단한다. |
| `docs/decision-log.md`, `templates/decision-log.md` | `DECISIONS.md` | 유지, 새 항목은 통합 대상 | 과거 결정을 새 파일로 복사하지 않는다. v2 파일은 기존 로그를 링크하고 향후 결정의 기록 형식은 Phase 3 전에 정한다. |
| `templates/troubleshooting.md` | `.newwork/incidents/` | 유지 | 양식은 사건별 파일에 재사용 가능. 기존 로그를 자동 이동하지 않는다. |
| `templates/retrospective.md` | `RETROSPECTIVE.md`, `LESSONS.yaml` | 유지 | 회고 원문과 재사용 교훈은 분리한다. 교훈 승격은 Phase 4 이후. |
| `CLAUDE.md` 13번 Lessons Learned | `.newwork/LESSONS.yaml` | 유지, 향후 중복 검토 | 사용자 승인 교훈을 기계적으로 복제하지 않는다. Phase 4에서 범위와 효과 근거를 붙여 이관한다. |
| 기존 PoC `scripts/loop-agent-poc.sh` | v2 Inner Loop | 유지 | 이미 존재하는 기능이나 Phase 1–2에 포함하지 않는다. v2 인터페이스 연결은 Phase 3로 남긴다. |

`STATE.yaml`은 현재 상태를 표시하는 재생성 가능한 스냅샷, `events.jsonl`은 변경 이력 원장, `FINDINGS.yaml`은 근거와 상태가 붙은 사실 목록이다. `DECISIONS.md`는 선택 이유를 쓰는 문서이며 event와 동일한 대체물이 아니다. `LESSONS.yaml`은 이번 단계에서 빈 파생 구조만 만들고 자동 학습은 하지 않는다.

## Phase 2 최소 계약

- `./run.sh memory init`이 `.newwork/`를 초기화한다. 기존 동일 이름의 파일은 덮어쓰지 않는다.
- `./run.sh memory start ID`가 Git 브랜치, HEAD, `.newwork` 이외 작업 트리 지문을 확인하고 세션을 연다. 이전 세션과 달라졌으면 자동 덮어쓰기 없이 중단한다.
- `./run.sh memory request-confirmation ID "질문"`과 `resolve-confirmation ID "답"`은 열린 확인을 event와 STATE에 동시 반영한다.
- `./run.sh memory finding ID "주장" STATUS --evidence 상대경로`는 파일 존재·저장소 내부 여부를 확인하고 SHA-256으로 근거를 연결한다. `CONFIRMED`·`REFUTED`·`EVIDENCE_FOUND`는 근거 파일이 필수다.
- `./run.sh memory open-task ID "제목"`, `close-task ID`로 열린 작업을 추적한다.
- Phase 2.5부터 `./run.sh memory end ID --next-start "다음 시작점"`이 세션을 닫는다. `reconcile`은 현재 snapshot과 event, Git 상태를 비교하고 `rebuild`는 event에서 snapshot을 재생성한다. 검토된 Git 변경은 열린 세션 중에도 `accept-git "이유"`로 원장에 기록한 뒤 기준 상태로 받아들인다. 상세 계약은 [newwork-v2-session-contract.md](newwork-v2-session-contract.md)를 따른다.
- JSON 문법은 YAML 1.2의 하위집합이므로 `.yaml`은 별도 패키지 없이 JSON으로 기록한다. 사람이 YAML 문법으로 직접 편집한 파일은 이 CLI가 읽지 못한다.

## 안전한 이관 순서

1. Phase 1–2를 임시 Git 저장소 테스트로 검증한다.
2. 이 저장소에 v2 파일을 초기화한다. 기존 문서의 내용을 새 원장에 사실로 자동 삽입하지 않는다.
3. 실제 프로젝트 적용 전, 사용자 문서의 확정 결정·미완료 작업 중 옮길 항목을 개별 검토한다. 원본 파일과 SHA/경로를 evidence로 남기고 상태를 `UNVERIFIED`부터 시작한다.
4. Phase 3에서 계획 파일명, 파생 대시보드, PoC 연결 여부를 결정한다. 중복 파일 삭제는 그 이후 사용자 검토로 미룬다.

## 현재 한계

이 CLI는 Codex나 Claude의 자동 세션 훅에 아직 연결되지 않는다. `run.sh memory start/end`를 호출해야 동작한다. Git 지문은 작업 트리 변화를 감지하지만 원격 branch freshness를 증명하지 않는다. `reconcile`은 evidence 파일의 SHA-256도 재검사하지만, 바뀐 근거의 의미를 자동 판정하지 않는다. 이벤트 해시 체인은 우발적 손상 탐지용이지 접근 제어·변조 방지 보안 경계가 아니다. Pending confirmation의 사용자 답변은 명령 입력을 그대로 기록하므로 비밀정보를 넣지 않아야 한다.
