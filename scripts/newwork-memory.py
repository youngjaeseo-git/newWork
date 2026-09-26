#!/usr/bin/env python3
"""Small, dependency-free Memory Foundation for newWork v2.

The .yaml files contain JSON, which is valid YAML 1.2. Events are the source of
truth; STATE/FINDINGS/LESSONS are replaceable projections.
"""

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = 1
STATUSES = {"UNVERIFIED", "EVIDENCE_FOUND", "PENDING_CONFIRMATION", "CONFIRMED", "REFUTED", "SUPERSEDED"}
LESSON_EFFECTS = {"supported", "inconclusive", "contradicted"}
INTERNAL_PROJECTIONS = (".newwork/events.jsonl", ".newwork/STATE.yaml",
                        ".newwork/FINDINGS.yaml", ".newwork/LESSONS.yaml")
EXIT = {"ok": 0, "invalid_input": 2, "conflict": 10, "review_required": 11,
        "ledger_corrupt": 12, "invalid_evidence": 13, "io_error": 14}
RETRY_EVENTS = {"start": "session_started", "end": "session_ended", "finding": "finding_recorded",
                "interrupt": "session_interrupted"}
LIFECYCLE_EVENTS = {"session_started", "session_ended", "session_interrupted"}


class MemoryFailure(Exception):
    def __init__(self, status, message, **details):
        super().__init__(message)
        self.status, self.details = status, details


def fail(status, message, **details):
    raise MemoryFailure(status, message, **details)


def reply(status="ok", **fields):
    print(canonical({"status": status, **fields}))


def request_key(command, data):
    return digest({"command": command, "request": data})


