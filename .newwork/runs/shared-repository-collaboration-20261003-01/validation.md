# Shared repository collaboration contract validation

- Scope: `CLAUDE.md`, its byte-identical start-project copy, and `docs/newwork-shared-repository-collaboration.md`. No Memory/Loop code, schema, command or project Skill changed.
- Base: `claude/loving-newton-BjOEj` at `1daca4dc577b0859fbb78ab2f9d4a081c589b0a0`; remote tip observed read-only as `1ba82c2eeafcd7f3e98658666558e6bba66c968e` before editing. No fetch, push or branch switch.
- Existing behavior: one canonical linear `events.jsonl`, one active session, projections from ledger, local-only file lock and same-branch/direct-child clean checkpoint rule. The document explicitly does not claim multi-writer or merge support.

## Checks

- `git diff --check`: PASS. New document whitespace checked separately.
- Bash syntax for `run.sh` and `scripts/loop-agent-poc.sh`: PASS.
- Python AST syntax for Memory core and tests: PASS.
- `cmp` of the two CLAUDE files: PASS.
- `./run.sh test`: Loop PoC PASS and Memory 38/38 PASS. Existing tests exercise core behavior, not live multi-user collaboration.
- Independent Spec/Safety/Memory reviewer initially found two documentation gaps: unclear canonical recording owner and reuse of a PASS after integration tree changes. Both were added to the contract; re-review PASS.

## Static scenarios (not a live collaboration trial)

| Scenario | Contract outcome |
| --- | --- |
| A: independent settings and network tasks | Separate task branches/PRs; verify each, then verify integrated tree. |
| B: same HUD screen | Identify task owners and dependency before parallel changes. |
| C: conflicting button behavior | Resolve from shared decision or human gate, not a Git-only merge choice. |
| D: human implementation, AI review | Same risk/evidence criteria; actor identity is not completion proof. |
| E: long-lived teammate branch | Fetch on resume; inspect divergence and recent integration before acting. |
| F: parallel Memory edits | Do not auto-merge independently grown canonical ledgers; preserve and review. |

Limit: these checks validate a written operating contract, not concurrent users, remote PR integration, or cryptographic provenance. The existing stale Lesson candidate was neither changed nor approved.
