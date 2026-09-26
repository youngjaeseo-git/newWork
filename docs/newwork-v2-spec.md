# newWork v2 확정안

작성일: 2026-09-26

## 목적

newWork는 특정 모델용 프롬프트 모음이나 스킬 컬렉션이 아니다.

**프로젝트 경험과 사용자 피드백을 축적하고, 필요한 교훈만 다음 작업에 적용·검증하여, 사용자에게 맞는 AI 작업방식을 지속적으로 개선하는 개인 AI 작업 시스템**이다.

핵심 원칙:
1. 상태는 사람의 기억에 의존하지 않는다.
2. 확정 사실과 미확정 가설을 구분한다.
3. 프로젝트 경험은 해당 프로젝트에서 끝나지 않고 중앙 newWork로 돌아온다.
4. AI가 스스로 할 수 있는 일을 사용자에게 떠넘기지 않는다.
5. 이미 더 좋은 Skill/MCP/도구/OSS가 있는지 필요한 경우 탐색한다.
6. 규칙과 워크플로는 계속 추가만 하지 않고, 효과가 없으면 완화·비활성·제거한다.
7. 강한 최신 모델의 자율성을 오래된 워크플로가 방해하지 않도록 최소 개입을 기본으로 한다.
8. 작업방식은 AI가 성능을 보고 자동 조정할 수 있지만, 권한은 사용자가 승인한다.

## 1. 이중 루프

### Inner Loop
Goal → Work → Verify → Fail이면 Fix → Evidence → Complete

### Outer Loop
Project/Milestone Complete → 측정 + 회고 → Lesson Candidate → 효과 검증 → Keep/Modify/Relax/Remove → Project/Global Lesson → 필요 시 Skill Candidate → 다음 프로젝트

## 2. 기록 구조

- `brainstorming.md`: 무슨 아이디어가 나왔나?
- `PLAN.md`: 무엇을 만들기로 했나?
- `.newwork/STATE.yaml`: 지금 어디까지 왔나? (현재 상태의 유일한 snapshot)
- `.newwork/events.jsonl`: 실제로 무슨 일이 있었나? (append-only event ledger)
- `.newwork/DECISIONS.md`: 왜 이 선택을 했나?
- `.newwork/FINDINGS.yaml`: 무엇이 사실/거짓으로 확인됐나?
- `.newwork/incidents/`: 문제를 어떻게 조사하고 해결했나?
- `.newwork/LESSONS.yaml`: 다음에도 어떤 방식으로 일할까?
- `.newwork/runs/`: 테스트/빌드/스크린샷 등 증거
- `RETROSPECTIVE.md`: 이번 프로젝트 전체는 어땠나?

### Finding 상태
UNVERIFIED / EVIDENCE_FOUND / PENDING_CONFIRMATION / CONFIRMED / REFUTED / SUPERSEDED

## 3. Start / End Hook

Event Log = 원장  
STATE = 현재 snapshot  
Hook = 둘을 언제 정리·검증할지 강제하는 장치

### Session Start
1. STATE 읽기
2. 마지막 event 확인
3. Git 실제 상태 확인
4. STATE ↔ Event ↔ Git 불일치 reconcile
5. Pending Finding / Pending Confirmation 확인
6. 이번 작업에 필요한 Lesson만 로드
7. 작업 시작

### 작업 중
- 중요한 event는 즉시 기록
- 중요한 상태 전환 시 STATE 갱신

### Session End
1. 미기록 event 확인
2. STATE 재생성/갱신
3. 열린 task 확인
4. pending confirmations 정리
5. 다음 시작점 기록
6. consistency check

STATE는 events로 복구 가능해야 한다.

## 4. 열린 문제 닫기

`STATE.yaml.pending_confirmations`에 관리한다.

다시 물어야 하는 시점:
- 미확정 결론 때문에 불필요한 대안 탐색이 계속될 때
- 이후 구현 방향이 달라질 때
- 세션 종료 시 중요한 열린 항목이 남을 때
- 다음 세션 시작 시 여전히 중요한 경우

