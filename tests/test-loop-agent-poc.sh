#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/newwork-loop-agent-test.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

WORKSPACE="$TMP_ROOT/workspace"
RUN_DIR="$TMP_ROOT/run"
FAKE_CODEX="$TMP_ROOT/fake-codex"
mkdir -p "$WORKSPACE" "$RUN_DIR"

cat > "$FAKE_CODEX" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail

sandbox=""
workspace=""
output=""
prompt="${*: -1}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    exec|--ephemeral) shift ;;
    -s) sandbox="$2"; shift 2 ;;
    -C) workspace="$2"; shift 2 ;;
    -o) output="$2"; shift 2 ;;
    *) shift ;;
  esac
done

case "$prompt" in
  *"ROLE: planner"*)
    role="planner"
    printf '%s\n' "Plan: create result.txt with the requested content." > "$output"
    ;;
  *"ROLE: implementer"*)
    role="implementer"
    implementer_runs="$(grep -c '^implementer:' "$workspace/calls.log" 2>/dev/null || true)"
    if [[ "${FAKE_REVIEW_RETRY:-0}" == "1" && "$implementer_runs" == "0" ]]; then
      printf '%s\n' "LOOP POC NEEDS REVIEW" > "$workspace/result.txt"
      printf '%s\n' "Created provisional result." "IMPLEMENTATION: COMPLETE" > "$output"
    elif [[ "${FAKE_REVIEW_RETRY:-0}" == "1" && "$prompt" != *"Reviewer feedback: replace provisional result."* ]]; then
      printf '%s\n' "Review feedback was not forwarded." "IMPLEMENTATION: BLOCKED" > "$output"
    else
      printf '%s\n' "LOOP POC OK" > "$workspace/result.txt"
      printf '%s\n' "Implemented result.txt." "IMPLEMENTATION: COMPLETE" > "$output"
    fi
    ;;
  *"ROLE: reviewer"*)
    role="reviewer"
    if [[ "${FAKE_REVIEW_NO_OUTPUT:-0}" == "1" ]]; then
      :
    elif [[ "${FAKE_REVIEW_FAIL:-0}" == "1" ]]; then
      printf '%s\n' "Forced review failure." "VERDICT: FAIL" > "$output"
    elif [[ "${FAKE_REVIEW_RETRY:-0}" == "1" && "$(cat "$workspace/result.txt" 2>/dev/null || true)" == "LOOP POC NEEDS REVIEW" ]]; then
      printf '%s\n' "Reviewer feedback: replace provisional result." "VERDICT: FAIL" > "$output"
    elif [[ "$(cat "$workspace/result.txt" 2>/dev/null || true)" == "LOOP POC OK" ]]; then
      printf '%s\n' "Review found the requested result." "VERDICT: PASS" > "$output"
    else
      printf '%s\n' "Result is missing or wrong." "VERDICT: FAIL" > "$output"
    fi
    ;;
  *"ROLE: verifier"*)
    role="verifier"
    if [[ "${FAKE_VERIFY_FAIL:-0}" == "1" ]]; then
      printf '%s\n' "Forced verification failure." "VERDICT: FAIL" > "$output"
    elif [[ "$prompt" != *"PLANNER OUTPUT:"* || "$prompt" != *"Plan: create result.txt with the requested content."* ]]; then
      printf '%s\n' "Planner acceptance context was not forwarded." "VERDICT: FAIL" > "$output"
    elif [[ "$(cat "$workspace/result.txt" 2>/dev/null || true)" == "LOOP POC OK" ]]; then
      printf '%s\n' "Verified result.txt content." "VERDICT: PASS" > "$output"
    else
      printf '%s\n' "Acceptance check failed." "VERDICT: FAIL" > "$output"
    fi
    ;;
  *)
    echo "unexpected prompt" >&2
    exit 2
    ;;
esac

printf '%s:%s\n' "$role" "$sandbox" >> "$workspace/calls.log"
FAKE
chmod +x "$FAKE_CODEX"

