#!/usr/bin/env python3
"""Memory Foundation acceptance tests in disposable Git repositories."""

import hashlib
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "newwork-memory.py"
RUN = SCRIPT.parents[1] / "run.sh"


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        (self.repo / "README.md").write_text("proof\n", encoding="utf-8")
        (self.repo / "scripts").mkdir()
        shutil.copy2(SCRIPT, self.repo / "scripts/newwork-memory.py")
        shutil.copy2(RUN, self.repo / "run.sh")
        subprocess.run(["git", "-C", str(self.repo), "add", "README.md", "run.sh", "scripts/newwork-memory.py"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "initial"], check=True)

    def call(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.repo), *args],
                                capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def state(self):
        return json.loads((self.repo / ".newwork/STATE.yaml").read_text(encoding="utf-8"))

    def lessons(self):
        return json.loads((self.repo / ".newwork/LESSONS.yaml").read_text(encoding="utf-8"))["items"]

    def lesson_fixture(self):
        self.call("init")
        self.call("start", "lesson-session")
        (self.repo / "retrospective.md").write_text("Keep: verify changes.\n", encoding="utf-8")
        self.call("finding", "proof", "README is proof", "EVIDENCE_FOUND", "--evidence", "README.md")

    def propose_lesson(self, lesson_id, effect="supported", *extra):
        return self.call("lesson-propose", lesson_id, "Verify changes before closing work",
                         "--source", "retrospective.md", "--support", "README.md",
                         "--effect", effect, "--effect-note", "Reviewed the recorded result", *extra)

    def check_lesson(self, lesson_id):
        return json.loads(self.call("lesson-check", lesson_id).stdout)

    def test_project_lesson_live_reuse_requires_current_references(self):
        self.lesson_fixture()
        contrary = self.repo / ".newwork/runs/contrary/log.txt"
        contrary.parent.mkdir(parents=True)
        contrary.write_text("Counterexample\n", encoding="utf-8")
        self.propose_lesson("source", "supported", "--contradict", ".newwork/runs/contrary/log.txt")
        self.call("lesson-decide", "source", "approve", "--reason", "Reviewed")
        self.assertEqual(self.lessons()["source"]["reuse_policy"], "live_freshness_check_required")
        self.assertTrue(self.check_lesson("source")["reusable"])
        for path in (self.repo / "retrospective.md", self.repo / "README.md", contrary):
            original = path.read_bytes()
            path.write_bytes(original + b"changed\n")
            result = self.check_lesson("source")
            self.assertFalse(result["reusable"])
            self.assertEqual(result["status"], "review_required")
            self.assertEqual(self.lessons()["source"]["status"], "approved")
            path.write_bytes(original)
        contrary.unlink()
        self.assertFalse(self.check_lesson("source")["reusable"])
        contrary.write_text("Counterexample\n", encoding="utf-8")
        self.assertTrue(self.check_lesson("source")["reusable"])

    def test_project_lesson_replacement_reuse_chain(self):
        self.lesson_fixture()
        for lesson_id in ("withdrawn", "a", "b", "c"):
            self.propose_lesson(lesson_id)
        self.call("lesson-decide", "withdrawn", "approve", "--reason", "Reviewed")
        self.call("lesson-decide", "withdrawn", "withdraw", "--reason", "Retired")
        self.assertFalse(self.check_lesson("withdrawn")["reusable"])
        self.call("lesson-decide", "a", "approve", "--reason", "Reviewed")
        result = self.call("lesson-decide", "a", "replace", "--replacement", "a",
                           "--reason", "Self", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "conflict")
        self.call("lesson-decide", "a", "replace", "--replacement", "b", "--reason", "Better")
        self.assertFalse(self.check_lesson("a")["reusable"])
        self.assertTrue(self.check_lesson("b")["reusable"])
        self.call("lesson-decide", "b", "replace", "--replacement", "c", "--reason", "Best")
        self.assertEqual([self.check_lesson(item)["reusable"] for item in ("a", "b", "c")],
                         [False, False, True])
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        self.assertFalse(self.check_lesson("c")["reusable"])

    def test_project_lesson_lifecycle_and_projection_rebuild(self):
        self.lesson_fixture()
        before = self.state()["event_seq"]
        result = self.call("lesson-propose", "source-only", "Claim", "--source", "retrospective.md",
                           "--effect", "supported", "--effect-note", "one recollection", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid_evidence")
        self.assertEqual(self.state()["event_seq"], before)
        self.propose_lesson("uncertain", "inconclusive")
        self.assertEqual(self.lessons()["uncertain"]["status"], "candidate")
        result = self.call("lesson-decide", "uncertain", "approve", "--reason", "Review", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "review_required")
        self.assertEqual(self.lessons()["uncertain"]["status"], "candidate")
        self.call("lesson-decide", "uncertain", "reject", "--reason", "Effect unproven")
        self.assertEqual(self.lessons()["uncertain"]["status"], "rejected")
        (self.repo / ".newwork/runs/observation").mkdir()
        (self.repo / ".newwork/runs/observation/summary.txt").write_text("Observed pass\n", encoding="utf-8")
        self.propose_lesson("first", "supported", "--contradict", ".newwork/runs/observation/summary.txt")
        candidate = self.lessons()["first"]
        self.assertEqual((candidate["scope"], candidate["status"], candidate["effect"]["status"]),
                         ("project", "candidate", "supported"))
        self.assertEqual(len(candidate["supporting"]), 1)
        self.assertEqual(len(candidate["contradictory"]), 1)
        self.call("lesson-decide", "first", "approve", "--reason", "Contrary observation reviewed")
        self.assertEqual(self.lessons()["first"]["status"], "approved")
        self.call("lesson-decide", "first", "withdraw", "--reason", "Later evidence changed")
        self.assertEqual(self.lessons()["first"]["status"], "withdrawn")
        self.propose_lesson("old")
        self.call("lesson-decide", "old", "approve", "--reason", "Reviewed")
        self.propose_lesson("replacement")
        self.call("lesson-decide", "old", "replace", "--replacement", "replacement", "--reason", "More precise")
        self.assertEqual(self.lessons()["old"]["status"], "replaced")
        self.assertEqual(self.lessons()["old"]["replaced_by"], "replacement")
        self.assertEqual(self.lessons()["replacement"]["status"], "approved")
        self.call("lesson-propose", "run-supported", "Use run evidence", "--source", "retrospective.md",
                  "--support", ".newwork/runs/observation/summary.txt", "--effect", "supported",
                  "--effect-note", "Run output reviewed")
        self.assertEqual(self.lessons()["run-supported"]["status"], "candidate")
        before_rebuild = self.lessons()
        (self.repo / ".newwork/LESSONS.yaml").write_text("{}\n", encoding="utf-8")
        self.call("rebuild")
        self.assertEqual(self.lessons(), before_rebuild)

    def test_project_lesson_stale_references_and_scope_fail_closed(self):
        self.lesson_fixture()
        result = self.call("lesson-propose", "global", "Claim", "--scope", "global",
                           "--source", "retrospective.md", "--support", "README.md",
                           "--effect", "supported", "--effect-note", "Review", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid_input")
        (self.repo / "other.md").write_text("Unrecorded\n", encoding="utf-8")
        result = self.call("lesson-propose", "unrecorded", "Claim", "--source", "retrospective.md",
                           "--support", "other.md", "--effect", "supported", "--effect-note", "Review", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid_evidence")
        self.propose_lesson("stale")
        source = self.repo / "retrospective.md"
        source.write_text("Changed\n", encoding="utf-8")
        result = self.call("lesson-decide", "stale", "approve", "--reason", "Review", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "review_required")
        self.assertEqual(self.lessons()["stale"]["status"], "candidate")
        (self.repo / "README.md").write_text("proof\n", encoding="utf-8")
        (self.repo / ".newwork/runs/contrary").mkdir()
        counterproof = self.repo / ".newwork/runs/contrary/log.txt"
        counterproof.write_text("Counterexample\n", encoding="utf-8")
        self.propose_lesson("stale-contrary", "supported", "--contradict", ".newwork/runs/contrary/log.txt")
        counterproof.write_text("Changed counterexample\n", encoding="utf-8")
        result = self.call("lesson-decide", "stale-contrary", "approve", "--reason", "Review", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "review_required")
        self.assertIn(".newwork/runs/contrary/log.txt", json.loads(self.call("reconcile", ok=False).stdout)["stale_lesson_evidence"])
        self.assertIn("retrospective.md", json.loads(self.call("status").stdout)["stale_lesson_evidence"])
        source.write_text("Keep: verify changes.\n", encoding="utf-8")
        (self.repo / "README.md").write_text("Changed proof\n", encoding="utf-8")
        result = self.call("lesson-decide", "stale", "approve", "--reason", "Review", ok=False)
        self.assertEqual(json.loads(result.stdout)["status"], "review_required")
        self.assertEqual(self.lessons()["stale"]["status"], "candidate")

    def test_project_lesson_same_contract_across_callers(self):
        def caller(name, *command):
            result = subprocess.run([str(self.repo / "run.sh"), "memory", *command], cwd=self.repo,
                                    env={**os.environ, "NEWWORK_TEST_CALLER": name},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            return json.loads(result.stdout)

        caller("codex", "init")
        caller("codex", "start", "lesson-session")
        (self.repo / "retrospective.md").write_text("Keep: verify changes.\n", encoding="utf-8")
        caller("codex", "finding", "proof", "README is proof", "EVIDENCE_FOUND", "--evidence", "README.md")
        caller("codex", "lesson-propose", "shared", "Verify changes", "--source", "retrospective.md",
               "--support", "README.md", "--effect", "supported", "--effect-note", "Reviewed")
        caller("claude", "lesson-decide", "shared", "approve", "--reason", "Human approved")
        self.assertEqual(self.lessons()["shared"]["status"], "approved")
        self.assertNotIn("caller", (self.repo / ".newwork/events.jsonl").read_text(encoding="utf-8"))

    def result(self, task_id="task-1", open_event=None, run_id="run-1", verdict="PASS",
               evidence_path=None, evidence_hash=None, verifier_text="VERDICT: PASS\n"):
        folder = self.repo / ".newwork/runs" / run_id
        folder.mkdir(parents=True, exist_ok=True)
        proof = folder / "verifier.md"
        proof.write_text(verifier_text, encoding="utf-8")
        rel = evidence_path or f".newwork/runs/{run_id}/verifier.md"
        proof_hash = hashlib.sha256(proof.read_bytes()).hexdigest()
        result = {"schema_version": 1, "run_id": run_id, "task_id": task_id,
                  "task_open_event": open_event if open_event is not None else self.state()["open_tasks"][task_id]["open_event"],
                  "verdict": verdict, "evidence": [{"path": rel,
                  "sha256": evidence_hash or proof_hash}],
                  "verifier_artifact": {"path": f".newwork/runs/{run_id}/verifier.md", "sha256": proof_hash}}
        path = folder / "verification-result.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        return path.relative_to(self.repo).as_posix()

    def assert_close_rejected(self, expected, path):
        before = self.state()["event_seq"]
        response = self.call("close-task", "task-1", "--result", path, ok=False)
        self.assertEqual(json.loads(response.stdout)["status"], expected)
        self.assertIn("task-1", self.state()["open_tasks"])
        self.assertEqual(self.state()["event_seq"], before)

    def test_verifier_artifact_consistency_gate(self):
        self.call("init")
        self.call("start", "session-1")
        self.call("open-task", "task-1", "Verify")
        self.assert_close_rejected("conflict", self.result(run_id="json-pass-verifier-fail",
                                                           verifier_text="Details\nVERDICT: FAIL\n"))
        self.assert_close_rejected("conflict", self.result(run_id="json-fail-verifier-pass", verdict="FAIL"))
        tampered = self.result(run_id="tampered-hash")
        verifier = self.repo / ".newwork/runs/tampered-hash/verifier.md"
        verifier.write_text("Details changed\nVERDICT: PASS\n", encoding="utf-8")
        body = json.loads((self.repo / tampered).read_text(encoding="utf-8"))
        body["evidence"][0]["sha256"] = hashlib.sha256(verifier.read_bytes()).hexdigest()
        (self.repo / tampered).write_text(json.dumps(body), encoding="utf-8")
        self.assert_close_rejected("invalid_evidence", tampered)
        other = self.result(run_id="other-run")
        wrong_run = self.result(run_id="wrong-run")
        body = json.loads((self.repo / wrong_run).read_text(encoding="utf-8"))
        body["verifier_artifact"] = json.loads((self.repo / other).read_text(encoding="utf-8"))["verifier_artifact"]
        (self.repo / wrong_run).write_text(json.dumps(body), encoding="utf-8")
        self.assert_close_rejected("invalid_evidence", wrong_run)
        escaped = self.result(run_id="escaped")
        body = json.loads((self.repo / escaped).read_text(encoding="utf-8"))
        body["verifier_artifact"]["path"] = ".newwork/runs/escaped/../../DECISIONS.md"
        (self.repo / escaped).write_text(json.dumps(body), encoding="utf-8")
        self.assert_close_rejected("invalid_evidence", escaped)
        symlinked = self.result(run_id="symlinked")
        alias = self.repo / ".newwork/runs/symlinked/alias.md"
        alias.symlink_to(self.repo / ".newwork/runs/other-run/verifier.md")
        body = json.loads((self.repo / symlinked).read_text(encoding="utf-8"))
        body["verifier_artifact"]["path"] = ".newwork/runs/symlinked/alias.md"
        (self.repo / symlinked).write_text(json.dumps(body), encoding="utf-8")
        self.assert_close_rejected("invalid_evidence", symlinked)
        omitted = self.result(run_id="omitted-verifier")
        body = json.loads((self.repo / omitted).read_text(encoding="utf-8"))
        body.pop("verifier_artifact")
        (self.repo / omitted).write_text(json.dumps(body), encoding="utf-8")
        self.assert_close_rejected("invalid_evidence", omitted)
        missing = self.result(run_id="missing-verifier")
        body = json.loads((self.repo / missing).read_text(encoding="utf-8"))
        separate_proof = self.repo / ".newwork/runs/missing-verifier/reviewer.md"
        separate_proof.write_text("Review passed\n", encoding="utf-8")
        body["evidence"] = [{"path": ".newwork/runs/missing-verifier/reviewer.md",
                             "sha256": hashlib.sha256(separate_proof.read_bytes()).hexdigest()}]
        (self.repo / missing).write_text(json.dumps(body), encoding="utf-8")
        (self.repo / ".newwork/runs/missing-verifier/verifier.md").unlink()
        self.assert_close_rejected("invalid_evidence", missing)
        good = self.result(run_id="valid-verifier", verifier_text="Details\n\nVERDICT: PASS\n\n")
        self.call("close-task", "task-1", "--result", good)

    def test_completion_gate_rejections_preserve_open_task(self):
        self.call("init")
        self.call("start", "session-1")
        opened = self.call("open-task", "task-1", "Verify").stdout
        seq = json.loads(opened)["event_seq"]
        self.assertEqual(self.state()["open_tasks"]["task-1"]["open_event"], seq)
        self.assert_close_rejected("invalid_evidence", ".newwork/runs/missing/verification-result.json")
        self.assert_close_rejected("conflict", self.result(run_id="fail", verdict="FAIL"))
        path = self.result(run_id="missing-proof")
        (self.repo / ".newwork/runs/missing-proof/verifier.md").unlink()
        self.assert_close_rejected("invalid_evidence", path)
        self.assert_close_rejected("invalid_evidence", self.result(run_id="bad-hash", evidence_hash="0" * 64))
        self.assert_close_rejected("conflict", self.result(task_id="other", open_event=seq, run_id="wrong-task"))
        self.assert_close_rejected("conflict", self.result(run_id="wrong-generation", open_event=seq - 1))
        self.assert_close_rejected("invalid_evidence", "../outside/verification-result.json")
        self.assert_close_rejected("invalid_evidence", self.result(run_id="outside-proof", evidence_path="../outside"))
        outside = self.repo / "result.json"
        outside.write_text("{}", encoding="utf-8")
        self.assert_close_rejected("invalid_evidence", "result.json")
        good = self.result(run_id="good")
        closed = self.call("close-task", "task-1", "--result", good)
        self.assertEqual(json.loads(closed.stdout)["status"], "ok")
        self.assertNotIn("task-1", self.state()["open_tasks"])
        self.call("rebuild")
        self.assertNotIn("task-1", self.state()["open_tasks"])

    def test_completion_gate_rejects_old_and_consumed_run(self):
        self.call("init")
        self.call("start", "session-1")
        self.call("open-task", "task-1", "First")
        old = self.result(run_id="old")
        self.call("close-task", "task-1", "--result", old)
        self.call("open-task", "task-1", "Second")
        self.assert_close_rejected("conflict", old)
        rewritten = json.loads((self.repo / old).read_text(encoding="utf-8"))
        rewritten["task_open_event"] = self.state()["open_tasks"]["task-1"]["open_event"]
        (self.repo / old).write_text(json.dumps(rewritten), encoding="utf-8")
        self.assert_close_rejected("conflict", old)

    def test_completion_gate_survives_crash_and_is_caller_independent(self):
        def caller(name, *command):
            result = subprocess.run([str(self.repo / "run.sh"), "memory", *command], cwd=self.repo,
                                    env={**os.environ, "NEWWORK_TEST_CALLER": name},
                                    capture_output=True, text=True)
            return result.returncode, json.loads(result.stdout)

        self.assertEqual(caller("codex", "init")[0], 0)
        self.assertEqual(caller("codex", "start", "session-1")[0], 0)
        self.assertEqual(caller("codex", "open-task", "task-1", "Crash recovery")[0], 0)
        generation = self.state()["open_tasks"]["task-1"]["open_event"]
        self.assertEqual(caller("codex", "interrupt", "session-1", "crash")[0], 0)
        self.assertEqual(caller("claude", "start", "session-2")[0], 0)
        self.assertEqual(self.state()["open_tasks"]["task-1"]["open_event"], generation)
        proof = self.result(run_id="recovered")
        rc, body = caller("claude", "close-task", "task-1", "--result", proof)
        self.assertEqual((rc, body["status"]), (0, "ok"))
        self.assertNotIn("caller", (self.repo / ".newwork/events.jsonl").read_text(encoding="utf-8"))
        self.assertNotIn("caller", json.dumps(self.state()))

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def checkpoint_ready(self):
        self.call("init")
        (self.repo / ".newwork/.gitignore").write_text(".lock\n", encoding="utf-8")
        (self.repo / "README.md").write_text("approved change\n", encoding="utf-8")
        parent = self.git("rev-parse", "HEAD")
        self.call("accept-git", "Reviewed checkpoint files")
        return parent

    def assert_reconcile_status(self, expected):
        result = self.call("reconcile", ok=expected == "ok")
        self.assertEqual(json.loads(result.stdout)["status"], expected)
        self.assertEqual(result.returncode, 0 if expected == "ok" else 11)

    def test_session_rebuild_confirmation_and_evidence(self):
        self.call("init")
        self.call("start", "session-1")
        self.call("open-task", "task-1", "Inspect proof")
        self.call("request-confirmation", "choice-1", "Approve change?")
        self.call("finding", "fact-1", "README says proof", "EVIDENCE_FOUND", "--evidence", "README.md")
        self.assertEqual(self.state()["pending_confirmations"]["choice-1"]["question"], "Approve change?")
        findings = json.loads((self.repo / ".newwork/FINDINGS.yaml").read_text(encoding="utf-8"))
        evidence = findings["items"]["fact-1"]["evidence"][0]
        self.assertEqual(evidence["sha256"], hashlib.sha256(b"proof\n").hexdigest())
        self.call("end", "session-1", "--next-start", "Review choice-1")
        self.assertIsNone(self.state()["active_session"])
        self.assertEqual(self.state()["next_start"], "Review choice-1")
        self.call("start", "session-2")
        self.call("resolve-confirmation", "choice-1", "Approved")
        self.call("close-task", "task-1", "--result", self.result())
        self.call("end", "session-2", "--next-start", "Continue")
        self.assertFalse(self.state()["pending_confirmations"])
        self.call("reconcile")
        before = self.state()
        (self.repo / ".newwork/STATE.yaml").write_text("{}\n", encoding="utf-8")
        self.call("reconcile", ok=False)
        self.call("rebuild")
        self.assertEqual(before, self.state())
        self.call("reconcile")
        (self.repo / "README.md").write_text("changed proof\n", encoding="utf-8")
        result = self.call("reconcile", ok=False)
        self.assertIn('"stale_evidence":["README.md"]', result.stdout)

    def test_invalid_evidence_and_corrupt_ledger_fail_closed(self):
        self.call("init")
        self.call("start", "session-1")
        self.call("finding", "fact", "No proof", "CONFIRMED", ok=False)
        self.call("finding", "fact", "Outside", "EVIDENCE_FOUND", "--evidence", "../outside", ok=False)
        ledger = self.repo / ".newwork/events.jsonl"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write('{"seq":999}\n')
        self.call("rebuild", ok=False)

    def test_git_drift_and_existing_files(self):
        (self.repo / ".newwork").mkdir()
        (self.repo / ".newwork/STATE.yaml").write_text("personal\n", encoding="utf-8")
        self.call("init", ok=False)
        self.assertEqual((self.repo / ".newwork/STATE.yaml").read_text(), "personal\n")
        (self.repo / ".newwork/STATE.yaml").unlink()
        self.call("init")
        self.call("start", "session-1")
        self.call("end", "session-1", "--next-start", "Next")
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        self.call("reconcile", ok=False)
        self.call("start", "session-2", ok=False)
        self.call("accept-git", "Reviewed README edit")
        self.call("reconcile")
        self.call("start", "session-2")

    def test_common_idempotency_and_crash_interrupt(self):
        self.call("init")
        for command in (("start", "s1"),
                        ("finding", "f1", "claim", "EVIDENCE_FOUND", "--evidence", "README.md")):
            first = json.loads(self.call(*command).stdout)
            again = json.loads(self.call(*command).stdout)
            self.assertEqual(again["status"], "ok")
            self.assertTrue(again["replayed"])
            self.assertEqual(first["event_seq"], again["event_seq"])
        self.assertEqual(self.state()["active_session"], "s1")
        for command in (("interrupt", "s1", "agent crash"), ("start", "s2"),
                        ("end", "s2", "--next-start", "Next")):
            first = json.loads(self.call(*command).stdout)
            again = json.loads(self.call(*command).stdout)
            self.assertTrue(again["replayed"])
            self.assertEqual(first["event_seq"], again["event_seq"])
        stale = self.call("interrupt", "s1", "agent crash", ok=False)
        self.assertEqual((stale.returncode, json.loads(stale.stdout)["status"]), (10, "conflict"))
        self.assertEqual(json.loads(self.call("resume", "s1", ok=False).stdout)["status"], "invalid_input")

    def test_stale_end_replay_after_next_session_starts(self):
        self.call("init")
        self.call("start", "s1")
        self.call("end", "s1", "--next-start", "Next")
        self.assertTrue(json.loads(self.call("end", "s1", "--next-start", "Next").stdout)["replayed"])
        self.call("start", "s2")
        stale = self.call("end", "s1", "--next-start", "Next", ok=False)
        self.assertEqual((stale.returncode, json.loads(stale.stdout)["status"]), (10, "conflict"))
        self.assertEqual(self.state()["active_session"], "s2")

    def test_end_review_keeps_active_until_head_and_evidence_accepted(self):
        self.call("init")
        self.call("start", "s1")
        self.call("finding", "f1", "claim", "EVIDENCE_FOUND", "--evidence", "README.md")
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "changed"], check=True)
        result = self.call("end", "s1", "--next-start", "Next", ok=False)
        self.assertEqual(result.returncode, 11)
        self.assertEqual(json.loads(result.stdout)["status"], "review_required")
        self.assertEqual(self.state()["active_session"], "s1")
        self.call("accept-git", "Reviewed new HEAD")
        result = self.call("end", "s1", "--next-start", "Next", ok=False)
        self.assertEqual(json.loads(result.stdout)["stale_evidence"], ["README.md"])
        self.call("finding", "f1", "claim", "EVIDENCE_FOUND", "--evidence", "README.md")
        self.call("end", "s1", "--next-start", "Next")
        self.assertIsNone(self.state()["active_session"])

    def test_status_codes_and_backend_independent_contract(self):
        self.call("init")
        self.call("start", "same-session")  # Codex and Claude both use this command.
        self.assertEqual(json.loads(self.call("start", "other", ok=False).stdout)["status"], "conflict")
        invalid = self.call("finding", "f", "claim", "CONFIRMED", ok=False)
        self.assertEqual((invalid.returncode, json.loads(invalid.stdout)["status"]), (13, "invalid_evidence"))
        self.assertEqual(json.loads(self.call("status").stdout)["active_session"], "same-session")
        ledger = self.repo / ".newwork/events.jsonl"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write("broken\n")
        corrupt = self.call("status", ok=False)
        self.assertEqual((corrupt.returncode, json.loads(corrupt.stdout)["status"]), (12, "ledger_corrupt"))

    def test_status_uses_read_only_shared_lock_without_writing_memory(self):
        self.call("init")
        base = self.repo / ".newwork"
        lock = base / ".lock"
        observed = {path.name: path.read_bytes() for path in base.iterdir() if path.is_file()}
        lock.chmod(0o444)
        try:
            result = json.loads(self.call("status").stdout)
        finally:
            lock.chmod(0o644)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(observed, {path.name: path.read_bytes() for path in base.iterdir() if path.is_file()})

    def test_uninitialized_status_does_not_create_memory_files(self):
        result = self.call("status", ok=False)
        self.assertEqual((result.returncode, json.loads(result.stdout)["status"]), (2, "invalid_input"))
        self.assertFalse((self.repo / ".newwork").exists())

    def test_status_waits_for_exclusive_writer_lock(self):
        self.call("init")
        lock = self.repo / ".newwork/.lock"
        with lock.open("a+b") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            process = subprocess.Popen([sys.executable, str(SCRIPT), "--root", str(self.repo), "status"],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                process.communicate(timeout=0.2)
                blocked = False
            except subprocess.TimeoutExpired:
                blocked = True
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
            stdout, stderr = process.communicate(timeout=2)
        self.assertTrue(blocked, "status bypassed the writer lock")
        self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(json.loads(stdout)["status"], "ok")

    def test_mutation_waits_for_shared_status_lock(self):
        self.call("init")
        lock = self.repo / ".newwork/.lock"
        with lock.open("rb") as handle:
            fcntl.flock(handle, fcntl.LOCK_SH)
            process = subprocess.Popen([sys.executable, str(SCRIPT), "--root", str(self.repo), "start", "blocked-writer"],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                process.communicate(timeout=0.2)
                blocked = False
            except subprocess.TimeoutExpired:
                blocked = True
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
            stdout, stderr = process.communicate(timeout=2)
        self.assertTrue(blocked, "mutation no longer requires the exclusive lock")
        self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(json.loads(stdout)["active_session"], "blocked-writer")

    def test_ordinary_errors_are_not_ledger_corruption(self):
        self.call("init")
        self.call("start", "s1")
        cases = (("request-confirmation", "q1", "Question?"),
                 ("open-task", "t1", "Task"))
        for command in cases:
            self.call(*command)
            result = self.call(*command, ok=False)
            self.assertEqual((result.returncode, json.loads(result.stdout)["status"]), (10, "conflict"))
        result = self.call("close-task", "missing", ok=False)
        self.assertEqual((result.returncode, json.loads(result.stdout)["status"]), (2, "invalid_input"))
        result = self.call("finding", "f", "claim", "CONFIRMED", "--evidence", "../missing", ok=False)
        self.assertEqual((result.returncode, json.loads(result.stdout)["status"]), (13, "invalid_evidence"))

    def test_codex_claude_share_run_sh_contract(self):
        def caller(name, *command):
            return subprocess.run([str(self.repo / "run.sh"), "memory", *command], cwd=self.repo,
                                  env={**os.environ, "NEWWORK_TEST_CALLER": name},
                                  capture_output=True, text=True)

        self.assertEqual(caller("codex", "init").returncode, 0)
        started = caller("codex", "start", "shared")
        self.assertEqual(started.returncode, 0)
        codex_status = caller("codex", "status")
        claude_status = caller("claude", "status")
        self.assertEqual((codex_status.returncode, json.loads(codex_status.stdout)),
                         (claude_status.returncode, json.loads(claude_status.stdout)))
        found = caller("claude", "finding", "fact", "proof", "EVIDENCE_FOUND", "--evidence", "README.md")
        self.assertEqual((found.returncode, json.loads(found.stdout)["status"]), (0, "ok"))
        ended = caller("claude", "end", "shared", "--next-start", "Next")
        self.assertEqual((ended.returncode, json.loads(ended.stdout)["status"]), (0, "ok"))
        ledger = (self.repo / ".newwork/events.jsonl").read_text(encoding="utf-8")
        state = self.state()
        self.assertNotIn("caller", ledger + json.dumps(state))
        self.assertEqual(state["active_session"], None)
        self.assertEqual({p.name for p in (self.repo / ".newwork").iterdir()},
                         {".lock", "DECISIONS.md", "events.jsonl", "STATE.yaml", "FINDINGS.yaml",
                          "LESSONS.yaml", "incidents", "runs"})

    def test_checkpoint_accepted_tree_direct_child_and_internal_record(self):
        parent = self.checkpoint_ready()
        self.git("add", "-A")
        self.git("commit", "-qm", "checkpoint")
        self.assertEqual(self.git("rev-parse", "HEAD^"), parent)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assert_reconcile_status("ok")
        self.assertEqual(json.loads(self.call("status").stdout)["git_drift"], False)
        self.assertEqual(self.git("show", "HEAD:.newwork/events.jsonl"),
                         (self.repo / ".newwork/events.jsonl").read_text(encoding="utf-8").strip())
        self.call("start", "after-checkpoint")

    def test_checkpoint_during_active_session_allows_end(self):
        self.call("init")
        self.call("start", "active")
        (self.repo / ".newwork/.gitignore").write_text(".lock\n", encoding="utf-8")
        (self.repo / "README.md").write_text("reviewed in session\n", encoding="utf-8")
        self.call("accept-git", "Reviewed active session changes")
        self.git("add", "-A")
        self.git("commit", "-qm", "checkpoint in session")
        self.call("end", "active", "--next-start", "Next")
        self.assertIsNone(self.state()["active_session"])

    def test_checkpoint_rejects_extra_edit(self):
        self.checkpoint_ready()
        (self.repo / "README.md").write_text("unapproved edit\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "unapproved")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_rejects_unapproved_extra_file(self):
        self.checkpoint_ready()
        (self.repo / "extra.txt").write_text("unapproved\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "extra file")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_rejects_partial_commit(self):
        self.call("init")
        (self.repo / ".newwork/.gitignore").write_text(".lock\n", encoding="utf-8")
        (self.repo / "README.md").write_text("approved\n", encoding="utf-8")
        (self.repo / "second.txt").write_text("approved too\n", encoding="utf-8")
        self.call("accept-git", "Reviewed both files")
        self.git("add", "README.md")
        self.git("commit", "-qm", "partial")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_rejects_branch_change_and_unrelated_commit(self):
        self.checkpoint_ready()
        self.git("switch", "-q", "-c", "unexpected")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_rejects_unrelated_or_multi_commit(self):
        self.checkpoint_ready()
        self.git("commit", "--allow-empty", "-qm", "unrelated")
        self.git("add", "-A")
        self.git("commit", "-qm", "approved files later")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_rejects_unrelated_parent_with_matching_files(self):
        self.checkpoint_ready()
        self.git("add", "-A")
        tree = self.git("write-tree")
        unrelated = self.git("commit-tree", tree, "-m", "unrelated root")
        branch = self.git("branch", "--show-current")
        self.git("update-ref", f"refs/heads/{branch}", unrelated)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_rejects_new_dirty_worktree_and_human_memory_edit(self):
        self.checkpoint_ready()
        self.git("add", "-A")
        self.git("commit", "-qm", "checkpoint")
        (self.repo / "README.md").write_text("post-commit change\n", encoding="utf-8")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_rejects_unapproved_human_memory_edit(self):
        self.checkpoint_ready()
        (self.repo / ".newwork/DECISIONS.md").write_text("# Unapproved decision\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "memory change")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_accepts_reviewed_human_memory_edit(self):
        self.call("init")
        (self.repo / ".newwork/.gitignore").write_text(".lock\n", encoding="utf-8")
        (self.repo / ".newwork/DECISIONS.md").write_text("# Reviewed decision\n", encoding="utf-8")
        self.call("accept-git", "Reviewed decision")
        self.git("add", "-A")
        self.git("commit", "-qm", "reviewed memory file")
        self.assert_reconcile_status("ok")

    def test_legacy_acceptance_without_identity_is_not_retroactive(self):
        self.checkpoint_ready()
        ledger = self.repo / ".newwork/events.jsonl"
        lines = ledger.read_text(encoding="utf-8").splitlines()
        last = json.loads(lines[-1])
        last["data"].pop("accepted_change_identity")
        last.pop("hash")
        last["hash"] = hashlib.sha256(json.dumps(last, ensure_ascii=False, sort_keys=True,
                                                  separators=(",", ":")).encode("utf-8")).hexdigest()
        lines[-1] = json.dumps(last, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "legacy acceptance")
        self.assert_reconcile_status("review_required")

    def test_checkpoint_without_acceptance_remains_review_required(self):
        self.call("init")
        self.call("start", "baseline")
        self.call("end", "baseline", "--next-start", "Next")
        (self.repo / ".newwork/.gitignore").write_text(".lock\n", encoding="utf-8")
        (self.repo / "README.md").write_text("not reviewed\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "unaccepted")
        self.assert_reconcile_status("review_required")


if __name__ == "__main__":
    unittest.main(verbosity=2)