## 5. 중앙 newWork와 실제 프로젝트

### 중앙 newWork
- 공통 원칙
- 사용자 선호
- Global Lesson
- Skill
- Script
- Model profile
- Learning Engine
- Benchmark / Discovery 기준

### 실제 프로젝트
`newwork init` 또는 `/start-project` 실행 시:

```text
project/
  .newwork/
    STATE.yaml
    events.jsonl
    FINDINGS.yaml
    DECISIONS.md
    LESSONS.yaml
    incidents/
    runs/
```

중앙 규칙 전체를 복사하지 않고 관련 Lesson/Skill만 선택한다.

## 6. Project Lifecycle

### ① Bootstrap
repo 탐색 → branch/dirty state/README/test/build 확인 → 관련 Global Lessons 검색 → `.newwork/` 초기화 → STATE 생성 → 시작 브리핑

### ② Work Loop
Session Start → STATE/Event/Git reconcile → 관련 Finding/Lesson → Plan → Work → Verify → Fix → Evidence → Event → STATE

### ③ Task Checkpoint
Task 완료 시:
- 새 Finding?
- Pending Confirmation?
- Improvement Candidate?
- Lesson Candidate?
- 다음 Task?

### ④ Project Retrospective
- 자동 metric
- 사용자 짧은 평가
- Keep / Problem / Try
- Lesson / Skill 후보

### ⑤ Learning Loop
Project Lesson → 중앙 newWork learning inbox → 중복/evidence/effect 확인 → Project/Global 승격 → Skill Candidate 검증 → newWork 개선

## 7. Better Path Check

다음 시점에만 실행:
1. 계획 확정 전
2. 사용자에게 수동 작업을 요청하기 직전
3. 같은 행동/실패가 반복될 때
4. 검증 시작 전

질문:
- AI가 직접 할 수 있는가?
- 이미 가진 Tool/Script/Skill이 있는가?
- 사용자 개입을 줄일 수 있는가?
- 더 검증 가능한 방법이 있는가?
- 시간/비용/안전성에서 의미 있는 개선인가?

### Manual Action Gate
사용자에게 명령 실행, 로그 복사, 스크린샷 업로드, 파일 재업로드를 요청하기 전에:
1. 내가 직접 할 수 있는가?
2. 자동화할 수 있는가?
3. 정말 불가능한가?
순으로 확인한다.

## 8. External Solution Scout

실행 조건:
- 반복 수동 작업
- 새 Skill/MCP를 만들려는 순간
- 같은 문제를 2회 이상 해결
- 구현 비용이 큰 기능
- 현재 방식보다 개선 여지가 큼

검색 우선순위:
1. 공식 문서
2. 공식 MCP Registry
3. 대표 Agent Skills 저장소
4. GitHub OSS

스타 수는 후보 발견 신호일 뿐 선택 기준이 아니다.

평가 기준:
- 문제 적합성
- 효과 가능성
- 유지보수 상태
- 범용성
- Context 비용
- 설치 복잡도
- 보안
- 사내망 적용 가능성
- 검증 가능성

## 9. Skill 정책

Skill 수 자체는 목표가 아니다.

초기 Core Skill 후보:
- start-project
- resume-project
- verify-completion
- close-task
- retrospective
- promote-lesson

새 Skill 후보 조건:
1. 3회 이상 반복
2. 절차가 유사
3. 입력/출력이 명확
4. 성공 여부를 검증 가능

Lifecycle:
CANDIDATE → ACTIVE → MONITOR → KEEP / RELAX / DEPRECATED → ARCHIVED / REMOVED

Skill은 경험의 결과물이다.

## 10. Model Profile

### LIGHT
강한 모델:
- Core / STATE / Findings 중심
- 높은 자율성
- 필요한 경우만 별도 리뷰