LOOP_AGENT_POC_CODEX_BIN="$FAKE_CODEX" \
LOOP_AGENT_POC_RUN_DIR="$RUN_DIR" \
  "$ROOT_DIR/run.sh" loop-poc "Create result.txt containing exactly LOOP POC OK" "$WORKSPACE"

[[ "$(cat "$WORKSPACE/result.txt")" == "LOOP POC OK" ]]

expected=$(cat <<'EXPECTED'
planner:read-only
implementer:workspace-write
reviewer:read-only
verifier:read-only
EXPECTED
)
actual="$(cat "$WORKSPACE/calls.log")"
[[ "$actual" == "$expected" ]]

grep -qx 'VERDICT: PASS' "$RUN_DIR/reviewer.md"
grep -qx 'VERDICT: PASS' "$RUN_DIR/verifier.md"
grep -qx 'Planner runs: 1' "$RUN_DIR/summary.txt"
grep -qx 'Implementer runs: 1' "$RUN_DIR/summary.txt"
grep -qx 'Reviewer runs: 1' "$RUN_DIR/summary.txt"
grep -qx 'Verifier runs: 1' "$RUN_DIR/summary.txt"
grep -qx 'Reviewer retries: 0' "$RUN_DIR/summary.txt"
grep -qx 'Final status: PASS' "$RUN_DIR/summary.txt"
grep -Eq '^Start: [0-9]{4}-[0-9]{2}-[0-9]{2}T' "$RUN_DIR/summary.txt"
grep -Eq '^End: [0-9]{4}-[0-9]{2}-[0-9]{2}T' "$RUN_DIR/summary.txt"
grep -Eq '^Duration seconds: [0-9]+$' "$RUN_DIR/summary.txt"

echo "[test] normal path PASS"

RETRY_WORKSPACE="$TMP_ROOT/retry-workspace"
RETRY_RUN_DIR="$TMP_ROOT/retry-run"
mkdir -p "$RETRY_WORKSPACE" "$RETRY_RUN_DIR"

FAKE_REVIEW_RETRY=1 \
LOOP_AGENT_POC_CODEX_BIN="$FAKE_CODEX" \
LOOP_AGENT_POC_RUN_DIR="$RETRY_RUN_DIR" \
  "$ROOT_DIR/run.sh" loop-poc "Create result.txt containing exactly LOOP POC OK" "$RETRY_WORKSPACE"

[[ "$(cat "$RETRY_WORKSPACE/result.txt")" == "LOOP POC OK" ]]
expected_retry=$(cat <<'EXPECTED_RETRY'
planner:read-only
implementer:workspace-write
reviewer:read-only
implementer:workspace-write
reviewer:read-only
verifier:read-only
EXPECTED_RETRY
)
actual_retry="$(cat "$RETRY_WORKSPACE/calls.log")"
[[ "$actual_retry" == "$expected_retry" ]]
grep -qx 'Reviewer feedback: replace provisional result.' "$RETRY_RUN_DIR/reviewer-1.md"
grep -qx 'VERDICT: PASS' "$RETRY_RUN_DIR/reviewer-2.md"
grep -qx 'Implementer runs: 2' "$RETRY_RUN_DIR/summary.txt"
grep -qx 'Reviewer runs: 2' "$RETRY_RUN_DIR/summary.txt"
grep -qx 'Verifier runs: 1' "$RETRY_RUN_DIR/summary.txt"
grep -qx 'Reviewer retries: 1' "$RETRY_RUN_DIR/summary.txt"
grep -qx 'Final status: PASS' "$RETRY_RUN_DIR/summary.txt"

echo "[test] reviewer retry path PASS"


FAIL_WORKSPACE="$TMP_ROOT/fail-workspace"
FAIL_RUN_DIR="$TMP_ROOT/fail-run"
mkdir -p "$FAIL_WORKSPACE" "$FAIL_RUN_DIR"

set +e
FAKE_REVIEW_FAIL=1 \
LOOP_AGENT_POC_CODEX_BIN="$FAKE_CODEX" \
LOOP_AGENT_POC_RUN_DIR="$FAIL_RUN_DIR" \
  "$ROOT_DIR/run.sh" loop-poc "Create result.txt containing exactly LOOP POC OK" "$FAIL_WORKSPACE" \
  >"$TMP_ROOT/fail.out" 2>&1
