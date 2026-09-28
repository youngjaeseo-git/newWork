# show_weather pilot 회수와 newWork 다음 개선 후보

작성일: 2026-09-28. 사용자 요청에 따라 직전 채팅 분석을 공유용으로 보존한다. 새 구현이나 Lesson 승인을 의미하지 않는다.

## 결론

다음 개선은 **memory init이 존재하지 않는 legacy 문서 경로를 생성하지 않도록 초기 문구를 단순화하는 것** 하나를 권장한다. 실사용에서 확인됐고 작은 수정과 결정적 테스트로 검증할 수 있으며 새 subsystem이 필요 없다.

## 실제 저장소 확인

- show_weather 현재 branch: release/v0.9.
- release HEAD: `c1785f4ea6b7ba0af1d0a939d78e1fe4f70b6870`.
- release commit에는 제품 코드 3개와 테스트 2개만 포함된다.
- 실험 기록은 experiment/newwork-widget-freshness의 `06e64aec1e4c27bb3656b62680961e146242692c` commit에 보존되어 있다.
- 두 branch의 android/lib/test 내용은 동일하다.
- 현재 release 작업 폴더에는 run 기록이 없다. branch 전환 없이 experiment commit에서 읽었다.
- newWork 분석 당시 HEAD는 c71dc02이며 기존 미커밋 Memory 코드·테스트·projection 변경이 있었다. 그 변경은 수정·승인하지 않았다.

근거는 show_weather experiment commit의 `.newwork/runs/widget-freshness-20260927-01/` 아래 파일과 `.newwork/events.jsonl`, FINDINGS/STATE, release commit diff다. 이번 분석에서 테스트·기기 관찰을 새로 수행하지 않았다.

## newWork 강점

- 자동 테스트 PASS와 launcher 실기기 표시 확인을 섞지 않았다.
- 기기 검증 pending 동안 task를 열어 두고 최종 확인 후 event 12에서 닫았다.
- event 6·9의 다음 시작점과 열린 task로 기기 연결·최종 화면 확인을 이어갈 수 있었다.
- 첫 review의 결함 미확인 기록을 이후 발견 때문에 고쳐 쓰지 않았다.
- show_weather의 build/run script·지침·기존 테스트 구조를 교체하지 않았다.

completion gate는 task instance·artifact·해시·verdict 일관성을 확인하는 데 의미가 있었다. 그러나 실기기 검증이 필수라는 판단은 workflow가 제공했다. gate 자체가 관측의 진실성이나 검증 범위의 충분성을 자동 판단한 것은 아니다.

## 실제 불편·문제와 제거 후보

| 확인된 사항 | 판단 |
|---|---|
| DECISIONS.md가 없는 docs/decision-log.md 참조 | 실제 초기화 결함. 불필요한 가정 제거 대상 |
| 여러 artifact 작성과 result 해시 수동 조립 | 실제 추가 작업 부담. 소요 시간이나 절감 수치는 측정되지 않음 |
| 테스트 결과·검증 범위를 여러 문서에서 반복 | 일부 중복. 다음 실행에서 요약 축소 후보 |
| lock·Git-object 접근의 host 권한 처리 | 실행 환경 마찰. sandbox 완화·우회 기능 대상 아님 |
| 기기 연결·설치 허용·홈화면 확인 | 필요한 사용자 개입. newWork가 제거한 비용 아님 |

별도 계획·테스트 시스템을 복제하지 않았고 원장/projection은 목적 있는 구조다. 제품 release에서 metadata를 제외했으므로 현재 release commit을 하네스가 오염시키지 않았다.

과거 기록의 미커밋·최종 확인 대기는 작성 당시 사실이다. 현재 상태와 구분해 읽되 소급 수정하지 않는다.

## contract-review Lesson과 관계

분류: **supporting — 제한적인 지지**.

| 단계 | 실제 근거와 판단 |
|---|---|
| pre-review PASS | pre-review-test.txt, 2026-09-27 05:12:09 UTC |
| 이후 별도 review | contract-review.md, 05:13:01 UTC |
| review에서 새 문제 발견 | 실기기 검증 공백 확인, event 4. 제품 결함은 미확인 |
| 그 문제 때문에 코드 변경 | 직접 증명되지 않음. 직후 코드·회귀 테스트 변경 없음 |
| 이후 제품 결함 발견 | device-validation.md: small/medium stale 경고 말줄임 |
| 회귀 테스트·수정 | post-review-device-test.md: 기대값 변경 후 기존 구현 FAIL, 이후 최소 수정 |
| 수정 후 PASS | Dart 36·전체 468·Gradle 3·native 12 PASS 기록 |
| 최종 기기 확인·완료 | final-device-check.md, 이후 event 12 task close |

테스트 PASS만으로 완료를 판단하지 않는다는 부분은 지지한다. review가 구체적 말줄임 결함을 발견했다거나 review만이 수정의 원인이었다고 말할 수는 없다.

