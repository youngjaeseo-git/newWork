# Autonomous continuation observations — 2026-09-28

## Actual execution and runtime preflight

The execution tool approved `require_escalated` for this specific Loop invocation under the existing macOS user. Role sandbox flags stayed read-only/workspace-write as implemented. No global policy, configuration, credential, security validation or source file was changed.

Run 02 targeted the existing status-only disposable fixture plus test isolation, excluding the legacy-init patch. Task ID was `memory-readonly-status-20260927`, open event 16. The planner command reached the model service but failed because configured `gpt-6-sol` was unsupported with the ChatGPT account. There was no readonly DB/app-server initialization EPERM in this escalated attempt. This establishes runtime startup access, not successful model execution.

Separate minimal no-tool/no-write preflights used invocation-only `-m` overrides. `gpt-5.4` and `gpt-5.3-codex` were also rejected as unsupported. The historical successful planner log identified `chatgpt-web/gpt-5.6-sol`. With that exact existing path the CLI reported:

`ChatGPT requested sign-in. Open sign in in the launcher, then retry.`

The CLI retried the sampling request five times and exited 1. No login automation, new credential, endpoint change or authentication bypass was attempted. Run 02 remains FAIL; no verification result exists. The previous production failure and sandbox failure are unchanged.

## Finding A — runtime preflight

A minimal actual-model preflight can distinguish runtime filesystem/app-server restrictions, model availability and login prerequisites from role implementation failures. These failures occurred before any implementer/reviewer/verifier execution. This is an observation and improvement candidate, not an implemented preflight feature or Lesson.

## Finding B — whole-tree acceptance

The real worktree still contains distinct read-only status and legacy-init hunks. Existing accept-git approves the whole worktree, while a recognized checkpoint must match its accepted user-file identity and leave the tree clean. A status-only partial commit with legacy hunks left over cannot satisfy those conditions. No partial/staged acceptance or new checkpoint mode was added.

A separate checkout can preserve and test patch subsets without modifying the original worktree, as this fixture demonstrates. It does not by itself close the original session or satisfy the original checkout's acceptance contract. Moving accepted lifecycle/checkpoint work to another checkout needs an explicit plan; no worktree/branch transfer or commit was performed.

## Remaining boundary

Task and session must remain open because actual-model E2E has not passed. The next prerequisite is a human sign-in through the existing launcher, followed by another fresh run ID and invocation-only selection of the established model path. Session end may additionally require explicit Git review because recorded HEAD differs from current HEAD. No accept-git or Lesson decision was made.