### STANDARD
일반 모델:
- 관련 Lesson
- 필요한 Skill
- Verify Gate

### STRICT
제약이 많거나 약한 모델:
- 작은 Task
- 명확한 scope
- 결정적 test
- 짧은 retry
- 자주 checkpoint

### 자동 조정
새 모델 연결 시 capability probe + 실제 프로젝트 성능을 보고 newWork가 작업방식 프로필을 자동 조정한다.

### 권한은 별도
작업방식: AI가 자동 조정 가능  
권한: 사용자만 승인

AI가 자동 확대하면 안 되는 예:
- push
- merge
- deploy
- 파일 삭제
- secret 접근
- 외부 데이터 전송
- DB 변경

## 11. Pruning / Workflow Diet

각 Rule/Lesson/Skill/Workflow는:
ADD / KEEP / MODIFY / RELAX / DISABLE / REMOVE

새 모델에서는 기존 workflow 전체를 적용하지 않는다.
최소 Core로 baseline을 보고 문제 발생 부분에만 지원을 추가한다.

핵심 원칙:
**newWork는 경험을 축적하지만, 규칙을 축적하는 시스템은 아니다.
경험을 이용해 그 시점에 필요한 최소한의 규칙만 유지한다.**

## 12. 측정

자동 지표 후보:
- 사용자 지시 횟수
- 재지시 횟수
- 같은 failure category 재발
- 근거 없는 완료 선언
- human intervention
- first-pass verification
- wall-clock time
- model/tool call 수
- token/cost
- acceptance test 통과율

사용자 짧은 평가:
- 관리 부담
- 결과 신뢰도
- 재설명 피로도
- 자율성 적절성
- 결과 만족도
- 한 줄 코멘트

## 13. GPU Telemetry 같은 사내 분석

모델 기억에 의존하지 않는다.

- 구조화 사실/수치: DB / DuckDB / SQLite / Parquet
- 장기 지식/해석: Markdown / Findings
- 분석 이력: Analysis Registry

질문 처리:
1. 기존 Finding 확인
2. 기존 Analysis Registry 확인
3. data watermark 확인
4. 새 데이터가 있을 때만 추가 분석
5. 결과/Finding 갱신

정확한 숫자는 SQL.
비슷한 사례 검색은 필요할 때 semantic/vector search.

Hermes / GLM / Kimi 같은 사내 모델에도 적용할 수 있도록 모델 adapter는 교체 가능하게 유지한다.

## 14. 구현 우선순위

### Phase 1 — Spec / Migration
- v2 문서 확정
- 기존 plan/todo/work/history/decision-log/troubleshooting/lessons 구조 매핑
- 삭제/유지/자동생성 결정

### Phase 2 — Memory Foundation
- `.newwork/STATE.yaml`
- `.newwork/events.jsonl`
- `.newwork/FINDINGS.yaml`
- start/end hook
- state rebuild/reconcile
- evidence 구조

### Phase 3 — Inner Loop
- task
- verify
- retry
- evidence
- completion gate

### Phase 4 — Outer Learning Loop
- Lesson Candidate
- effect measurement
- project/global scope
- skill candidate
- promotion

### Phase 5 — Improve / Discover / Prune
- Better Path Check
- Manual Action Gate
- External Solution Scout
- model profile adaptation
- Skill/Rule pruning

## 15. v2 성공 기준

1. 새 세션에서 사용자가 “지금 어디까지 했는지 다시 확인해봐”라고 말하지 않아도 이어갈 수 있다.
2. 이미 확인된 사실을 다시 처음부터 조사하지 않는다.
3. 반복 수동 작업을 AI가 먼저 더 좋은 방식으로 대체한다.
4. 프로젝트를 할수록 다음 프로젝트의 시작점이 좋아진다.
5. 새로운 강한 모델이 나오면 불필요한 규칙/workflow를 덜어내 자율성을 보존한다.
