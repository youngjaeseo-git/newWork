# show_weather — 첫 newWork 실사용 실험 최종 검토

작성일: 2026-09-28. 앞서 수행한 읽기 전용 최종 검토를 공유용으로 보존한다. 이 문서의 게시가 show_weather의 checkpoint·merge·release 승인을 의미하지 않는다.

## 결론

실제 제품 결함을 재현했고 최소 수정으로 해결했다. 제품 코드와 회귀 테스트는 release 반영 가치가 있고, newWork 기록은 experiment branch에만 보존하는 것을 권장한다.

별도 contract review가 직접 발견한 것은 **실기기 검증 공백**이다. 구체적인 말줄임 결함은 이후 실기기 관찰에서 발견했다. 두 발견을 혼동하거나 과거 review의 결과를 사후 변경해서는 안 된다.

## 검토 당시 기준점

- 저장소: `/Users/youngjaeseo/work/show_weather`
- branch: `experiment/newwork-widget-freshness`
- experiment HEAD와 `release/v0.9`: 모두 `2e5df1ab7399bf65cb3c172fb25a9983cf47fbe6`
- tracked 변경: 5개, 46줄 추가·16줄 삭제
- untracked: `.newwork/` 아래 17개 파일
- task: event 3에서 열림, event 12에서 완료, event 13에서 세션 종료
- 재조회 memory status: `ok`, `git_drift=false`, active session 없음, snapshot/stale evidence 문제 없음
- 해당 검토의 reconcile 실행: sandbox `.newwork/.lock` EPERM으로 실패, exit 14. 사용자 제공 일반 host의 기존 성공 결과와 구분한다.
- `git diff --check`: PASS

Memory의 `ok`는 기록된 미커밋 상태와 일치한다는 뜻이다. working tree clean이나 checkpoint commit 완료를 의미하지 않는다. 검토에서 테스트나 기기 관찰을 다시 수행하지 않았으며, 기존 artifact의 기록을 대조했다.

## 변경 파일 분류

아래는 show_weather 저장소 기준 상대 경로다. 관련 근거 파일은 아직 해당 저장소의 미커밋 실험 자료이므로, 이 문서에 적힌 경로가 GitHub에서 공개되어 있다는 뜻은 아니다.

| 분류 | 파일 | 발생 이유·필요성 | 권장 위치 |
|---|---|---|---|
| A 제품 코드 | `android/app/src/main/kotlin/com/youngjaeseo/annyeong/WeatherWidgetBinder.kt` | 오래된 정보의 경고를 장소명보다 먼저 배치하여 좁은 위젯의 경고 숨김 방지 | experiment 및 release |
| A 제품 코드 | `android/app/src/main/kotlin/com/youngjaeseo/annyeong/WidgetFreshness.kt` | 오래됨을 시간 앞에 배치하고 metadata 순서 함수 추가. fresh 순서는 유지 | experiment 및 release |
| A 제품 코드 | `lib/services/home_widget_service.dart` | Dart stale 문구와 Kotlin 표시 계약의 일치 | experiment 및 release |
| B regression/test | `test/home_widget_service_test.dart` | 표시 순서와 3시간 직전·정확한 경계 검증 | experiment 및 release |
| B regression/test | `test/native/WidgetFreshnessCheck.java` | native stale-first/fresh 순서와 시간 경계 검증 | experiment 및 release |
| C integration metadata | `.newwork/events.jsonl`, `.newwork/STATE.yaml`, `.newwork/FINDINGS.yaml` | 세션·task·관측·완료 근거 원장과 projection | experiment만 |
| C integration metadata | `.newwork/LESSONS.yaml` | 초기화된 빈 projection. 이 프로젝트에서 Lesson 생성·승인 없음 | experiment만 |
| C integration metadata | `.newwork/DECISIONS.md` | 초기화 placeholder. 존재하지 않는 docs/decision-log.md 참조는 불필요한 일반 문구 | 현재 실험 근거로 보존, release 제외 |
| C integration metadata | `.newwork/.gitignore` | runtime lock을 Git에서 제외 | experiment만 |
| C integration metadata | `.newwork/incidents/.gitkeep`, `.newwork/runs/.gitkeep` | 초기 구조. incidents는 비어 있고 runs marker는 현재 비필수 | 구조 보존 가능, release 제외 |
| D run/evidence/retrospective | 아래 9개 run 파일 | 테스트→검토→기기 발견→수정→최종 검증의 시간순 보존 | experiment만 |
| E 무관한 변경 | 발견되지 않음 | 지침·build/run script·버전·다른 기능 변경 없음 | 해당 없음 |

run 디렉터리: `.newwork/runs/widget-freshness-20260927-01/`

- `pre-review-test.txt`
- `contract-review.md`
- `post-review-test.txt`
- `device-validation.md`
- `post-review-device-test.md`
- `final-device-check.md`
- `verifier.md`
- `verification-result.json`
- `retrospective.md`

무시된 `.newwork/.lock`은 runtime 파일이며 commit 대상이 아니다. 삭제를 권장하지 않는다.

## 실제 발견된 제품 결함

stale 경고가 시간·장소 뒤에 붙어 있어 small/medium 위젯에서 말줄임으로 숨겨졌다. large에서는 보였다.

