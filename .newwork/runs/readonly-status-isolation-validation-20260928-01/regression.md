# Test-only optional-result environment isolation

Scope: `tests/test-loop-agent-poc.sh`; production Loop path validation is unchanged. Existing FAIL run is preserved. This artifact records directly observed commands, not model E2E completion.

## Before fix

Copied the existing scripts into `/private/tmp/newwork-autonomous-validation.oK9ZGi/before` and ran its Loop suite with parent task ID `parent-task`, open event `16`, and an injected run path. Exit code 2; exact output:

```text
[loop-poc] result run directory must be workspace/.newwork/runs/<run-id>
```

## Minimal test fix

At test entry, unset only `LOOP_AGENT_POC_TASK_ID`, `LOOP_AGENT_POC_TASK_OPEN_EVENT`, `LOOP_AGENT_POC_RUN_DIR`. Each test supplies its own inputs. Added a negative task-bound production path check asserting exit 2, exact rejection, no created invalid run directory, and no role invocation.

## After fix

- Clean optional environment: full Loop suite PASS, exit 0.
- Parent task ID `parent-task`, open event `16`, and run path `/private/tmp/parent-run`: full Loop suite PASS, exit 0.
- Explicit bound test: its own workspace/run/task inputs produce result and close disposable task; retry-limit result stays absent and task stays open.
- Invalid task-bound path: rejection regression PASS.
- Bash syntax, Python AST syntax and `git diff --check`: PASS.
- Real working-tree `./run.sh test`: Loop PASS; Memory 38 tests PASS, exit 0. This includes three unrelated init tests and is not an isolated status-only result.

No production path rule, real task lifecycle, Lesson decision or accepted Git identity changed by these tests.
