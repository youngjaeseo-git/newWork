# Product Decision Handoff — Candidate

> Status: candidate design principle, not yet a formal newWork contract or approved lesson.
>
> Recorded: 2026-09-28

## Why this exists

The current workflow has a useful separation:

- Human + ChatGPT is strong at product thinking, UX, direction, trade-offs, and iterative planning.
- Codex is strong at implementation and execution, but when asked directly it can move too quickly into coding before product intent is sufficiently explored.
- newWork should improve implementation quality and continuity without replacing the high-value product-planning loop.

A full handoff after every small change would add too much friction. The goal is therefore not to route every iteration back through Human + ChatGPT, but to define a clear boundary between **product decisions** and **implementation decisions**.

## Proposed boundary

### Human + ChatGPT owns

- What should be built
- Product intent
- UX / game feel / interaction direction
- Option comparison
- Important trade-offs
- Requirement changes
- Decisions that materially affect the user experience

### Web Sol + newWork + Codex owns

- Repository investigation
- Technical planning
- Implementation
- Tests
- Reviewer feedback
- Retry loops
- Verification
- Refactoring needed to satisfy the agreed requirement
- Routine fixes discovered during implementation

## Escalation rule

Do **not** return to Human + ChatGPT for ordinary implementation problems.

Examples that should stay inside the development loop:

- test failures
- null / state bugs
- build errors
- implementation-detail refactors
- reviewer feedback
- verifier failures
- animation or timing fixes that do not change the intended product behavior

Return to Human + ChatGPT only when implementation exposes a new **product-level decision**.

Example:

> A collision case forces a choice between automatic avoidance and preserving direct player input.

That choice changes the intended experience, so it should be escalated as a product decision instead of being silently decided by the implementation agent.

## Handoff model

The full planning conversation should not be copied into the implementation loop.

Instead, hand off only the **decision delta** plus acceptance criteria.

Example:

```text
Decision update

- Keep F2 as the control direction.
- Do not add automatic avoidance.
- Prioritize player input.
- Strengthen collision feedback.
- Preserve the existing speed curve.

Acceptance criteria

- Existing F2 control feel is preserved.
- Input recovers immediately after collision.
- No regression in existing tests.
```

This keeps product intent explicit while avoiding unnecessary context growth.

## Two-loop model

```text
[Product loop]

Human <-> ChatGPT
  |
  | confirmed decision / changed intent
  v

[Development loop]

Web Sol -> newWork -> Codex
   ^                    |
   |                    v
   +--- review / test / retry
```

Most development iterations remain inside the development loop.

Only a new product decision crosses back to the product loop.

## Possible future newWork support

A future version of newWork may benefit from a small persistent product-decision layer, for example:

```text
.newwork/
  product/
    CURRENT.md
    DECISIONS.md
```

Possible responsibilities:

- `CURRENT.md`: current product intent / active constraints
- `DECISIONS.md`: accepted decision deltas and their rationale
- planners/reviewers/verifiers read these decisions before acting
- implementation agents must not silently override accepted product decisions
- unresolved product decisions can become explicit escalation points

This is only a candidate direction.

Do not implement this structure or treat it as a contract until it has been tested on real projects.

## Validation plan

Validate this model incrementally rather than migrating every active project at once.

Suggested approach:

1. Keep current working projects on their existing workflow.
2. Select one independent feature in an active project.
3. Plan the product/UX direction with Human + ChatGPT.
4. Hand off only the confirmed decision delta and acceptance criteria.
5. Let Web Sol + newWork + Codex run the implementation/review/verification loop.
6. Measure:
   - human intervention count
   - repeated explanations
   - rework count
   - regressions
   - failed tests / retries
   - total elapsed time
   - final quality
7. Promote this candidate into a formal newWork contract or lesson only if real usage shows clear benefit.

## Working principle

A useful default boundary is:

> **What should we build, and what should it feel like?**  
> Human + ChatGPT decides.

> **How should the agreed requirement be implemented safely and verified?**  
> newWork + Web Sol + Codex decides.

This boundary is intentionally provisional and should evolve from production evidence.
