#!/usr/bin/env python3
"""Memory Foundation acceptance tests in disposable Git repositories."""

import hashlib
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
        self.call("close-task", "task-1")
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
