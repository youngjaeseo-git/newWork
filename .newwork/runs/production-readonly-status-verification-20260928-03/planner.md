Existing patch is present; no source changes are needed.

Implementation/verification plan:

1. Verify scripts/newwork-memory.py only:
   
   - status requires an existing .newwork/.lock, opens it rb, and takes LOCK\_SH.
   - mutation path remains a+b + LOCK\_EX.
   - confirm status performs no persistent writes and uninitialized status creates no .newwork.
2. Run the four focused lock tests in tests/test-newwork-memory.py:
   
   - test\_status\_uses\_read\_only\_shared\_lock\_without\_writing\_memory
   - test\_uninitialized\_status\_does\_not\_create\_memory\_files
   - test\_status\_waits\_for\_exclusive\_writer\_lock
   - test\_mutation\_waits\_for\_shared\_status\_lock
3. Verify test isolation in tests/test-loop-agent-poc.sh:
   
   - inherited LOOP\_AGENT\_POC\_TASK\_ID, LOOP\_AGENT\_POC\_TASK\_OPEN\_EVENT, and LOOP\_AGENT\_POC\_RUN\_DIR are unset at suite start.
   - explicit task-bound cases later set all required values and still exercise valid/invalid result paths.
4. Implementer should not reimplement anything. Run:  
   env LOOP\_AGENT\_POC\_TASK\_ID=parent-task LOOP\_AGENT\_POC\_TASK\_OPEN\_EVENT=999 LOOP\_AGENT\_POC\_RUN\_DIR=/tmp/parent-run ./run.sh test  
   in a write-capable temporary-file environment, then confirm git diff is empty.
5. Reviewer independently inspect the lock/write contracts and tests. Verifier independently rerun the focused acceptance tests plus full ./run.sh test. Fake-Codex suite success must not be reported as real-model E2E.

Observed here:

- git diff for the scoped files is empty.
- Only three pre-existing untracked .newwork/runs/production-readonly-status-verification-\* directories are present.
- Full test execution could not start because this planner sandbox forbids temporary-directory creation: mktemp ... Operation not permitted, both with the default macOS temp directory and TMPDIR=/tmp. Repository state remained unchanged.

Material risks: do not accidentally include the separate legacy-init change, do not treat the existing untracked run artifacts as new evidence, and distinguish sandbox inability to create temp files from a test/code failure.