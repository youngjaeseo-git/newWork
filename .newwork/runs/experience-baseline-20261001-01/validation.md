# Experience Baseline Gate — 문서 계약 검증

- task: `experience-baseline-gate` (open event 41)
- 변경 대상: `CLAUDE.md`, `.claude/skills/start-project/CLAUDE.md`만. 두 파일의 SHA-256은 모두 `179811fbed07468f79c6fb2a930c5b3c2f3d73ba1125af3706f38978099c5390`이며 `cmp`로 byte-identical 확인.
- 자동 검사: `git diff --check` PASS, Python source compile PASS(파일 생성 없음), Bash syntax PASS, `./run.sh test`의 Loop suite PASS 및 Memory 38 tests PASS. 마지막 문구 수정 이후 전체 테스트 재실행.
- 별도 Spec/Usability/Scope/Consistency/Corporate/Human Gate review: PASS. 회사 포맷이 없을 때마다 묻는 것으로 읽힐 수 있는 비차단 문구를, 적용할 기준이 없고 선택이 결과를 바꿀 때만 확인하도록 축소했다.
- 최종 독립 verifier: 조건부 적용, 기존 정본 재사용, 대표 경험 우선, 회사 포맷·보안 경계, A~F 시나리오의 문서 의미 및 배포용 copy 동기화 PASS.
- 한계: 이 검증은 문서 계약과 기존 코드 테스트에 관한 것이다. 실제 앱·게임·PPT의 시각/청각/조작 체감이나 향후 에이전트 준수는 검증하지 않았다. 기존 stale Lesson 근거는 변경하거나 승인하지 않았다.