fail_rc=$?
set -e

[[ "$fail_rc" -ne 0 ]]
expected_fail=$(cat <<'EXPECTED_FAIL'
planner:read-only
implementer:workspace-write
reviewer:read-only
implementer:workspace-write
reviewer:read-only
implementer:workspace-write
reviewer:read-only
EXPECTED_FAIL
)
actual_fail="$(cat "$FAIL_WORKSPACE/calls.log")"
[[ "$actual_fail" == "$expected_fail" ]]
[[ ! -e "$FAIL_RUN_DIR/verifier.md" ]]
grep -qx 'Implementer runs: 3' "$FAIL_RUN_DIR/summary.txt"
grep -qx 'Reviewer runs: 3' "$FAIL_RUN_DIR/summary.txt"
grep -qx 'Reviewer retries: 2' "$FAIL_RUN_DIR/summary.txt"
grep -qx 'Final status: FAIL' "$FAIL_RUN_DIR/summary.txt"
grep -qx 'Failure stage: reviewer' "$FAIL_RUN_DIR/summary.txt"
grep -qx 'Failure reason: reviewer rejected attempt 3 and maximum retries (2) were exhausted' "$FAIL_RUN_DIR/summary.txt"

echo "[test] reviewer retry limit PASS"

VERIFY_FAIL_WORKSPACE="$TMP_ROOT/verify-fail-workspace"
VERIFY_FAIL_RUN_DIR="$TMP_ROOT/verify-fail-run"
mkdir -p "$VERIFY_FAIL_WORKSPACE" "$VERIFY_FAIL_RUN_DIR"

set +e
FAKE_VERIFY_FAIL=1 \
LOOP_AGENT_POC_CODEX_BIN="$FAKE_CODEX" \
LOOP_AGENT_POC_RUN_DIR="$VERIFY_FAIL_RUN_DIR" \
  "$ROOT_DIR/run.sh" loop-poc "Create result.txt containing exactly LOOP POC OK" "$VERIFY_FAIL_WORKSPACE" \
  >"$TMP_ROOT/verify-fail.out" 2>&1
verify_fail_rc=$?
set -e

[[ "$verify_fail_rc" -ne 0 ]]
expected_verify_fail=$(cat <<'EXPECTED_VERIFY_FAIL'
planner:read-only
implementer:workspace-write
reviewer:read-only
verifier:read-only
EXPECTED_VERIFY_FAIL
)
actual_verify_fail="$(cat "$VERIFY_FAIL_WORKSPACE/calls.log")"
[[ "$actual_verify_fail" == "$expected_verify_fail" ]]
grep -qx 'Reviewer retries: 0' "$VERIFY_FAIL_RUN_DIR/summary.txt"
grep -qx 'Final status: FAIL' "$VERIFY_FAIL_RUN_DIR/summary.txt"
grep -qx 'Failure stage: verifier' "$VERIFY_FAIL_RUN_DIR/summary.txt"
grep -qx 'Failure reason: verifier rejected the result' "$VERIFY_FAIL_RUN_DIR/summary.txt"

echo "[test] verifier fail stops without retry PASS"

STALE_WORKSPACE="$TMP_ROOT/stale-workspace"
STALE_RUN_DIR="$TMP_ROOT/stale-run"
mkdir -p "$STALE_WORKSPACE" "$STALE_RUN_DIR"
printf '%s\n' "VERDICT: PASS" > "$STALE_RUN_DIR/reviewer.md"
printf '%s\n' "VERDICT: PASS" > "$STALE_RUN_DIR/verifier.md"
printf '%s\n' "old verifier log" > "$STALE_RUN_DIR/verifier.log"

set +e
FAKE_REVIEW_NO_OUTPUT=1 \
LOOP_AGENT_POC_CODEX_BIN="$FAKE_CODEX" \
LOOP_AGENT_POC_RUN_DIR="$STALE_RUN_DIR" \
  "$ROOT_DIR/run.sh" loop-poc "Create result.txt containing exactly LOOP POC OK" "$STALE_WORKSPACE" \
  >"$TMP_ROOT/stale.out" 2>&1
