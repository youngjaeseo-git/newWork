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
    printf '%s\n' "LOOP POC OK" > "$workspace/result.txt"
    {
      printf '%s\n' "Implemented result.txt."
      printf '%s\n' "IMPLEMENTATION: COMPLETE"
    } > "$output"
    ;;
  *"ROLE: reviewer"*)
    role="reviewer"
    if [[ "${FAKE_REVIEW_NO_OUTPUT:-0}" == "1" ]]; then
      :
    elif [[ "${FAKE_REVIEW_FAIL:-0}" == "1" ]]; then
      printf '%s\n' "Forced review failure." "VERDICT: FAIL" > "$output"
    elif [[ "$(cat "$workspace/result.txt" 2>/dev/null || true)" == "LOOP POC OK" ]]; then
      printf '%s\n' "Review found the requested result." "VERDICT: PASS" > "$output"
    else
      printf '%s\n' "Result is missing or wrong." "VERDICT: FAIL" > "$output"
    fi
    ;;
  *"ROLE: verifier"*)
    role="verifier"
    if [[ "$prompt" != *"PLANNER OUTPUT:"* || "$prompt" != *"Plan: create result.txt with the requested content."* ]]; then
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
EXPECTED_FAIL
)
actual_fail="$(cat "$FAIL_WORKSPACE/calls.log")"
[[ "$actual_fail" == "$expected_fail" ]]
[[ ! -e "$FAIL_RUN_DIR/verifier.md" ]]

echo "[test] reviewer gate PASS"

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

echo "[test] loop-agent PoC PASS"
