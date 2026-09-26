#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_BIN="${LOOP_AGENT_POC_CODEX_BIN:-codex}"
MAX_RETRIES="${LOOP_AGENT_POC_MAX_RETRIES:-2}"

usage() {
  cat <<USAGE
Usage:
  ./run.sh loop-poc "<task>" [workspace]

Runs four roles as independent Codex sessions:
  planner(read-only) -> implementer(workspace-write) -> reviewer(read-only) -> verifier(read-only)
Reviewer FAIL returns to implementer, up to the configured retry limit.

Environment:
  LOOP_AGENT_POC_CODEX_BIN  Override codex executable (used by tests)
  LOOP_AGENT_POC_RUN_DIR    Preserve role outputs in this directory
  LOOP_AGENT_POC_MAX_RETRIES  Maximum reviewer-triggered rework attempts (default: 2)
  LOOP_AGENT_POC_TASK_ID and LOOP_AGENT_POC_TASK_OPEN_EVENT  Together enable an optional
    verification-result.json in LOOP_AGENT_POC_RUN_DIR under workspace/.newwork/runs/<run-id>
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

if [[ ! "$MAX_RETRIES" =~ ^[0-9]+$ ]]; then
  echo "[loop-poc] LOOP_AGENT_POC_MAX_RETRIES must be a non-negative integer" >&2
  exit 2
fi

if ! command -v "$CODEX_BIN" >/dev/null 2>&1 && [[ ! -x "$CODEX_BIN" ]]; then
  echo "[loop-poc] codex executable not found: $CODEX_BIN" >&2
  exit 127
fi

RESULT_TASK_ID="${LOOP_AGENT_POC_TASK_ID:-}"
RESULT_OPEN_EVENT="${LOOP_AGENT_POC_TASK_OPEN_EVENT:-}"
WRITE_RESULT=0
if [[ -n "$RESULT_TASK_ID" || -n "$RESULT_OPEN_EVENT" ]]; then
  if [[ -z "$RESULT_TASK_ID" || ! "$RESULT_OPEN_EVENT" =~ ^[1-9][0-9]*$ || -z "${LOOP_AGENT_POC_RUN_DIR:-}" ]]; then
    echo "[loop-poc] optional result requires task ID, positive open event, and run directory" >&2
    exit 2
  fi
  if [[ ! -d "$(dirname "$LOOP_AGENT_POC_RUN_DIR")" ]]; then
    echo "[loop-poc] result run parent directory does not exist" >&2
    exit 2
  fi
  LOOP_AGENT_POC_RUN_DIR="$(cd "$(dirname "$LOOP_AGENT_POC_RUN_DIR")" && pwd)/$(basename "$LOOP_AGENT_POC_RUN_DIR")"
  RUN_ID="${LOOP_AGENT_POC_RUN_DIR#"$WORKSPACE/.newwork/runs/"}"
  if [[ "$RUN_ID" == "$LOOP_AGENT_POC_RUN_DIR" || ! "$RUN_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "[loop-poc] result run directory must be workspace/.newwork/runs/<run-id>" >&2
    exit 2
  fi
  if [[ -e "$LOOP_AGENT_POC_RUN_DIR" ]]; then
    echo "[loop-poc] result run directory already exists; use a new run ID" >&2
    exit 2
  fi
  WRITE_RESULT=1
fi

if [[ -n "${LOOP_AGENT_POC_RUN_DIR:-}" ]]; then
  RUN_DIR="$LOOP_AGENT_POC_RUN_DIR"
  mkdir -p "$RUN_DIR"
else
  RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/newwork-loop-agent-poc.XXXXXX")"
fi

rm -f \
  "$RUN_DIR/planner.md" "$RUN_DIR/planner.log" \
  "$RUN_DIR"/implementer*.md "$RUN_DIR"/implementer*.log \
  "$RUN_DIR"/reviewer*.md "$RUN_DIR"/reviewer*.log \
  "$RUN_DIR/verifier.md" "$RUN_DIR/verifier.log" \
  "$RUN_DIR/summary.txt"

START_TIME="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
START_EPOCH="$(date +%s)"
PLANNER_COUNT=0
IMPLEMENTER_COUNT=0
REVIEWER_COUNT=0
VERIFIER_COUNT=0
REVIEW_RETRY_COUNT=0
FINAL_STATUS="FAIL"
FAILURE_STAGE=""
FAILURE_REASON=""

write_summary() {
  local rc="$1"
  local end_time end_epoch duration
  end_time="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  end_epoch="$(date +%s)"
  duration=$((end_epoch - START_EPOCH))

  if [[ "$rc" -ne 0 && -z "$FAILURE_REASON" ]]; then
    FAILURE_REASON="loop exited with status $rc"
  fi

  {
    printf 'Start: %s\n' "$START_TIME"
    printf 'End: %s\n' "$end_time"
    printf 'Duration seconds: %s\n' "$duration"
    printf 'Planner runs: %s\n' "$PLANNER_COUNT"
    printf 'Implementer runs: %s\n' "$IMPLEMENTER_COUNT"
    printf 'Reviewer runs: %s\n' "$REVIEWER_COUNT"
    printf 'Verifier runs: %s\n' "$VERIFIER_COUNT"
    printf 'Reviewer retries: %s\n' "$REVIEW_RETRY_COUNT"
    printf 'Final status: %s\n' "$FINAL_STATUS"
    if [[ "$FINAL_STATUS" == "FAIL" ]]; then
      printf 'Failure stage: %s\n' "${FAILURE_STAGE:-unknown}"
      printf 'Failure reason: %s\n' "${FAILURE_REASON:-unknown}"
    fi
  } > "$RUN_DIR/summary.txt"
}

trap 'rc=$?; write_summary "$rc"' EXIT

last_line_equals() {
  local expected="$1"
  local file="$2"
  [[ "$(tail -n 1 "$file")" == "$expected" ]]
}

run_role() {
  local role="$1"
  local sandbox="$2"
  local prompt="$3"
  local artifact="${4:-$role}"
  local output="$RUN_DIR/$artifact.md"
  local log="$RUN_DIR/$artifact.log"

  case "$role" in
    planner) PLANNER_COUNT=$((PLANNER_COUNT + 1)) ;;
    implementer) IMPLEMENTER_COUNT=$((IMPLEMENTER_COUNT + 1)) ;;
    reviewer) REVIEWER_COUNT=$((REVIEWER_COUNT + 1)) ;;
    verifier) VERIFIER_COUNT=$((VERIFIER_COUNT + 1)) ;;
  esac

  echo "[loop-poc] $artifact ($sandbox)"
  if ! "$CODEX_BIN" exec --ephemeral -s "$sandbox" -C "$WORKSPACE" -o "$output" "$prompt" >"$log" 2>&1; then
    FAILURE_STAGE="$role"
    FAILURE_REASON="$role command failed; see $log"
    echo "[loop-poc] $artifact failed; log: $log" >&2
    cat "$log" >&2
    exit 1
  fi

  if [[ ! -s "$output" ]]; then
    FAILURE_STAGE="$role"
    FAILURE_REASON="$role produced no final output: $output"
    echo "[loop-poc] $artifact produced no final output: $output" >&2
    exit 1
  fi

  if [[ "$artifact" != "$role" ]]; then
    cp "$output" "$RUN_DIR/$role.md"
    cp "$log" "$RUN_DIR/$role.log"
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
REVIEW_FEEDBACK=""
ATTEMPT=1

