확인 결과, 수정 방향은 작게 잡을 수 있습니다. 파일은 수정하지 않았습니다.

현재 실패는 재현됐습니다:

```
./run.sh memory status
→ {"message":"[Errno 1] Operation not permitted: '.../.newwork/.lock'","status":"io_error"}
```

원인은 scripts/newwork-memory.py (line 168)의 locked()가 모든 명령에 대해 .lock을 a+b로 열고 LOCK\_EX를 획득하기 때문입니다. status도 execute() (line 420) 진입 즉시 이 경로를 타므로, 실제 데이터는 전혀 수정하지 않아도 read-only sandbox에서 실패합니다.

다만 lock 자체를 제거하면 안 됩니다. mutation 명령은 events.jsonl append 후 projection 파일을 갱신하므로, lock 없이 status가 동시에 읽으면 새 ledger와 이전 STATE/FINDINGS/LESSONS를 섞어 읽어 가짜 snapshot\_mismatches를 보고할 수 있습니다. 따라서 writer와의 동기화는 유지해야 합니다.

최소 구현 계획은 다음입니다.

1. locked()에 shared/read-only 모드를 추가합니다.
   
   - 기존 mutation 경로: .lock을 a+b로 열고 LOCK\_EX 유지.
   - status만: 기존 .lock을 rb로 열고 LOCK\_SH.
   - read-only 경로에서는 .newwork나 .lock을 만들지 않습니다.
   - 초기화되지 않은 저장소라면 기존 계약에 맞게 invalid\_input으로 처리하고, status 실행 자체가 파일을 생성하지 않게 합니다.
2. execute() (line 423)에서 오직 status만 shared lock을 선택합니다.
   
   - reconcile, lesson-check, rebuild, accept-git, session/finding/task/lesson mutation은 이번 변경 범위에서 건드리지 않습니다.
   - replay/idempotency, checkpoint/reconcile 판단, projection 생성 코드도 변경하지 않습니다.
3. tests/test-newwork-memory.py (line 449)에 집중 회귀 테스트를 추가합니다.
   
   - 초기화 후 .lock을 쓰기 불가능하게 만들어도 status가 성공하고 ledger/projection 내용이 변하지 않는지 확인.
   - exclusive writer lock이 잡힌 동안 status가 기다렸다가 lock 해제 후 정상 완료되는지 확인하여 synchronization을 제거하지 않았음을 증명.
   - 반대로 shared lock이 잡힌 동안 start 같은 mutation이 진행되지 않고, 해제 후 정상적으로 event를 기록하는지 확인해 writer가 계속 LOCK\_EX임을 검증.
   - 기존 corrupt-ledger/status 계약 테스트는 그대로 통과해야 합니다.

Acceptance checks:

```
./run.sh memory status          # 실제 read-only sandbox에서 성공
python3 tests/test-newwork-memory.py
tests/test-loop-agent-poc.sh
# 또는 전체 통합 확인
./run.sh test
```

추가로 replay/idempotency, reconcile, checkpoint 관련 기존 테스트가 전부 그대로 통과해야 하며, mutation 후 events.jsonl과 projections의 일관성도 유지되어야 합니다.

주요 위험은 두 가지입니다. shared lock을 생략하면 concurrent writer 중간 상태를 관찰할 수 있고, 반대로 read-only status에서 .lock 생성이나 write-open을 조금이라도 남기면 현재 sandbox 실패가 재발합니다. 또한 이 lock은 Memory 명령끼리만 조정하므로 외부에서 직접 Git/worktree를 바꾸는 것까지 원자적으로 막는 장치는 아닙니다. 이는 기존 계약 그대로입니다.

현재 작업트리는 .newwork/\*에 기존 변경사항이 있지만, 이번 대상인 scripts/newwork-memory.py와 테스트 파일들의 diff는 비어 있습니다. 구현자는 그 기존 .newwork 변경을 건드리지 않는 것이 안전합니다.