수정은 stale일 때만 경고를 시간과 장소 앞으로 옮긴 것이다. 3시간 판정, 데이터 갱신 방식, fresh 표시 순서는 바꾸지 않았다. 따라서 확인된 결함 없이 제품 코드를 억지로 변경한 사례가 아니다.

근거: `device-validation.md`, `post-review-device-test.md`, `final-device-check.md`와 현재 다섯 파일의 diff.

## 테스트와 실기기 검증

기록상 결과:

- 기존 구현에 변경된 회귀 기대값 적용: Dart와 native 모두 FAIL.
- 수정 후 관련 Dart 36개 PASS.
- non-golden Flutter 전체 468개 PASS.
- Gradle WidgetSnapshotStoreTest 3개 PASS.
- native JVM 12개 PASS.
- Flutter analyze와 debug APK build PASS.
- 최종 +23 설치본의 small/medium/large 모두 오래됨 표시 확인.

문자열·순서 테스트는 launcher의 실제 말줄임을 자동 검증하지 않는다. 실제 표시 검증은 실기기 관찰이 담당한다. package replacement에 따른 redraw와 현재 표시를 관찰했으며, Android 주기 갱신 시점과 실기기 자정 전환은 미검증이다. 날짜·시간대·3시간 경계는 deterministic 테스트 범위다.

## newWork 평가

| 항목 | 판단 |
|---|---|
| 기존 workflow 방해 | build system·지침·테스트를 교체하지 않았다. lock 권한과 Git-object 접근의 운영 마찰은 있었다. |
| 중복 상태·문서 | 새 plan/todo를 복제하지 않았다. 원장/projection은 의도된 구조지만 generic DECISIONS placeholder는 불필요하다. |
| evidence capture 비용 | 9개 run 문서 약 20KB. 용량보다 반복 서술과 수동 해시 조립이 부담이다. 첫 실증에는 유용하지만 매 task의 기본 비용으로 삼기에는 무겁다. |
| completion gate 의미 | 자동 테스트 PASS만으로 task를 닫지 않고 최종 기기 확인 후 event 12에서 닫았다. |
| gate 한계 | 해시·task binding·verdict 일관성을 검사한다. 필수 실기기 검증을 정하는 판단과 관측의 진실성까지 자동 보장하지 않는다. |

`post-review-device-test.md`의 최종 재확인 대기 문장은 이후 `final-device-check.md`로 해결된 당시 상태 기록이다. 현재 상태처럼 읽지 않되, 역사 근거를 수정·삭제하지 않는다.

## Lesson candidate와 관계

대상: `contract-review-before-checkpoint-v1`

제안: **supporting — 제한적인 지지 근거**.

기록된 순서는 테스트 PASS → 별도 review에서 검증 공백 발견 → 실기기에서 제품 결함 발견 → 회귀 테스트 FAIL → 최소 수정 → 테스트·실기기 PASS다.

이는 테스트 PASS만으로 완료를 판단하지 않는다는 주장을 지지한다. 그러나 contract review가 구체적 제품 결함을 직접 발견했다는 증거는 아니다. review가 없었다면 기기 검증도 없었을 것이라는 인과관계도 입증하지 못한다.

supporting evidence로 검토할 가치는 있지만 이 한 건만으로 candidate effect를 supported로 변경하거나 승인하지 않는다. 기존 candidate는 수정하지 않았다.

## Experiment / release / 제거 제안

### Experiment branch에 commit할 것

제품 코드 3개와 테스트 2개, `.newwork` 원장·projection·run 근거·회고를 보존한다. 연결된 근거 원문은 유지한다.

전체 실험을 한 commit으로 묶으면 제품과 실험 기록이 결합되므로 release에는 전체 commit 대신 제품·테스트 다섯 파일의 patch만 별도로 반영하는 편이 안전하다.

event 10의 Git 수락 이후 최종 근거·회고가 추가되었다. 현재 status ok만 보고 미래 commit의 accepted identity까지 승인되었다고 가정하지 않는다. 실제 checkpoint 때 최종 tree를 검토해야 한다.

### release/v0.9에 반영할 것

제품 코드 3개와 테스트 2개만 반영하고 `.newwork`는 제외한다. 반영 뒤 테스트와 release용 빌드 검증은 별도 수행한다. 현재 기기 확인은 debug +23 기준이지 release 배포 승인 자체가 아니다.

### 버릴 것·단순화 후보

- 현재 해시로 연결된 실험 기록에서 즉시 버릴 파일은 없다.
- runtime lock, 임시 screenshot, build 산출물은 commit하지 않는다.
- 향후 초기화에서 잘못된 DECISIONS placeholder와 불필요한 marker 생성을 줄이는 것을 검토한다.
- 다음 실험부터 중복 검증 요약을 줄이되 이번 근거는 삭제하지 않는다.
- 한 번의 실험 비용을 숨기기 위해 새 command·adapter·DB를 만들지 않는다.

## 최종 판정과 남은 단계

첫 실사용 최종 검토 완료. 실제 제품 수정은 보존·release 반영 권장, newWork 실험 기록은 experiment 보존 권장이다. 새 하네스 기능이나 Phase 4B 확장은 필요 없다.

show_weather의 commit·merge·push와 최종 tree 승인은 아직 별도 단계다. 본 공유 문서 게시에서는 show_weather의 파일·Memory·branch를 변경하지 않는다.
