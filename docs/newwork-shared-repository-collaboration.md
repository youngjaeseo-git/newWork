# Shared Repository Collaboration Contract

> 둘 이상의 사람 또는 사람·AI가 같은 원격 저장소에서 독립 작업할 때만 적용한다. 개인 작업에는 추가 절차를 강제하지 않는다. Task Intake·autonomous human gate·Git 승인·[session/completion 계약](newwork-v2-session-contract.md)·기존 PR 규칙을 대체하지 않는다.

## 작업 시작과 분업

- 착수·장기 branch 재개 시 `git fetch`로 원격 최신 상태, local/remote divergence, 최근 통합 변경과 현재 task의 충돌 가능성을 확인한다. 네트워크가 안 되면 최신이라고 주장하지 않고 제약을 알린다. 개인 저장소에는 이 확인을 강제하지 않는다.
- 기존 Issue·PR·plan·task 기록에서 작업 목표, 담당자, acceptance criteria, 의존 작업과 겹치는 범위를 확인한다. 병렬 작업 전 task 담당자와 canonical Memory의 통합 기록 담당자를 그중 기존 위치에 명시하고, 담당 변경 시 인계한다. 소유권은 task 단위 조정이며 영구적인 파일 소유권이나 새 관리 시스템이 아니다.
- 독립 작업은 기존 naming convention에 따른 task branch에서 진행하고 공유 integration/main branch에 동시 직접 쓰지 않는다. 기본 통합 경로는 PR이며, 다른 사람 branch의 reset·force push·history rewrite·덮어쓰기는 하지 않는다. commit·remote push·release merge 권한은 기존 7번과 autonomous human gate를 따른다.

## 결정과 handoff

- 여러 작업자에게 영향을 주는 제품·UX·architecture·interface 결정은 개인 채팅만이 아니라 기존 DECISIONS/spec/프로젝트 문서의 적절한 한 정본에 확정하고, 변경 시 decision delta를 관련 작업자에게 전달한다. 이미 확정된 내용은 다시 묻지 않는다. [Product Decision Handoff](2026-09-28_product-decision-handoff.md)는 아직 후보 원칙이며 별도 product DB를 도입하지 않는다.
- 인수인계는 전체 채팅 대신 **Goal, 확정 결정, 담당 task, acceptance criteria, branch/HEAD, 실행·테스트 방법, 알려진 blocker, 제외 범위, 다음 시작점**만 기존 PR·계획·작업 문서에 남긴다. 이미 있는 위치를 가리키고 매번 새 문서를 만들지 않는다.

## Canonical Memory와 통합

- 현재 Memory는 하나의 선형 `events.jsonl`, 하나의 active session, 그 원장에서 재생성되는 STATE/FINDINGS/LESSONS와 Git tree identity 검토를 전제로 한다. 로컬 `.lock`은 원격 branch 사이의 분산 잠금이 아니다. **여러 branch가 canonical 원장을 독립적으로 늘린 뒤 자동 병합하는 방식은 지원하지 않는다.**
- 병렬 worker는 각 branch에서 코드·테스트·고유 run ID의 근거를 만들 수 있다. 그 결과는 PR 입력이지 canonical task 완료가 아니다. canonical Memory 기록은 통합 지점의 단일 작성자가 담당한다. branch가 원장/projection을 수정했다면 기계적 병합·한쪽 삭제로 처리하지 말고 사건과 근거를 보존한 채 별도 검토한다.
- 통합 담당자는 각 PR의 범위·acceptance criteria·의존관계·테스트·근거와 공통 결정의 충돌을 확인한다. 두 branch가 각각 PASS여도 합쳐진 tree의 PASS는 아니다. 마지막 통합 변경 후 필요한 regression, 독립 review/verifier를 수행한다. 검증 뒤 통합 tree가 다시 바뀌면 이전 PASS를 그대로 소비하지 말고 현재 tree에서 새 run으로 재검증한다. 현재 canonical task/open event에 결속된 결과만 기존 completion gate로 닫고, 과거 branch의 result를 그대로 재사용하지 않는다.
- merge로 HEAD가 이동하면 기존 [Git checkpoint 계약](newwork-v2-session-contract.md)의 단일 직접 자식 자동 transition으로 간주하지 않는다. 실제 통합 tree를 검토하고 필요한 명시적 `accept-git`을 사용한다. 이는 Git 상태 수락이지 근거 의미의 자동 승인이 아니다.
- 구현 주체가 사람인지 AI인지는 완료 기준이 아니다. 변경 위험에 맞는 테스트·review·verifier·근거를 동일하게 요구한다. 다만 실제 사용자 체감이나 제품 결정은 기존 human gate에 남는다.

## 충돌과 적용 점검

- 단순 Git 충돌은 양쪽 의도가 명확할 때만 안전하게 해결한다. 제품 동작·공유 architecture·interface 결정이 다르면 Git 편집으로 임의 선택하지 않고 기존 정본을 확인한 뒤 미결정이면 human gate로 올린다. 일반 테스트 실패·review feedback은 승인 범위에서 자율 처리한다.
- 독립 기능 두 개: 각 branch·PR의 검증 뒤 통합 검증. 같은 화면 동시 수정: 착수 시 task 경계·의존성 확인. 상충하는 버튼 동작: 공통 결정 없으면 human gate. 사람 구현/AI 검토: 같은 근거 기준. 오래된 branch: 재개 시 fetch와 divergence 확인. 병렬 원장 수정: 자동 병합을 정상 workflow로 취급하지 않음.

이 문서는 협업 절차의 경계다. multi-writer ledger, 분산 event 병합, 협업 서버·task DB·lock service·Controller engine을 제공한다는 뜻이 아니다.
