# newWork와 mattpocock/skills 구조 비교

작성일: 2026-09-28. 2026-09-27에 수행한 벤치마크 분석을 공유용 문서로 정리했다.

## 분석 범위와 결론

로컬 newWork의 `run.sh`, Loop/Memory 코드, 테스트, `CLAUDE.md`, v2 설계·세션·Project Lesson 계약과 Matt 저장소의 실제 `SKILL.md` 및 참조 문서를 대조했다. 분석 당시 newWork 기준점은 `1d58f3d337dbbb522e1d0c11d50d94ac0e117015`, branch는 `claude/loving-newton-BjOEj`였다. 기존 미커밋 Memory 코드·테스트 변경도 존재했으므로 분석은 당시 working tree 기준이며, 해당 구현을 승인하거나 checkpoint한 것은 아니다. 외부 저장소는 당시 main을 읽었으며 고정 SHA를 확보하지 않았으므로 링크 대상은 이후 바뀔 수 있다.

결론은 **Matt의 skill 묶음을 이식하기보다, 기존 절차를 더 선명하게 만드는 원칙만 수동으로 시험하는 것**이다. 정적 분석이며 테스트 실행·skill 설치·구현 변경을 하지 않았다.

## 1. mattpocock/skills가 호응을 얻는 핵심 이유

README는 요구 이해 차이, 코드 피드백 부족, 설계 복잡성을 작은 조합형 skill로 다루겠다고 설명한다. 사용자 호출 절차와 모델이 필요할 때 호출할 수 있는 공통 작업 원칙을 나누는 구조는 사용자 통제와 재사용을 함께 추구한다. 이것은 설계에 대한 해석이지 인기의 원인을 실증한 결과는 아니다.

