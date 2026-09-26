# Phase 4A — Project Lesson Contract

> 2026-09-26. 근거가 있는 프로젝트 교훈만 수동 승인한다. 원장은 `.newwork/events.jsonl`, `.newwork/LESSONS.yaml`은 재생성 가능한 projection이다. Global 승격·Skill 생성·다른 프로젝트 자동 적용은 포함하지 않는다.

## 범위와 입력

열린 Memory session에서 `./run.sh memory lesson-propose ID "재사용 주장" --source PATH --support PATH --effect supported|inconclusive|contradicted --effect-note "판단 근거"`를 호출한다. `--support`와 `--contradict`는 반복 가능하고 `--scope project`만 허용한다. source는 회고 또는 관측 원본 파일이다. source와 별개로 최소 하나의 supporting 파일이 필요하며, 그중 하나는 현재 finding에 연결된 근거 또는 `.newwork/runs/<run-id>/` 아래 run artifact여야 한다. 각 참조는 저장소 내부의 해석된 경로와 SHA-256으로 기록한다. 반증 자료가 있으면 `--contradict`로 함께 남긴다. 원장과 파생 snapshot은 자기참조 근거로 사용할 수 없다.

후보에는 `id`, `scope=project`, `claim`, `source`, `supporting`, `contradictory`, `effect={status,note}`가 기록된다. `effect.status`는 사람의 평가이지 자동 계산된 인과 결론이 아니다. 반복 횟수나 회고 원문 하나만으로 `supported` 또는 승인을 만들지 않는다. 제안 직후 status는 `candidate`다.

## 명시적 결정

`./run.sh memory lesson-decide ID approve|reject|withdraw|replace --reason "검토 이유"`를 사용한다. 교체는 `--replacement NEW_ID`가 필수다. 결정 이유는 빈 문자열일 수 없다.

- `approve`: candidate의 effect가 `supported`이고 source·supporting·contradictory가 모두 현재 해시와 일치할 때만 `lesson_approved` event를 기록한다. `inconclusive`·`contradicted`는 `review_required`이며 candidate를 유지한다.
- `reject`: candidate를 `rejected`로 투영한다. 원본 제안은 삭제하지 않는다. stale 후보도 거부하여 정리할 수 있다.
- `withdraw`: approved Project Lesson을 `withdrawn`으로 투영한다. 원래 승인 사건은 유지한다.
- `replace`: approved 기존 ID와 `supported`이고 근거가 최신인 새 candidate ID를 한 `lesson_replaced` event로 연결한다. 기존 교훈은 `replaced`, 새 교훈은 `approved`가 된다.

명령은 사람의 명시적 승인·거부 의사를 전달할 때만 호출해야 한다. CLI는 실제 호출자가 사람인지 인증하지 않으며, agent가 독자적으로 승인을 추론해 실행해서는 안 된다. 이 계약은 사용자의 승인 절차를 대체하지 않는다.

## Projection과 복구

`LESSONS.yaml.items[ID]`는 후보 입력, lifecycle status, 결정 이유와 event 번호, 교체 관계를 보여준다. `rebuild`는 event 원장에서 동일 내용을 재생성한다. `status/reconcile`은 candidate와 approved lesson의 source·근거 SHA를 다시 확인하고 변경·누락 시 `stale_lesson_evidence`와 `review_required`를 반환한다. 오래된 후보는 자동 수정·승격하지 않는다. 거부·철회·대체된 역사 항목은 원장에 보존하되 현재 적용 교훈으로 취급하지 않는다.

`approved`는 특정 근거 상태에서 과거에 승인되었다는 이력이지 현재 재사용 허가가 아니다. 각 항목의 정적 `reuse_policy=live_freshness_check_required`는 이를 명시하며 `LESSONS.yaml`에는 stale 가능한 `usable: true`를 저장하지 않는다. 사용 직전 `./run.sh memory lesson-check ID`를 실행한다. 이 읽기 전용 조회는 원장의 현재 projection과 기존 source·supporting·contradictory 해시 검사로 `reusable`을 계산한다. 현재 status가 `approved`, effect가 `supported`, 모든 참조가 존재하고 기록된 해시와 일치할 때에만 `reusable=true`다. 철회·대체된 항목은 재사용하지 않으며, 교체된 새 항목도 자신의 근거를 독립적으로 통과해야 한다. 조회를 실행할 수 없거나 freshness를 확인할 수 없는 consumer는 자동 적용하지 않는다. `LESSONS.yaml` 단독 읽기만으로 재사용을 결정해서는 안 된다. 이 조회는 새로운 상태나 승인 사건을 기록하지 않는다.

Codex·Claude 등 caller는 같은 core CLI를 사용한다. backend 이름은 교훈 계약의 필수 데이터가 아니다. 기존 `CLAUDE.md` 13번과 start-project Skill은 이번 단계에서 수정하거나 동기화하지 않는다. 승인된 Project Lesson의 다음 프로젝트 조회·import·자동 적용, Global scope와 중앙 inbox, Skill Candidate는 후속 설계 대상이다.