stale_rc=$?
set -e

[[ "$stale_rc" -ne 0 ]]
[[ ! -e "$STALE_RUN_DIR/reviewer.md" ]]
[[ ! -e "$STALE_RUN_DIR/verifier.md" ]]
[[ ! -e "$STALE_RUN_DIR/verifier.log" ]]

echo "[test] stale artifact gate PASS"

BOUND_WORKSPACE="$TMP_ROOT/bound-workspace"
mkdir -p "$BOUND_WORKSPACE"
git -C "$BOUND_WORKSPACE" init -q
git -C "$BOUND_WORKSPACE" config user.name Test
git -C "$BOUND_WORKSPACE" config user.email test@example.invalid
printf '%s\n' baseline > "$BOUND_WORKSPACE/README.md"
git -C "$BOUND_WORKSPACE" add README.md
git -C "$BOUND_WORKSPACE" commit -qm baseline
MEMORY=(python3 "$ROOT_DIR/scripts/newwork-memory.py" --root "$BOUND_WORKSPACE")
"${MEMORY[@]}" init > /dev/null
"${MEMORY[@]}" start session-1 > /dev/null
open_json="$("${MEMORY[@]}" open-task task-1 'Verify result')"
open_event="$(printf '%s' "$open_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["event_seq"])')"
BOUND_RUN="$BOUND_WORKSPACE/.newwork/runs/run-1"
LOOP_AGENT_POC_CODEX_BIN="$FAKE_CODEX" \
LOOP_AGENT_POC_RUN_DIR="$BOUND_RUN" \
LOOP_AGENT_POC_TASK_ID=task-1 \
LOOP_AGENT_POC_TASK_OPEN_EVENT="$open_event" \
  "$ROOT_DIR/run.sh" loop-poc 'Create result.txt containing exactly LOOP POC OK' "$BOUND_WORKSPACE"
[[ -f "$BOUND_RUN/verification-result.json" ]]
"${MEMORY[@]}" close-task task-1 --result .newwork/runs/run-1/verification-result.json > /dev/null

"${MEMORY[@]}" open-task task-2 'Retry exhausted' > /dev/null
open_event_2="$("${MEMORY[@]}" status | python3 -c 'import json,sys; print(json.load(sys.stdin)["event_seq"])')"
BOUND_FAIL_RUN="$BOUND_WORKSPACE/.newwork/runs/run-2"
set +e
FAKE_REVIEW_FAIL=1 LOOP_AGENT_POC_MAX_RETRIES=0 \
LOOP_AGENT_POC_CODEX_BIN="$FAKE_CODEX" \
LOOP_AGENT_POC_RUN_DIR="$BOUND_FAIL_RUN" \
LOOP_AGENT_POC_TASK_ID=task-2 \
LOOP_AGENT_POC_TASK_OPEN_EVENT="$open_event_2" \
  "$ROOT_DIR/run.sh" loop-poc 'Create result.txt containing exactly LOOP POC OK' "$BOUND_WORKSPACE" > /dev/null 2>&1
bound_fail_rc=$?
set -e
[[ "$bound_fail_rc" -ne 0 ]]
[[ -f "$BOUND_FAIL_RUN/summary.txt" ]]
[[ ! -e "$BOUND_FAIL_RUN/verification-result.json" ]]
set +e
"${MEMORY[@]}" close-task task-2 --result .newwork/runs/run-2/verification-result.json > "$TMP_ROOT/no-result.json"
close_fail_rc=$?
set -e
[[ "$close_fail_rc" -eq 13 ]]
[[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$TMP_ROOT/no-result.json")" == "invalid_evidence" ]]
python3 - "$BOUND_WORKSPACE/.newwork/STATE.yaml" <<'PY'
import json, sys
state = json.load(open(sys.argv[1], encoding="utf-8"))
assert "task-2" in state["open_tasks"]
PY
echo "[test] optional verification result and retry-limit gate PASS"

echo "[test] loop-agent PoC PASS"