while :; do
implementer_prompt=$(cat <<EOF_IMPLEMENT
ROLE: implementer
TASK:
$TASK

PLANNER OUTPUT:
<planner>
$PLAN
</planner>

REVIEW FEEDBACK FROM PREVIOUS ATTEMPT:
<review-feedback>
${REVIEW_FEEDBACK:-None. This is the first implementation attempt.}
</review-feedback>

Implement the task with the smallest reasonable change inside the workspace.
If review feedback is present, address that feedback before reporting completion.
Follow repository rules. Run focused checks if possible.
Do not commit or push.
End with exactly one of these lines:
IMPLEMENTATION: COMPLETE
IMPLEMENTATION: BLOCKED
EOF_IMPLEMENT
)
run_role "implementer" "workspace-write" "$implementer_prompt" "implementer-$ATTEMPT"

if ! last_line_equals "IMPLEMENTATION: COMPLETE" "$RUN_DIR/implementer.md"; then
  FAILURE_STAGE="implementer"
  FAILURE_REASON="implementer did not report IMPLEMENTATION: COMPLETE on attempt $ATTEMPT"
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
run_role "reviewer" "read-only" "$reviewer_prompt" "reviewer-$ATTEMPT"

if last_line_equals "VERDICT: PASS" "$RUN_DIR/reviewer.md"; then
  break
fi

if ! last_line_equals "VERDICT: FAIL" "$RUN_DIR/reviewer.md"; then
  FAILURE_STAGE="reviewer"
  FAILURE_REASON="reviewer returned an invalid verdict on attempt $ATTEMPT"
  echo "[loop-poc] reviewer returned an invalid verdict" >&2
  exit 1
fi

if (( REVIEW_RETRY_COUNT >= MAX_RETRIES )); then
  FAILURE_STAGE="reviewer"
  FAILURE_REASON="reviewer rejected attempt $ATTEMPT and maximum retries ($MAX_RETRIES) were exhausted"
  echo "[loop-poc] reviewer rejected the implementation; maximum retries ($MAX_RETRIES) exhausted" >&2
  exit 1
fi

REVIEW_FEEDBACK="$(cat "$RUN_DIR/reviewer.md")"
REVIEW_RETRY_COUNT=$((REVIEW_RETRY_COUNT + 1))
ATTEMPT=$((ATTEMPT + 1))
echo "[loop-poc] reviewer requested rework; retry $REVIEW_RETRY_COUNT/$MAX_RETRIES"
done

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
  FAILURE_STAGE="verifier"
  FAILURE_REASON="verifier rejected the result"
  echo "[loop-poc] verifier rejected the result" >&2
  exit 1
fi

if [[ "$WRITE_RESULT" == "1" ]]; then
  python3 - "$RUN_DIR" "$RUN_ID" "$RESULT_TASK_ID" "$RESULT_OPEN_EVENT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

folder, run_id, task_id, open_event = Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
proof = folder / "verifier.md"
proof_hash = hashlib.sha256(proof.read_bytes()).hexdigest()
result = {"schema_version": 1, "run_id": run_id, "task_id": task_id,
          "task_open_event": open_event, "verdict": "PASS",
          "evidence": [{"path": f".newwork/runs/{run_id}/verifier.md",
                        "sha256": proof_hash}],
          "verifier_artifact": {"path": f".newwork/runs/{run_id}/verifier.md", "sha256": proof_hash}}
with (folder / "verification-result.json").open("x", encoding="utf-8") as handle:
    json.dump(result, handle, sort_keys=True)
    handle.write("\n")
PY
fi

FINAL_STATUS="PASS"
echo "[loop-poc] PASS"
echo "[loop-poc] artifacts: $RUN_DIR"