근거: [README](https://github.com/mattpocock/skills/blob/main/README.md), [호출 원칙](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md).

## 2. 같은 철학과 본질적 차이

둘 다 작은 책임, 사용자 판단, 검토 가능한 결과를 중시한다. Matt setup은 기존 저장소와 지침을 탐색하고 초안을 확인받는다. newWork는 기존 작업을 보존하며 Git 수락과 Lesson 승인을 명시적 행위로 둔다.

- Matt: 에이전트가 **어떻게 일할지** 안내하는 절차·작업 원칙의 모음.
- newWork: 실행에 더해 원장·근거 해시·task instance·검증 결과·Git checkpoint를 연결하여 **무엇을 완료로 인정할지** 다룬다.

Matt의 간결함은 배울 수 있지만 skill만으로 newWork의 복구·stale 방지 계약을 대체할 수는 없다.

근거: [Matt setup](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md), [newWork Loop](2026-09-24_loop-agent-poc.md), [세션 계약](newwork-v2-session-contract.md), [Lesson 계약](newwork-v2-project-lesson-contract.md).

## 3. 비교표

| Matt 개념 | newWork 대응 | 차이·분류 | 배울 가치 | 복잡성 위험 |
|---|---|---|---|---|
| 사용자 호출 절차 / 모델 호출 작업 원칙 | 명시적 Memory CLI와 고정 Loop | 이름은 다르지만 유사: 사용자 통제와 자동 실행 경계 | 행위별 승인 주체 명료화 | 호출 관례를 인증·권한으로 오해 |
| setup 탐색→제안→확인 | init-project의 기존 파일 건너뛰기, 수동 분석 | 없는 부분 중 가치 큼: 사전 중복·충돌 진단 | 기존 프로젝트의 불필요한 복사 감소 | setup 명령·설정 문서 증가 |
| grill-with-docs 인터뷰·용어·ADR | brainstorming·plan·DECISIONS·confirmation | 유사하지만 모호한 용어 검증 규율은 약함 | 요구·상태 전이 오해 감소 | CONTEXT·ADR 일괄 도입 시 중복 |
| 얇은 implement→TDD→review | planner→implementer→reviewer→verifier | 실행·검토는 이미 존재, TDD는 고정 역할 아님 | 필요한 작업에서 테스트 우선 | 별도 implement 오케스트레이터는 중복 |
| Standards / Spec review | 단일 reviewer, verifier, contract review | 없는 부분 중 시험 가치: 두 질문 결과 구분 | 요구 불일치와 규약 위반을 섞지 않음 | 병렬 agent·retry 비용 증가 |
| pointer·pruning | CLAUDE.md·계약 문서·Memory | 없는 부분 중 가치 큼: 정보 배치 기준 | 상시 문맥·오래된 설명 감소 | 새 문서 관리 skill은 역효과 |
| issue tracker·triage label | Memory task/event | 현재 필요 없음 | 외부 협업 확대 때 재평가 | 같은 상태의 이중 관리 |

Matt 근거: [setup](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md), [grill-with-docs](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md), [domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md), [implement](https://github.com/mattpocock/skills/blob/main/skills/engineering/implement/SKILL.md), [code-review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md), [writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md).

newWork 근거: [run.sh](../run.sh), [Loop](../scripts/loop-agent-poc.sh), [Memory](../scripts/newwork-memory.py), [Memory tests](../tests/test-newwork-memory.py), [Loop tests](../tests/test-loop-agent-poc.sh), [CLAUDE.md](../CLAUDE.md), [v2 spec](newwork-v2-spec.md), [migration](newwork-v2-migration.md).

## 4. Q1 — user-invoked / model-invoked

Matt의 구분은 호출 관례이지 사람 신원을 증명하는 권한 장치가 아니다. newWork에서는 다음 경계가 적합하다.

| 행동 | 권장 실행 경계 |
|---|---|
| session start | LEVEL 1 명시적 workflow에서 호출, LEVEL 0 직접 호출 유지 |
| task open | 사용자가 정한 범위 안에서 workflow가 호출 |
| finding | 에이전트가 근거와 함께 기록 가능 |
| contract review / verifier | 작업 중 에이전트가 수행 가능. PASS와 사용자 승인은 별개 |
| accept-git | 사람이 diff를 검토한 뒤 명시적 지시로 실행 |
| lesson approve | 사용자 결정에 따른 procedural approval. CLI는 사람을 인증하지 않음 |
| release / merge | 완료 판정 밖의 별도 사용자 결정 |

## 5. Q2 — reviewer를 둘로 나눌 것인가

지금은 상시 분리하지 않는 편이 낫다. Spec와 Standards/Contract를 분리하면 요구 누락과 규약 위반을 구분하고 판단 혼합을 줄일 가능성이 있다. Matt는 병렬 하위 agent로 문맥을 격리하고 결과도 축별로 보존한다.

하지만 newWork는 reviewer와 verifier가 이미 별도 세션이다. 추가 reviewer는 토큰, 지연, 합의·FAIL 처리, retry 경로를 늘린다. 현재 자료만으로 결함 탐지가 더 좋아진다고 입증되지는 않는다.

먼저 동일 reviewer가 두 축을 별도로 보고하는 저비용 실험이 적합하다. 이는 Matt의 완전한 문맥 격리는 아니다. 실제 추가 발견과 비용을 비교한 뒤 분리를 판단한다.

## 6. Q3 — context load와 문서 중복

분석 당시 CLAUDE.md는 345줄이며 킥오프·경쟁 조사·배포·수익 모델·도구 추천까지 포함한다. 다음은 정리 후보이지 삭제 확정이 아니다.

- plan/todo/work/history 갱신 규칙과 event·STATE의 상태 책임 중복.
- CLAUDE.md 13절의 회고 교훈 전파와 Project Lesson의 live freshness 계약 차이.
- run.sh 명령처럼 환경에서 바로 조회 가능한 정보의 문서 복제.
- migration에 남은 과거 시점의 상태 설명이 현재 상태처럼 읽힐 위험.
- 특정 시점·작업에만 필요한 도구·배포 참조를 항상 로드하는 부담.
- 지침의 /start-project 등 호출명과 저장소 내 실제 구현의 구분. 저장소의 skills 디렉터리에서 확인되지 않았다고 전역 설치 부재까지 단정할 수는 없다.

pointer는 자료의 정체와 읽어야 할 조건을 함께 표현해야 한다. 모든 문서를 분할하면 사람의 문서 탐색 부담이 증가하므로, 모든 작업에 필요한 규칙은 남기고 특정 분기에만 필요한 참조를 분리한다. 구체적인 승인·복구 경계는 no-op이 아니다. 행동 변화가 없는 일반 문장인지 여부는 실제 실행 비교로 판정해야 한다.

Matt의 leading word 원칙은 긴 반복 설명을 공유된 짧은 용어로 줄이는 것이다. newWork의 task instance, stale evidence, checkpoint transition처럼 정의된 용어를 일관되게 쓰는 데 적용할 수 있지만, 모호한 새 용어를 만들어 설명 비용을 늘려서는 안 된다.

## 7. Q4 — 기존 프로젝트의 최소 setup

show_weather 같은 기존 프로젝트에서는 새 command 없이 먼저 다음을 수동 점검한다.

1. branch·dirty 상태·지침·계획 문서·테스트 진입점·기존 상태 기록 목록화.
2. 기존 구성요소를 유지 / 연결 / 향후 통합 검토로 분류.
3. 적용 범위와 쓰기·기기 설치·checkpoint 승인 경계 확인.
4. 실제 task 하나에 필요한 session·task·evidence·completion gate만 연결.
5. 2~3개 프로젝트에서 반복되는 부분이 확인된 후 자동화 판단.

Matt의 기존 지침 탐색과 작성 전 초안 확인은 배울 가치가 있다. 하지만 issue tracker·triage·domain 문서를 함께 설정하는 scaffold 전체는 첫 적용에 과하다.

## 8. Q5 — Loop 역할과 독립 discipline

Loop 역할은 **누가 언제 실행·검토하는가**, discipline은 **그 안에서 어떤 방법을 쓰는가**를 정한다.

| 방법 | 현재 역할과 연결 | 독립 방법으로 둘 때 | 새 role로 만들 때 위험 |
|---|---|---|---|
| TDD | implementer의 red→green→refactor | 필요한 seam에서만 적용 | 각 테스트 전환마다 역할 교환 |
| debugging | planner/implementer의 재현·가설·최소 수정 | bug task에 선택 적용 | 기존 retry와 별도 진단 engine 중복 |
| research | planner 또는 필요한 작업자의 조사 | 질문에 맞게 primary source 확인 | 모든 task에 조사 단계 강제 |
| domain modeling | 설계 대화와 contract review | 모호한 용어·경계가 나타날 때 사용 | glossary·ADR 의무 생성 |
| code review | 기존 reviewer와 가장 많이 겹침 | 두 축 질문을 reviewer에 적용 | 중복 orchestration·판정·retry |

독립 방법은 선택적 적용이 쉽지만 누락될 수 있다. task별 완료 기준에 필요한 방법만 명시하는 것이 균형점이다.

## 9. 실험할 가치가 큰 세 가지

### 1. 기존 프로젝트 수동 setup 점검

- 아이디어: 적용 전 구조·충돌·승인 범위를 확인한다.
- Matt 역할: setup-matt-pocock-skills.
- newWork 대응물: init-project.sh와 수동 저장소 분석.
- 중요한 차이: 기존 프로젝트에 불필요한 추적 파일을 얹을 수 있다.
- 실험: show_weather 포함 2~3곳을 읽기 전용으로 목록화한다.
- 성공: 반복되는 충돌·선택 질문으로 최소 공통 절차가 분명해진다.
- 실패/중단: 프로젝트별 차이가 커서 공통 절차가 거의 없다.
- 추가 moving parts: 실험 단계 0. 자동화하면 증가한다.
- 지금 구현 여부: 아니오.

### 2. 두 축 contract review

- 아이디어: Spec와 Standards/Contract 결과를 별도로 보고한다.
- Matt 역할: code-review.
- newWork 대응물: reviewer·verifier·수동 contract review.
- 중요한 차이: 테스트 PASS 뒤에도 요구·신뢰 경계 결함이 남을 수 있다.
- 실험: 다음 실제 task 2~3건에서 기존 reviewer가 두 축을 별도로 기록한다.
- 성공: 추가 결함 또는 더 명료한 무결함 판정이 기록되고 비용이 감당 가능하다.
- 실패/중단: 새로운 가치 없이 지연·토큰만 늘거나 retry가 모호해진다.
- 추가 moving parts: 실험 단계 0. 병렬 reviewer 구현 시 증가한다.
- 지금 구현 여부: 아니오.

### 3. 지침·문서 문맥 다이어트

- 아이디어: 상시 지침과 조건부 참조를 구분한다.
- Matt 역할: writing-for-agents.
- newWork 대응물: CLAUDE.md·docs·Memory.
- 중요한 차이: 중복 규칙과 오래된 상태 설명이 판단을 흐릴 수 있다.
- 실험: 수정 없이 문장을 필수·조건부·환경 조회 가능·중복으로 분류한다.
- 성공: 제거·pointer 후보의 근거와 단일 원본이 특정된다.
- 실패/중단: 축소 후보가 실제 필수 행동을 유도하고 있었다.
- 추가 moving parts: 실험 단계 0. 새 문서 체계를 만들면 증가한다.
- 지금 구현 여부: 아니오.

## 10. 지금 가져오지 말아야 할 것

전체 skill 설치, 전체 setup scaffold, issue/triage 이중 상태, CONTEXT·ADR 일괄 생성, 병렬 reviewer 상시화, implement의 자동 commit 규칙이다. Matt implement는 현재 branch에 commit하도록 지시하지만 newWork는 Git 수락·checkpoint에 별도 사용자 판단을 요구한다. 그대로 연결하면 승인 경계를 흐린다.

## 11. 제거·통합 후보

CLAUDE.md 진행 상태 규칙과 Memory projection, 수동 todo/work 상태표, CLAUDE.md 교훈과 LESSONS 재사용 판단, 반복 검토·검증 지시, 환경에서 조회 가능한 명령 목록을 우선 검토한다.

원문 계획·회고·결정의 이유는 event projection으로 대체되지 않으므로 보존한다. resume처럼 고유 상태를 만들지 않는 command를 제거한 원칙은 계속 타당하다. 실제 삭제나 규칙 변경은 이번 벤치마크 범위 밖이다.

## 12. show_weather와 다음 실험

전면 이관보다 기존 절차를 보존하면서 실제 task 한 건의 시간순 증거를 남기는 것이 핵심이다. setup 기능 신설보다 사전 목록화와 선택적 연결을 우선한다.

다음 실험은 **두 축 contract review**를 권장한다. 기존 reviewer·retry는 유지하고 같은 검토 기록에 Spec와 Standards/Contract의 발견·무발견을 나눈다. 사전 테스트→검토→필요한 수정·회귀 테스트의 증거로 실제 추가 발견과 비용을 비교한다. 효과가 없으면 reviewer 분리 구현 없이 종료한다.

이 문서는 제안이며 구현·Lesson 승인·Phase 4B 시작을 의미하지 않는다.