`contract-review-before-checkpoint-v1`의 현재 projection은 candidate/inconclusive다. 수정하거나 승인하지 않았다.

## Matt benchmark와 실제 연결

이전 [벤치마크 문서](newwork-vs-mattpocock-skills-benchmark.md)를 기준으로 대조했다.

| 아이디어 | 분류 | 근거 |
|---|---|---|
| user-invoked / model-invoked | B 가능성 | 설치 허용 등 경계는 작동. 호출 구분 실패는 관측되지 않음 |
| explore-before-setup | A 실제 문제 | 없는 legacy 경로를 초기 문서에 넣음 |
| Spec / Standards·Contract 분리 | B 가능성 | 별도 review 가치는 보였으나 두 reviewer 추가 효과는 시험하지 않음 |
| small composable disciplines | B 가능성 | 기존 테스트·수동 검증 재사용. skill 분리 효과 미측정 |
| context pointer / progressive disclosure | A 제한적 실제 문제 | 잘못된 pointer 확인. 상시 context 과부하까지 증명한 것은 아님 |
| single source of truth / pruning | A 제한적 실제 문제 | 잘못된 참조와 검증 요약 반복. 원장/projection 중복 오류는 없음 |

## 개선 후보 1 — 초기화 문서의 잘못된 가정 제거

- 문제: 없는 legacy 문서가 있는 것처럼 안내한다.
- 실제 evidence: experiment DECISIONS.md, integration-friction finding, retrospective.
- 현재 동작: Memory init이 경로를 무조건 기록한다.
- 제안 변경: 참조 문장을 제거하고 중립적 초기 문구만 유지한다.
- 추가 moving parts: 없음. 조건 분기나 setup command도 불필요하다.
- 제거할 moving parts: legacy 경로에 대한 암묵적 의존.
- 예상 이득: 잘못된 안내와 불필요한 문서 생성 유도 방지.
- 위험: 실제 legacy 이력이 있는 프로젝트의 안내가 줄어든다. 기존 문서 자체는 보존한다.
- 실험: legacy 문서 유무와 관계없이 허위 참조를 생성하지 않고 기존 파일 덮어쓰기 거부가 유지되는지 테스트한다.

## 개선 후보 2 — evidence 서술 중복 축소

- 문제: 검증 범위·결과를 여러 문서에 반복 작성한다.
- 실제 evidence: retrospective 비용 보고와 run 문서 내용.
- 현재 동작: gate는 일반 evidence 파일명·개수를 일률적으로 강제하지 않는다. 필수 result/verifier 계약은 별도로 유지된다.
- 제안 변경: 다음 pilot에서 원본 결과와 하나의 검증 요약을 재사용하는 작성 절차 실험.
- 추가 moving parts: 없음.
- 제거할 moving parts: 중복 요약 작성 단계.
- 예상 이득: 작성·갱신 부담 감소.
- 위험: pre-review와 post-fix 시간순을 잃을 수 있다.
- 실험: 시간순·발견 주체·검증 한계를 동일하게 재구성할 수 있는지 비교한다. 이번 기록은 수정하지 않는다.

## 개선 후보 3 — closeout 근거 위치 명시

- 문제: release 전환 후 기존 파일 경로만으로 실험 근거를 찾을 수 없다.
- 실제 evidence: 현재 run 경로는 없지만 experiment commit에는 보존된다.
- 현재 동작: branch에 속한 파일이며 별도 위치 안내가 없다.
- 제안 변경: 향후 closeout 보고에 보존 commit·branch·run 경로를 함께 표시한다.
- 추가 moving parts: 없음. Git 조회를 재사용한다.
- 제거할 moving parts: 근거 위치 재탐색 단계.
- 예상 이득: release와 실험 기록 분리 후 회수 가능.
- 위험: branch는 이동 가능하므로 commit SHA를 포함해야 한다.
- 실험: release checkout에서 복사·branch 전환 없이 기록을 찾아 읽는다.

## 다음에 구현할 하나

**후보 1: memory init의 허위 legacy 참조 제거.**

실제 finding과 현재 코드가 직접 연결되고, 문장 제거 중심의 작은 변경이며 복구·완료 gate·원장 계약을 건드릴 필요가 없다. 앞서 추천한 reviewer 두 축 실험보다 실제 결함 증거가 명확한 수정을 우선한다.

## 구현하지 말아야 할 것

새 setup command, reviewer 분리, evidence DB·daemon·adapter, sandbox 우회, 자동 Lesson 승격·cross-project import·Phase 4B는 시작하지 않는다.

원래 분석에서는 코드·문서·candidate 수정, commit·push·branch 전환을 하지 않았다. 이번 공유 문서 게시는 별도 사용자 요청에 따른 문서 보존이며 위 후보 구현을 승인하거나 실행한 것이 아니다.