def retry(events, state, findings, command, data):
    fingerprint = request_key(command, data)
    for event in events:
        if event.get("request_fingerprint") == fingerprint:
            if event["type"] != RETRY_EVENTS[command]:
                fail("ledger_corrupt", "request fingerprint belongs to another event")
            expected_active = None if command in ("end", "interrupt") else data.get("session_id", data.get("id"))
            latest_lifecycle = next((item for item in reversed(events) if item["type"] in LIFECYCLE_EVENTS), None)
            current_valid = state["active_session"] == expected_active
            if command in ("end", "interrupt"):
                current_valid = current_valid and latest_lifecycle["seq"] == event["seq"]
            if command == "finding":
                current_valid = current_valid and findings["items"].get(data["id"]) == event["data"]
            if not current_valid:
                fail("conflict", "request was applied previously but its result is no longer current",
                     active_session=state["active_session"])
            return event, fingerprint
    return None, fingerprint


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git(root):
    def run(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
        return result.stdout.strip()

    excluded = [f":(exclude){name}" for name in (*INTERNAL_PROJECTIONS, ".newwork/.lock")]
    tracked = subprocess.run(["git", "-C", str(root), "diff", "HEAD", "--binary", "--", ".",
                              *excluded], capture_output=True, check=True).stdout
    untracked = run("ls-files", "--others", "--exclude-standard", "--", ".", *excluded).splitlines()
    fingerprint = hashlib.sha256(tracked)
    for name in untracked:
        path = root / name
        fingerprint.update(name.encode("utf-8") + b"\0")
        if path.is_file():
            fingerprint.update(hashlib.sha256(path.read_bytes()).digest())
    return {"branch": run("branch", "--show-current"), "head": run("rev-parse", "HEAD"),
            "dirty": bool(tracked or untracked), "worktree_sha256": fingerprint.hexdigest()}


def tree_identity(root, tree):
    listing = subprocess.run(["git", "-C", str(root), "ls-tree", "-rz", "--full-tree", tree],
                             capture_output=True, check=True).stdout
    excluded = {name.encode("utf-8") for name in INTERNAL_PROJECTIONS}
    fingerprint = hashlib.sha256()
    for entry in listing.split(b"\0"):
        if entry and entry.split(b"\t", 1)[1] not in excluded:
            fingerprint.update(entry + b"\0")
    return fingerprint.hexdigest()


def accepted_tree_identity(root):
    # A temporary index observes the complete worktree, including untracked files,
    # without changing the user's staging area.
    with tempfile.TemporaryDirectory() as directory:
        environment = {**os.environ, "GIT_INDEX_FILE": str(Path(directory) / "index")}
        def run(*args):
            return subprocess.run(["git", "-C", str(root), *args], env=environment,
                                  capture_output=True, text=True, check=True).stdout.strip()
        run("read-tree", "HEAD")
        run("add", "-A", "--", ".")
        return tree_identity(root, run("write-tree"))


def checkpoint_transition(root, events, recorded, current):
    if recorded is None or current["branch"] != recorded["branch"] or not current["branch"]:
        return False
    acceptance = next((event for event in reversed(events) if event["type"] == "git_reconciled"
                       and event["data"].get("accepted_change_identity")
                       and event["data"]["git"] == recorded), None)
    if acceptance is None or current["head"] == recorded["head"]:
        return False
    parents = subprocess.run(["git", "-C", str(root), "rev-list", "--parents", "-n", "1", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.split()
    if len(parents) != 2 or parents[1] != recorded["head"]:
        return False
    if subprocess.run(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
                      capture_output=True, check=True).stdout:
        return False
    if tree_identity(root, "HEAD") != acceptance["data"]["accepted_change_identity"]:
        return False
    for name in INTERNAL_PROJECTIONS:
        committed = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{name}"],
                                   capture_output=True)
        try:
            current_bytes = (root / name).read_bytes()
        except OSError:
            return False
        if committed.returncode or committed.stdout != current_bytes:
            return False
    return True


def git_drift(root, events, recorded, current):
    return recorded is not None and recorded != current and not checkpoint_transition(root, events, recorded, current)


def root_for(path):
    root = Path(path).resolve()
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, check=True)
    if root != Path(result.stdout.strip()).resolve():
        fail("invalid_input", "--root must be the Git repository root")
    return root


@contextmanager
def locked(base):
    base.mkdir(exist_ok=True)
    with (base / ".lock").open("a+b") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def read_events(base):
    path = base / "events.jsonl"
    if not path.exists():
        fail("invalid_input", "Memory Foundation not initialized; run init")
    events = []
    previous = "0" * 64
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                fail("ledger_corrupt", f"invalid event line {number}: {exc}")
            checksum = event.pop("hash", None)
            if event.get("seq") != number or event.get("prev_hash") != previous or checksum != digest(event):
                fail("ledger_corrupt", f"event chain mismatch at line {number}")
            event["hash"] = checksum
            events.append(event)
            previous = checksum
    if not events or events[0]["type"] != "initialized":
        fail("ledger_corrupt", "event ledger has no initialization event")
    return events


def append(base, events, kind, data, fingerprint=None):
    event = {"seq": len(events) + 1, "at": now(), "type": kind, "data": data,
             "prev_hash": events[-1]["hash"] if events else "0" * 64}
    if fingerprint:
        event["request_fingerprint"] = fingerprint
    event["hash"] = digest(event)
    with (base / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(canonical(event) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    events.append(event)


def project(events):
    state = {"schema": SCHEMA, "event_seq": 0, "active_session": None, "next_start": "",
             "open_tasks": {}, "pending_confirmations": {}, "last_git": None}
    findings = {"schema": SCHEMA, "event_seq": 0, "items": {}}
    lessons = {"schema": SCHEMA, "event_seq": 0, "items": {}}
    for event in events:
        data, kind = event["data"], event["type"]
        state["event_seq"] = findings["event_seq"] = lessons["event_seq"] = event["seq"]
        if kind == "session_started":
            state["active_session"] = data["id"]
            state["last_git"] = data["git"]
        elif kind == "session_ended":
            state["active_session"] = None
            state["next_start"] = data["next_start"]
            state["last_git"] = data["git"]
        elif kind == "session_interrupted":
            state["active_session"] = None
        elif kind == "task_opened":
            state["open_tasks"][data["id"]] = {**data, "open_event": event["seq"]}
        elif kind == "task_closed":
            state["open_tasks"].pop(data["id"], None)
        elif kind == "git_reconciled":
            state["last_git"] = data["git"]
        elif kind == "confirmation_requested":
            state["pending_confirmations"][data["id"]] = data
        elif kind == "confirmation_resolved":
            state["pending_confirmations"].pop(data["id"], None)
        elif kind == "finding_recorded":
            findings["items"][data["id"]] = data
        elif kind == "lesson_proposed":
            lessons["items"][data["id"]] = {**data, "status": "candidate",
                                            "reuse_policy": "live_freshness_check_required",
                                            "proposed_event": event["seq"]}
        elif kind in {"lesson_approved", "lesson_rejected", "lesson_withdrawn"}:
            item = lessons["items"][data["id"]]
            item["status"] = {"lesson_approved": "approved", "lesson_rejected": "rejected",
                              "lesson_withdrawn": "withdrawn"}[kind]
            item["decision_reason"] = data["reason"]
            item["decision_event"] = event["seq"]
        elif kind == "lesson_replaced":
            old, new = lessons["items"][data["id"]], lessons["items"][data["replacement_id"]]
            old.update(status="replaced", replaced_by=data["replacement_id"], decision_reason=data["reason"],
                       decision_event=event["seq"])
            new.update(status="approved", replaces=data["id"], decision_reason=data["reason"],
                       decision_event=event["seq"])
        else:
            if kind != "initialized":
                fail("ledger_corrupt", f"unknown event type: {kind}")
    return state, findings, lessons


def write_json(path, value):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def projections(base, events):
    values = project(events)
    for name, value in zip(("STATE.yaml", "FINDINGS.yaml", "LESSONS.yaml"), values):
        write_json(base / name, value)
    return values


def consistency(base, events):
    expected = project(events)
    mismatches = []
    for name, value in zip(("STATE.yaml", "FINDINGS.yaml", "LESSONS.yaml"), expected):
        try:
            actual = json.loads((base / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            actual = None
        if actual != value:
            mismatches.append(name)
    return mismatches


def evidence(root, supplied):
    path = (root / supplied).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        fail("invalid_evidence", "evidence must be an existing file inside the repository", path=supplied)
    relative = path.relative_to(root).as_posix()
    if relative.startswith(".git/") or relative == ".git":
        fail("invalid_evidence", "Git internals cannot be evidence", path=supplied)
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def stale_evidence(root, findings):
    stale = []
    for item in findings["items"].values():
        for ref in item["evidence"]:
            try:
                current = evidence(root, ref["path"])
            except MemoryFailure:
                stale.append(ref["path"])
                continue
            if current["sha256"] != ref["sha256"]:
                stale.append(ref["path"])
    return sorted(set(stale))


def lesson_reference(root, supplied):
    ref = evidence(root, supplied)
    if ref["path"] in INTERNAL_PROJECTIONS or ref["path"] == ".newwork/.lock":
        fail("invalid_evidence", "Memory ledger and snapshots cannot be lesson evidence")
    return ref


def lesson_references(item):
    return [item["source"], *item["supporting"], *item["contradictory"]]


def changed_lesson_references(root, item):
    stale = []
    for ref in lesson_references(item):
        try:
            current = lesson_reference(root, ref["path"])
        except MemoryFailure:
            stale.append(ref["path"])
            continue
        if current != ref:
            stale.append(ref["path"])
    return sorted(set(stale))


def stale_lesson_evidence(root, lessons):
    stale = []
    for item in lessons["items"].values():
        if item["status"] in {"candidate", "approved"}:
            stale.extend(changed_lesson_references(root, item))
    return sorted(set(stale))


def require_fresh_lesson(root, item):
    stale = changed_lesson_references(root, item)
    if stale:
        fail("review_required", "lesson source or evidence changed; candidate preserved", stale_evidence=stale)


def lesson_support_is_recorded(ref, findings):
    if any(ref in item["evidence"] for item in findings["items"].values()):
        return True
    parts = Path(ref["path"]).parts
    return len(parts) >= 4 and parts[:2] == (".newwork", "runs")


def require_session(state):
    if state["active_session"] is None:
        fail("conflict", "start a session first")


def verification_result(root, events, supplied, task_id, open_event):
    ref = evidence(root, supplied)
    parts = Path(ref["path"]).parts
    if len(parts) != 4 or parts[:2] != (".newwork", "runs") or parts[3] != "verification-result.json":
        fail("invalid_evidence", "result must be under .newwork/runs/<run-id>/verification-result.json")
    if any(item["type"] == "task_closed" and item["data"].get("result", {}).get("path") == ref["path"]
           for item in events):
        fail("conflict", "verification result was already consumed")
    try:
        content = (root / ref["path"]).read_bytes()
        result = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeError):
        fail("invalid_evidence", "verification result is not valid JSON")
    ref["sha256"] = hashlib.sha256(content).hexdigest()
    if not isinstance(result, dict) or type(result.get("schema_version")) is not int or result["schema_version"] != 1:
        fail("invalid_evidence", "unsupported verification result schema")
    if result.get("run_id") != parts[2] or not parts[2] or result.get("task_id") != task_id:
        fail("conflict", "verification result belongs to another run or task")
    if type(result.get("task_open_event")) is not int or result["task_open_event"] != open_event:
        fail("conflict", "verification result belongs to another task lifecycle")
    if result.get("verdict") != "PASS":
        fail("conflict", "verification verdict is not PASS")
    run_folder = Path(".newwork/runs") / parts[2]
    proofs = result.get("evidence")
    if not isinstance(proofs, list) or not proofs:
        fail("invalid_evidence", "verification result requires evidence")
    for proof in proofs:
        if not isinstance(proof, dict) or not isinstance(proof.get("path"), str) or not isinstance(proof.get("sha256"), str):
            fail("invalid_evidence", "invalid verification evidence entry")
        current = evidence(root, proof["path"])
        if not Path(current["path"]).is_relative_to(run_folder) or current["path"] == ref["path"]:
            fail("invalid_evidence", "verification evidence must belong to the same run")
        if current["sha256"] != proof["sha256"]:
            fail("invalid_evidence", "verification evidence hash changed", path=proof["path"])
    artifact = result.get("verifier_artifact")
    if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str) or not isinstance(artifact.get("sha256"), str):
        fail("invalid_evidence", "verification result requires a verifier artifact")
    verifier = evidence(root, artifact["path"])
    if not Path(verifier["path"]).is_relative_to(run_folder) or verifier["path"] == ref["path"]:
        fail("invalid_evidence", "verifier artifact must belong to the same run")
    try:
        verifier_bytes = (root / verifier["path"]).read_bytes()
        lines = verifier_bytes.decode("utf-8").splitlines()
    except UnicodeError:
        fail("invalid_evidence", "verifier artifact is not UTF-8 text")
    if hashlib.sha256(verifier_bytes).hexdigest() != artifact["sha256"]:
        fail("invalid_evidence", "verifier artifact hash changed", path=artifact["path"])
    last = next((line for line in reversed(lines) if line.strip()), None)
    if last != "VERDICT: PASS":
        fail("conflict", "verifier artifact verdict is not PASS")
    return ref, result


def execute(args):
    root = root_for(args.root)
    base = root / ".newwork"
    with locked(base):
        if args.command == "init":
            if (base / "events.jsonl").exists():
                fail("conflict", "already initialized; existing ledger preserved")
            existing = [name for name in ("STATE.yaml", "FINDINGS.yaml", "LESSONS.yaml", "DECISIONS.md")
                        if (base / name).exists()]
            if existing:
                fail("conflict", "existing Memory Foundation files: " + ", ".join(existing))
            (base / "incidents").mkdir(exist_ok=True)
            (base / "runs").mkdir(exist_ok=True)
            for folder in ("incidents", "runs"):
                marker = base / folder / ".gitkeep"
                if not marker.exists():
                    marker.touch()
            (base / "DECISIONS.md").write_text("# Decisions\n\nNo v2 decisions recorded yet. See docs/decision-log.md for legacy history.\n", encoding="utf-8")
            (base / "events.jsonl").touch(exist_ok=False)
            events = []
            append(base, events, "initialized", {"schema": SCHEMA})
            projections(base, events)
            reply(path=str(base), event_seq=1)
            return
        events = read_events(base)
        state, findings, lessons = project(events)
        if args.command == "lesson-check":
            item = lessons["items"].get(args.id)
            if item is None:
                fail("invalid_input", "lesson id does not exist")
            stale = changed_lesson_references(root, item)
            reusable = (item["status"] == "approved" and item["effect"]["status"] == "supported"
                        and not stale)
            status = "ok" if reusable else "review_required"
            reply(status, lesson_id=args.id, decision=item["status"], reusable=reusable,
                  stale_evidence=stale)
            return
        if args.command == "rebuild":
            projections(base, events)
            reply(event_seq=len(events))
            return
        if args.command in ("reconcile", "status"):
            mismatches = consistency(base, events)
            current = git(root)
            drift = git_drift(root, events, state["last_git"], current)
            stale = stale_evidence(root, findings)
            stale_lessons = stale_lesson_evidence(root, lessons)
            result = {"snapshot_mismatches": mismatches, "git_drift": drift,
                      "recorded_git": state["last_git"], "current_git": current,
                      "active_session": state["active_session"], "event_seq": len(events),
                      "pending_confirmations": state["pending_confirmations"],
                      "stale_evidence": stale, "stale_lesson_evidence": stale_lessons}
            status = "review_required" if mismatches or drift or stale or stale_lessons else "ok"
            reply(status, **result)
            if args.command == "reconcile" and status != "ok":
                return EXIT[status]
            return
        if consistency(base, events):
            fail("review_required", "snapshot differs from ledger; run rebuild before recording new events")
        if args.command == "accept-git":
            observed = git(root)
            identity = accepted_tree_identity(root)
            if git(root) != observed:
                fail("review_required", "Git worktree changed while recording acceptance")
            append(base, events, "git_reconciled", {"git": observed, "reason": args.reason,
                                                    "accepted_change_identity": identity})
        elif args.command == "start":
            request = {"id": args.id}
            prior, fingerprint = retry(events, state, findings, "start", request)
            if prior:
                reply(event_seq=prior["seq"], active_session=state["active_session"], replayed=True)
                return
            if state["active_session"] is not None:
                fail("conflict", "session already active", active_session=state["active_session"])
            current = git(root)
            if git_drift(root, events, state["last_git"], current):
                fail("review_required", "Git state differs from last session; run reconcile and review before start")
            append(base, events, "session_started", {"id": args.id, "git": current}, fingerprint)
        elif args.command == "end":
            request = {"id": args.id, "next_start": args.next_start}
            prior, fingerprint = retry(events, state, findings, "end", request)
            if prior:
                reply(event_seq=prior["seq"], active_session=state["active_session"], replayed=True)
                return
            require_session(state)
            if state["active_session"] != args.id:
                fail("conflict", "end session id does not match active session")
            current = git(root)
            head_changed = ((current["branch"], current["head"]) !=
                            (state["last_git"]["branch"], state["last_git"]["head"]) and
                            not checkpoint_transition(root, events, state["last_git"], current))
            stale = stale_evidence(root, findings)
            if head_changed or stale:
                fail("review_required", "Git HEAD or evidence changed; active session preserved",
                     active_session=args.id, head_changed=head_changed, stale_evidence=stale)
            append(base, events, "session_ended", {"id": args.id,
                                                   "next_start": args.next_start, "git": current}, fingerprint)
        elif args.command == "interrupt":
            request = {"id": args.id, "reason": args.reason}
            prior, fingerprint = retry(events, state, findings, "interrupt", request)
            if prior:
                reply(event_seq=prior["seq"], active_session=state["active_session"], replayed=True)
                return
            require_session(state)
            if state["active_session"] != args.id:
                fail("conflict", "session id does not match active session")
            append(base, events, "session_interrupted", request, fingerprint)
        elif args.command == "request-confirmation":
            require_session(state)
            if args.id in state["pending_confirmations"]:
                fail("conflict", "confirmation id already pending")
            append(base, events, "confirmation_requested", {"id": args.id, "question": args.question})
        elif args.command == "resolve-confirmation":
            require_session(state)
            if args.id not in state["pending_confirmations"]:
                fail("invalid_input", "confirmation id is not pending")
            append(base, events, "confirmation_resolved", {"id": args.id, "answer": args.answer})
        elif args.command == "finding":
            refs = [evidence(root, item) for item in args.evidence]
            request = {"session_id": state["active_session"], "id": args.id, "claim": args.claim,
                       "status": args.status, "evidence": refs}
            prior, fingerprint = retry(events, state, findings, "finding", request)
            if prior:
                reply(event_seq=prior["seq"], active_session=state["active_session"], replayed=True)
                return
            require_session(state)
            if args.status not in STATUSES:
                fail("invalid_input", "unknown finding status")
            if args.status in {"EVIDENCE_FOUND", "CONFIRMED", "REFUTED"} and not refs:
                fail("invalid_evidence", "this status requires at least one evidence file")
            append(base, events, "finding_recorded", {"id": args.id, "claim": args.claim,
                                                     "status": args.status, "evidence": refs}, fingerprint)
        elif args.command == "open-task":
            require_session(state)
            if args.id in state["open_tasks"]:
                fail("conflict", "task id already open")
            append(base, events, "task_opened", {"id": args.id, "title": args.title})
        elif args.command == "close-task":
            require_session(state)
            if args.id not in state["open_tasks"]:
                fail("invalid_input", "task id is not open")
            ref, result = verification_result(root, events, args.result, args.id,
                                              state["open_tasks"][args.id]["open_event"])
            append(base, events, "task_closed", {"id": args.id, "task_open_event": result["task_open_event"],
                                                 "result": ref, "run_id": result["run_id"],
                                                 "evidence": result["evidence"]})
        elif args.command == "lesson-propose":
            require_session(state)
            if not args.id.strip() or not args.claim.strip() or not args.effect_note.strip():
                fail("invalid_input", "lesson id, claim, and effect note must be non-empty")
            if args.id in lessons["items"]:
                fail("conflict", "lesson id already exists")
            if not args.support:
                fail("invalid_evidence", "a separate finding or run evidence file is required")
            source = lesson_reference(root, args.source)
            supporting = [lesson_reference(root, path) for path in args.support]
            contradictory = [lesson_reference(root, path) for path in args.contradict]
            if any(ref["path"] == source["path"] for ref in supporting):
                fail("invalid_evidence", "source alone cannot support a lesson")
            if not any(lesson_support_is_recorded(ref, findings) for ref in supporting):
                fail("invalid_evidence", "at least one supporting reference must be a finding or run artifact")
            append(base, events, "lesson_proposed", {"id": args.id, "scope": args.scope, "claim": args.claim,
                                                     "source": source, "supporting": supporting,
                                                     "contradictory": contradictory,
                                                     "effect": {"status": args.effect, "note": args.effect_note}})
        elif args.command == "lesson-decide":
            require_session(state)
            if not args.reason.strip():
                fail("invalid_input", "lesson decision reason must be non-empty")
            item = lessons["items"].get(args.id)
            if item is None:
                fail("invalid_input", "lesson id does not exist")
            if args.action in {"approve", "reject"}:
                if item["status"] != "candidate" or args.replacement:
                    fail("conflict", "decision requires a candidate and no replacement id")
                if args.action == "approve":
                    if item["effect"]["status"] != "supported":
                        fail("review_required", "effect is not supported; candidate preserved")
                    require_fresh_lesson(root, item)
                kind = "lesson_approved" if args.action == "approve" else "lesson_rejected"
                append(base, events, kind, {"id": args.id, "reason": args.reason})
            elif args.action == "withdraw":
                if item["status"] != "approved" or args.replacement:
                    fail("conflict", "withdrawal requires an approved lesson and no replacement id")
                append(base, events, "lesson_withdrawn", {"id": args.id, "reason": args.reason})
            elif args.action == "replace":
                replacement = lessons["items"].get(args.replacement)
                if item["status"] != "approved" or replacement is None or replacement["status"] != "candidate":
                    fail("conflict", "replacement requires approved old and candidate new lessons")
                if replacement["effect"]["status"] != "supported":
                    fail("review_required", "replacement effect is not supported")
                require_fresh_lesson(root, replacement)
                append(base, events, "lesson_replaced", {"id": args.id, "replacement_id": args.replacement,
                                                         "reason": args.reason})
        else:
            fail("invalid_input", "unsupported command")
        projections(base, events)
        reply(event_seq=len(events), active_session=project(events)[0]["active_session"],
                         pending_confirmations=project(events)[0]["pending_confirmations"],
                         open_tasks=project(events)[0]["open_tasks"],
                         next_start=project(events)[0]["next_start"])


def main():
    class JsonParser(argparse.ArgumentParser):
        def error(self, message):
            fail("invalid_input", message)

    parser = JsonParser(description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "rebuild", "reconcile", "status", "accept-git", "start", "end", "interrupt", "request-confirmation",
                 "resolve-confirmation", "finding", "open-task", "close-task", "lesson-propose", "lesson-decide",
                 "lesson-check"):
        cmd = sub.add_parser(name)
        if name in ("start", "end", "interrupt", "request-confirmation", "resolve-confirmation", "finding", "open-task", "close-task", "lesson-propose", "lesson-decide", "lesson-check"):
            cmd.add_argument("id")
        if name == "end":
            cmd.add_argument("--next-start", required=True)
        if name == "accept-git":
            cmd.add_argument("reason")
        if name == "interrupt":
            cmd.add_argument("reason")
        if name == "request-confirmation":
            cmd.add_argument("question")
        if name == "resolve-confirmation":
            cmd.add_argument("answer")
        if name == "finding":
            cmd.add_argument("claim")
            cmd.add_argument("status", choices=sorted(STATUSES))
            cmd.add_argument("--evidence", action="append", default=[])
        if name == "open-task":
            cmd.add_argument("title")
        if name == "close-task":
            cmd.add_argument("--result", required=True)
        if name == "lesson-propose":
            cmd.add_argument("claim")
            cmd.add_argument("--scope", choices=["project"], default="project")
            cmd.add_argument("--source", required=True)
            cmd.add_argument("--support", action="append", default=[])
            cmd.add_argument("--contradict", action="append", default=[])
            cmd.add_argument("--effect", choices=sorted(LESSON_EFFECTS), required=True)
            cmd.add_argument("--effect-note", required=True)
        if name == "lesson-decide":
            cmd.add_argument("action", choices=["approve", "reject", "withdraw", "replace"])
            cmd.add_argument("--reason", required=True)
            cmd.add_argument("--replacement")
    try:
        args = parser.parse_args()
        return execute(args) or 0
    except MemoryFailure as exc:
        reply(exc.status, message=str(exc), **exc.details)
        return EXIT[exc.status]
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        reply("ledger_corrupt", message=str(exc))
        return EXIT["ledger_corrupt"]
    except (OSError, subprocess.CalledProcessError) as exc:
        reply("io_error", message=str(exc))
        return EXIT["io_error"]
    return 0


if __name__ == "__main__":
    sys.exit(main())
