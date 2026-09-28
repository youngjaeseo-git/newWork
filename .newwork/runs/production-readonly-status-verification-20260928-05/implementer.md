Implementer 실행 완료.

- 지정된 4개 lock 테스트: 4/4 PASS.
- 부모 환경변수 3개 주입 후 ./run.sh test: Loop PoC PASS, Memory 35 tests PASS.
- 계약 확인: status=rb + LOCK\_SH, mutation=a+b + LOCK\_EX; 테스트 진입부에서 옵션 env 3개 unset.
- 관련 4개 파일 SHA-256은 실행 전후 동일.
- tracked/staged diff 없음.
- 테스트가 만든 tests/\_\_pycache\_\_는 정리함.
- 기존 run01–05 untracked 디렉터리는 시작 전부터 존재했고 변경하지 않음.

전체 완료 판정은 outer reviewer/verifier/result gate에 남겨둠.  
IMPLEMENTATION: COMPLETE