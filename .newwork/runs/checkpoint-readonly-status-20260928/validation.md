# Read-only status checkpoint validation

Scope A: existing lock opened rb + LOCK_SH for status; mutation remains a+b + LOCK_EX; four lock tests added. The separate legacy-init patch is absent at this stage. Production Loop is unchanged, and B isolation is already in the parent commit.

This checkout passed Python/Bash syntax, git diff --check, Loop suite and Memory35 (40.404 seconds). Memory core, Memory tests and Loop test SHA-256 values exactly match the actual-model run-05 fixture. Run 05 executed all four roles and ended PASS; original completion gate closed task at event 20 and session at event 22.

The original run is archived unchanged here. `original-ledger-at-closeout.jsonl` is a byte-copy historical evidence artifact from the primary checkout at event 22, NOT this checkout's live ledger or a replacement projection. No task result is consumed again and no primary events are copied into this checkout's live ledger.

Checkpoint appends only the existing legitimate whole-tree Git acceptance and commits one direct child. The historical Lesson candidate remains inconclusive; changed test source makes its evidence stale and is deliberately not refreshed or approved.
