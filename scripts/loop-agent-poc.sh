#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_BIN="${LOOP_AGENT_POC_CODEX_BIN:-codex}"

usage() {
  cat <<USAGE
Usage:
  ./run.sh loop-poc "<task>" [workspace]

Runs four independent Codex sessions in order:
  planner(read-only) -> implementer(workspace-write) -> reviewer(read-only) -> verifier(read-only)

Environment:
  LOOP_AGENT_POC_CODEX_BIN  Override codex executable (used by tests)
  LOOP_AGENT_POC_RUN_DIR    Preserve role outputs in this directory
USAGE
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

TASK="$1"
WORKSPACE="${2:-$ROOT_DIR}"

if [[ -z "${TASK// }" ]]; then
  echo "[loop-poc] task must not be empty" >&2
  exit 2
fi

if [[ ! -d "$WORKSPACE" ]]; then
  echo "[loop-poc] workspace does not exist: $WORKSPACE" >&2
  exit 2
fi
WORKSPACE="$(cd "$WORKSPACE" && pwd)"

if ! command -v "$CODEX_BIN" >/dev/null 2>&1 && [[ ! -x "$CODEX_BIN" ]]; then
  echo "[loop-poc] codex executable not found: $CODEX_BIN" >&2
  exit 127
fi

if [[ -n "${LOOP_AGENT_POC_RUN_DIR:-}" ]]; then
  RUN_DIR="$LOOP_AGENT_POC_RUN_DIR"
  mkdir -p "$RUN_DIR"
else
  RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/newwork-loop-agent-poc.XXXXXX")"
fi

rm -f \
  "$RUN_DIR/planner.md" "$RUN_DIR/planner.log" \
  "$RUN_DIR/implementer.md" "$RUN_DIR/implementer.log" \
  "$RUN_DIR/reviewer.md" "$RUN_DIR/reviewer.log" \
  "$RUN_DIR/verifier.md" "$RUN_DIR/verifier.log"

last_line_equals() {
  local expected="$1"
  local file="$2"
  [[ "$(tail -n 1 "$file")" == "$expected" ]]
}

run_role() {
  local role="$1"
  local sandbox="$2"
  local prompt="$3"
  local output="$RUN_DIR/$role.md"
  local log="$RUN_DIR/$role.log"

  echo "[loop-poc] $role ($sandbox)"
  if ! "$CODEX_BIN" exec --ephemeral -s "$sandbox" -C "$WORKSPACE" -o "$output" "$prompt" >"$log" 2>&1; then
    echo "[loop-poc] $role failed; log: $log" >&2
    cat "$log" >&2
    exit 1
  fi

  if [[ ! -s "$output" ]]; then
    echo "[loop-poc] $role produced no final output: $output" >&2
    exit 1
  fi
}

planner_prompt=$(cat <<EOF_PLAN
ROLE: planner
TASK:
$TASK

Inspect the workspace and make a minimal implementation plan.
Do not modify any file. Include acceptance checks and material risks.
Your output will be handed to a separate implementer.
EOF_PLAN
)
run_role "planner" "read-only" "$planner_prompt"

PLAN="$(cat "$RUN_DIR/planner.md")"
implementer_prompt=$(cat <<EOF_IMPLEMENT
ROLE: implementer
TASK:
$TASK

PLANNER OUTPUT:
<planner>
$PLAN
</planner>

Implement the task with the smallest reasonable change inside the workspace.
Follow repository rules. Run focused checks if possible.
Do not commit or push.
End with exactly one of these lines:
IMPLEMENTATION: COMPLETE
IMPLEMENTATION: BLOCKED
EOF_IMPLEMENT
)
run_role "implementer" "workspace-write" "$implementer_prompt"

if ! last_line_equals "IMPLEMENTATION: COMPLETE" "$RUN_DIR/implementer.md"; then
  echo "[loop-poc] implementer did not report completion; stopping before review" >&2
  exit 1
fi

reviewer_prompt=$(cat <<EOF_REVIEW
ROLE: reviewer
TASK:
$TASK

PLANNER OUTPUT:
<planner>
$PLAN
</planner>

Review the current workspace and diff independently.
Do not modify files. Check correctness, scope, regressions, and whether the plan was followed.
The final line must be exactly:
VERDICT: PASS
or:
VERDICT: FAIL
EOF_REVIEW
)
run_role "reviewer" "read-only" "$reviewer_prompt"

if ! last_line_equals "VERDICT: PASS" "$RUN_DIR/reviewer.md"; then
  echo "[loop-poc] reviewer rejected the implementation; stopping before verification" >&2
  exit 1
fi

verifier_prompt=$(cat <<EOF_VERIFY
ROLE: verifier
TASK:
$TASK

PLANNER OUTPUT:
<planner>
$PLAN
</planner>

Independently verify the actual resulting behavior in the workspace.
Run the smallest relevant acceptance checks/tests that are possible without modifying source files.
Do not trust the implementer claims. Report concrete evidence.
The final line must be exactly:
VERDICT: PASS
or:
VERDICT: FAIL
EOF_VERIFY
)
run_role "verifier" "read-only" "$verifier_prompt"

if ! last_line_equals "VERDICT: PASS" "$RUN_DIR/verifier.md"; then
  echo "[loop-poc] verifier rejected the result" >&2
  exit 1
fi

echo "[loop-poc] PASS"
echo "[loop-poc] artifacts: $RUN_DIR"
