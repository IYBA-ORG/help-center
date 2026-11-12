"""Focused tests for commit policy and PR-range enforcement."""

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-commits.py"
SPEC = importlib.util.spec_from_file_location("validate_commits", SCRIPT)
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


class SubjectTests(unittest.TestCase):
    def test_valid_subjects(self):
        for subject in (
            "docs: add overview", "feat(boatdox): add document navigation",
            "fix!: change article URLs", "chore(help-center)!: reorganize navigation",
            "revert: undo broken navigation", "docs: " + "a" * 94,
        ):
            with self.subTest(subject=subject):
                self.assertEqual(policy.validate_subject(subject), [])

    def test_invalid_subjects(self):
        for subject in (
            "", "Add overview", "Docs: add overview", "feat: ", "feat:add overview",
            "docs(): add overview", "docs(BoatDox): add overview",
            "docs(help_center): add overview", "docs(help--center): add overview",
            "docs: add overview ", " docs: add overview", "docs: " + "a" * 95,
            "Merge branch 'main'", "Revert \"docs: add overview\"",
            "docs: first\nsecond", "docs:  add overview", "docs: add\tcontrols",
        ):
            with self.subTest(subject=subject):
                self.assertTrue(policy.validate_subject(subject))

    def test_message_file_body_does_not_change_subject_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            message = Path(directory) / "message"
            message.write_text("docs: add overview\n\nExplanation.\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(policy.main(["--message-file", str(message)]), 0)

    def test_empty_message_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            message = Path(directory) / "message"
            message.write_text("", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(policy.main(["--message-file", str(message)]), 1)


class GitRangeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.run_git("init", "-q")
        self.run_git("config", "user.email", "test@example.invalid")
        self.run_git("config", "user.name", "Test")
        self.run_git("config", "commit.gpgsign", "false")
        self.base = self.commit("chore: initialize repository")

    def run_git(self, *arguments):
        return subprocess.run(
            ["git", "-C", str(self.repo), *arguments], check=True,
            text=True, capture_output=True, timeout=5,
        ).stdout.strip()

    def commit(self, subject):
        self.run_git("-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "-qm", subject)
        return self.run_git("rev-parse", "HEAD")

    def invoke(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return policy.main(["--repo", str(self.repo), *arguments])

    def test_valid_tip_does_not_hide_invalid_earlier_commit(self):
        self.commit("bad subject")
        head = self.commit("docs: add overview")
        self.assertEqual(self.invoke("--range", f"{self.base}..{head}"), 1)

    def test_base_commit_is_excluded(self):
        base = self.commit("legacy invalid subject")
        head = self.commit("docs: add overview")
        self.assertEqual(self.invoke("--range", f"{base}..{head}"), 0)

    def merge_topic(self, subject="docs: add topic", use_hook=False):
        self.run_git("checkout", "-qb", "topic", self.base)
        self.commit(subject)
        self.run_git("checkout", "-")
        self.commit("docs: update main")
        hook_options = [] if use_hook else ["-c", "core.hooksPath=/dev/null"]
        self.run_git(*hook_options, "merge", "--no-ff", "-m", "Merge branch 'topic'", "topic")
        return self.run_git("rev-parse", "HEAD")

    def install_hook(self):
        scripts = self.repo / "scripts"
        scripts.mkdir()
        shutil.copy2(SCRIPT, scripts / SCRIPT.name)
        hooks = self.repo / ".git" / "hooks"
        shutil.copy2(SCRIPT.parents[1] / ".githooks" / "commit-msg", hooks / "commit-msg")
        (hooks / "commit-msg").chmod(0o755)
        self.run_git("config", "core.hooksPath", str(hooks))

    def test_merge_subject_is_ignored(self):
        head = self.merge_topic()
        subjects = policy.range_subjects(self.repo, f"{self.base}..{head}")
        self.assertEqual(len(subjects), 2)
        self.assertNotIn(head, [sha for sha, _ in subjects])
        self.assertEqual(self.invoke("--range", f"{self.base}..{head}"), 0)

    def test_merge_does_not_hide_invalid_commits_on_its_other_parent(self):
        head = self.merge_topic("bad topic subject")
        self.assertEqual(self.invoke("--range", f"{self.base}..{head}"), 1)

    def test_merge_prefix_does_not_exempt_regular_commit(self):
        head = self.commit("Merge branch 'main'")
        self.assertEqual(self.invoke("--range", f"{self.base}..{head}"), 1)

    def test_merge_only_range_passes_but_pr_title_is_still_checked(self):
        base = self.commit("docs: add overview")
        # Both parents are already reachable from base; only the merge is new.
        head = self.run_git("commit-tree", "HEAD^{tree}", "-p", base, "-p", self.base,
                            "-m", "Combine histories")
        self.assertEqual(policy.range_subjects(self.repo, f"{base}..{head}"), [])
        self.assertEqual(self.invoke("--range", f"{base}..{head}"), 0)
        event = self.repo / "event.json"
        data = {"pull_request": {
            "title": "Merge branch 'topic'", "base": {"sha": base}, "head": {"sha": head},
        }}
        event.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.invoke("--event-file", str(event)), 1)
        data["pull_request"]["title"] = "chore: synchronize histories"
        event.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.invoke("--event-file", str(event)), 0)

    def test_hook_allows_actual_merge(self):
        self.install_hook()
        self.merge_topic(use_hook=True)

    def test_hook_rejects_regular_commit_with_merge_prefix(self):
        self.install_hook()
        result = subprocess.run(
            ["git", "-C", str(self.repo), "commit", "--allow-empty", "-qm", "Merge branch 'main'"],
            text=True, capture_output=True, timeout=5,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid commit message", result.stderr)

    def test_empty_or_ambiguous_ranges_fail_closed(self):
        for revision_range in (f"{self.base}..{self.base}", "main...HEAD", "HEAD", "--all..HEAD"):
            with self.subTest(revision_range=revision_range):
                self.assertEqual(self.invoke("--range=" + revision_range), 1)

    def test_pr_title_is_checked_with_commits(self):
        head = self.commit("docs: add overview")
        event = self.repo / "event.json"
        data = {"pull_request": {"title": "Bad title", "base": {"sha": self.base}, "head": {"sha": head}}}
        event.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.invoke("--event-file", str(event)), 1)
        data["pull_request"]["title"] = "docs: add overview"
        event.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.invoke("--event-file", str(event)), 0)

    def test_untrusted_event_revision_cannot_be_a_git_option(self):
        event = self.repo / "event.json"
        event.write_text(json.dumps({"pull_request": {
            "title": "docs: add overview", "base": {"sha": "--all"}, "head": {"sha": self.base},
        }}), encoding="utf-8")
        self.assertEqual(self.invoke("--event-file", str(event)), 1)


if __name__ == "__main__":
    unittest.main()
