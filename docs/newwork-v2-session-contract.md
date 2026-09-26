# Phase 2.5 — Session Integration Contract

> 2026-09-26. 이 문서는 newWork core의 CLI 계약이다. Codex·Claude 내부 이벤트 형식이나 자동 hook 설치를 전제로 하지 않는다. 기존 v2 migration은 [newwork-v2-migration.md](newwork-v2-migration.md)를 따른다.

## 경계와 기본 운영

기본값은 LEVEL 1: `/start-project` 또는 agent workflow가 명시적으로 같은 core 명령을 호출한다. LEVEL 0(사람의 직접 호출)은 언제나 가능하다. LEVEL 2(native hook)는 아직 설치하지 않는다. Codex adapter, Claude adapter, 미래의 내부 모델 adapter는 인자 변환과 결과 표시만 담당하며 상태·원장·별도 저장 형식을 갖지 않는다. `memory evidence` 별칭도 만들지 않는다. 근거는 `finding --evidence`로 기록한다.

| 수준 | 신뢰성 | 이식성 | 누락 가능성 | vendor 의존 | 복구 |
|---|---|---|---|---|---|
| LEVEL 0 직접 호출 | 사람이 실행하면 명확 | 높음 | 높음 | 없음 | `status/reconcile/rebuild` |
| LEVEL 1 명시적 workflow | 호출 절차를 점검 가능 | 높음 | 중간 | 낮음 | 동일 core CLI 재호출 |
| LEVEL 2 native hook | 제품 이벤트에 좌우 | 낮음 | hook 실패 가능 | 높음 | core ledger에 의존; 이번 범위 밖 |

## CLI와 결과

모든 명령은 `./run.sh memory <명령>`으로 호출한다. `--root`는 core script의 옵션이며 `run.sh`는 현재 저장소 루트를 넘긴다. 정상/실패 모두 stdout에 JSON 한 객체를 반환한다. `status` 문자열은 기계 판독용이며 메시지 텍스트는 계약이 아니다. 종료 코드: `ok=0`, `invalid_input=2`, `conflict=10`, `review_required=11`, `ledger_corrupt=12`, `invalid_evidence=13`, `io_error=14`. `status` 조회는 검토 항목을 JSON으로 보여줘도 종료 코드 0이고, `reconcile`은 검토 항목이 있으면 11이다. 잘못된 CLI 문법은 argparse 오류로 종료 코드 2다.

| 명령 | 필수 입력 | 선택 입력 | 성공 출력 핵심 | 멱등성/재실행 | 실패 시 행동 |
|---|---|---|---|---|---|
| `status` | 없음 | 없음 | active session, Git drift, stale evidence, pending confirmations | 읽기 전용, 반복 가능 | 원장 손상은 12 |
| `start ID` | 고유 세션 ID | 없음 | event_seq, active_session | 동일 요청은 `replayed: true` | 다른 active 세션은 10; Git drift는 11 |
| `finding ID CLAIM STATUS --evidence PATH` | ID, 주장, 상태; 특정 상태는 근거 | `--evidence` 반복 | event_seq, active_session | 같은 세션·동일 정규화 내용·근거 해시 재호출은 replay; 내용/해시 변경은 새 finding event | 잘못된 근거는 13; 기존 event 불변 |
| `end ID --next-start TEXT` | active ID, 다음 시작점 | 없음 | event_seq, active_session=null | 동일 요청은 replay | HEAD/근거 변경은 11, active 유지; 확인 후 같은 명령 재실행 |
| `interrupt ID REASON` | active ID, 이유 | 없음 | event_seq, active_session=null | 동일 요청은 replay | ID 불일치는 10; pending 작업/확인 보존 |
| `reconcile` | 없음 | 없음 | snapshot/Git/근거 차이 | 읽기 전용 | 차이가 있으면 11; 자동 수락·삭제 없음 |
| `rebuild` | 없음 | 없음 | event_seq | 반복 가능 | 손상된 원장은 12; 원장 수정 없음 |
| `accept-git REASON` | 사람 검토 이유 | 없음 | event_seq | 매 호출은 새 수락 사건 | 관찰한 Git 상태와 검토한 파일 tree identity를 기록; 근거 의미는 수락하지 않음 |

기존 `request-confirmation`, `resolve-confirmation`, `open-task`, `close-task`는 유지한다. `init`은 기존 파일을 덮어쓰지 않는다. 명령별 출력의 `event_seq`는 성공 시 기록한 사건 번호이며 replay 시 원래 사건 번호다.

## 단일 멱등성 규칙

