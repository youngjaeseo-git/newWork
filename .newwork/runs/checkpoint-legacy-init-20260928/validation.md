# Legacy assumption removal checkpoint

Scope C is a neutral init sentence, three regression tests, and one migration-row clarification distinguishing manual history links from init output. There is no new conditional branch, setup command, config, discovery, automatic link, Skill, adapter or lifecycle/completion/acceptance change. Existing legacy documents are untouched.

This new actual regression ran before the core sentence change: 2 FAIL and overwrite protection PASS (exit 1). After the change all 3 passed (exit 0). These are current regression artifacts, not fabricated historical evidence. Full ./run.sh test then passed Loop and Memory38 in 41.024 seconds. Python/Bash syntax and git diff --check passed.

Independent review initially flagged the migration wording. The approved pilot source of truth requires neutral init even when legacy exists; the one-row clarification preserves manual migration links without automatic init links. Independent Spec/Contract and scoped verifier then passed after inspecting the applied diff and before/after logs. Full-suite execution is the main agent's result, not an independently rerun verifier suite.

No new model E2E or task-close event is asserted for C. This is an independently regression-tested Git checkpoint. Core/tests match the preserved primary A+C source hashes. The original session/task completion remains in the primary ledger; side-branch ledger entries are only legitimate Git acceptance records. Lesson hashes/effect/approval remain unchanged.