`start/end/finding/interrupt`는 모두 명령 이름과 정규화된 요청 JSON의 SHA-256 `request_fingerprint`를 이벤트에 기록한다. 재호출 시 원장에서 같은 fingerprint를 찾더라도 현재 active session과 원래 사건의 결과를 공통 규칙으로 대조한다. 종료 사건은 그 사건이 마지막 lifecycle 사건이어야 replay 가능하다. 현재 의미가 달라졌다면 `conflict`를 반환하며, 일치할 때만 새 사건 없이 `replayed: true`를 반환한다. `finding`의 정규화 요청에는 active session ID, 주장, 상태, 증거 경로와 현재 SHA-256이 포함된다. 따라서 변경된 근거를 재기록하면 새 사건이다. 현재 finding projection이 이후 변경되었다면 예전 요청은 replay하지 않고 `conflict`로 멈춘다. 종료된 ID의 `start` 재호출도 현재 active 상태와 맞지 않아 `conflict`다. 새 세션에는 새 ID를 사용한다. fingerprint에는 timestamp와 작업 트리 지문을 넣지 않는다. 이전 Phase 2 event에는 fingerprint가 없으며 읽기·재생성은 가능하지만 소급 replay 보증은 하지 않는다.

## Lifecycle과 recovery

정상 흐름: `status` → `start` → 열린 상태/미해결 확인 → 작업과 `finding`·확인 기록 → 검증 → `end` → `reconcile`. 기존 세션이 end 없이 멈추면 `status`로 active ID를 찾고 같은 세션에서 작업을 계속한다. 별도 `resume` 명령은 복구 상태를 바꾸지 않고 고유 정보도 제공하지 않아 제거했다. 의도적으로 중단할 때만 `interrupt`하며 pending 확인과 작업은 지우지 않는다. 중복 start/end는 현재 상태가 여전히 맞을 때만 fingerprint replay다. agent crash나 projection 쓰기 중단 후에는 `rebuild`로 원장을 STATE/FINDINGS/LESSONS에 재투영한다. 원장이 손상되면 자동 절단·수정하지 않고 `ledger_corrupt`로 멈춘다.

세션 중 HEAD가 바뀌거나 기록된 근거 SHA가 바뀌면 `end`는 `review_required`를 반환하고 active 상태를 유지한다. HEAD 변경은 사람이 diff를 검토한 뒤 `accept-git "검토 이유"`로 기준을 갱신한다. 근거 변경은 의미를 확인한 뒤 같은 finding ID로 현재 근거를 다시 기록한다. 그 후 원래 `end` 요청을 재실행한다. `accept-git`은 evidence를 승인하지 않는다. 일반 작업 트리 변경은 end를 막지 않지만 `reconcile`에서 차이로 보일 수 있다. Git 원격 최신성은 이 계약이 증명하지 않는다.

`accept-git` 이후 한 번의 checkpoint commit으로 HEAD가 바뀌어도, 같은 branch의 직접 자식 commit이고 승인 당시 파일 tree identity가 정확히 일치하며 전체 Git 작업 트리가 clean일 때만 정상 transition으로 인정한다. identity는 경로·mode·blob을 포함한다. 원장 `events.jsonl`과 재생성 가능한 STATE/FINDINGS/LESSONS만 identity 계산에서 제외하며, `DECISIONS.md`와 incidents/runs 등 사람이 수정 가능한 파일은 포함한다. 제외한 내부 네 파일도 유효한 원장·snapshot이어야 하고 commit된 내용과 현재 내용이 같아야 한다. branch 이동, merge/rebase/multi-commit, 부분·추가 commit, commit 후 변경은 `review_required`다. 이전 `git_reconciled` 사건에 identity가 없으면 소급 승인하지 않는다.

## 구성요소 정리 판단

유지: `.newwork/events.jsonl` 원장과 파생 STATE/FINDINGS/LESSONS, 수동 `run.sh memory`, 원문 계획·회고·결정 로그, 기존 Loop Agent PoC. 통합: Codex/Claude 세션 workflow는 같은 core CLI 호출로 수렴한다. 제거 후보: 중복 상태를 수동 기록하는 todo/work 뷰와 중복 Skill·workflow는 기능 보존 및 사용자 검토 후 판단한다. 이번에는 삭제하지 않는다. 신규 구성요소는 이 계약 문서와 core의 `status/interrupt` 및 공통 fingerprint 처리뿐이다. `resume` 명령과 무의미한 사건을 제거해 구성요소 수를 줄였다. adapter별 저장소나 compatibility layer를 늘리지 않아 상태 책임 중복을 피한다. 사용자의 선택권·복구·검증·backend 독립성은 유지한다.

## 완료 기준과 제한

결정적 임시 Git 저장소 테스트에서 정상 start/end, 중복 및 오래된 replay, crash 후 `status`로 active 확인과 `interrupt`, open session reconcile, stale STATE rebuild, HEAD/evidence 변경 후 동일 end 재시도, Codex→Claude가 같은 `./run.sh memory` CLI를 호출하는 경우를 통과해야 한다. native hook·Phase 3 Inner Loop·Outer Learning Loop·router·새 MCP·dependency는 포함하지 않는다. `CLAUDE.md`와 Loop Agent는 수정하지 않는다.
