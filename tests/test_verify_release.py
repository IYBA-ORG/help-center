"""Release deployment guards, with no GitHub requests or real releases."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-release.py"
SPEC = importlib.util.spec_from_file_location("verify_release", SCRIPT)
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)
COMMIT = "a" * 40
OTHER_COMMIT = "b" * 40


def published(**changes):
    return {
        "id": 42, "tag_name": "v1.0.0", "draft": False, "prerelease": False,
        "published_at": "2026-11-12T12:00:00Z", **changes,
    }


class ReleasePolicyTests(unittest.TestCase):
    def validate(self, **changes):
        values = {
            "tag": "v1.0.0", "release": published(), "latest": published(),
            "local_sha": COMMIT, "remote_sha": COMMIT, "on_main": True,
        }
        return policy.validate_release(**(values | changes))

    def test_current_stable_release_on_main_is_allowed(self):
        self.assertEqual(self.validate(expected_sha=COMMIT), COMMIT)

    def test_draft_prerelease_and_unpublished_releases_are_rejected(self):
        for metadata in (published(draft=True), published(prerelease=True),
                         published(published_at=None), published(published_at="")):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.validate(release=metadata)

    def test_old_release_rerun_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(latest=published(id=43, tag_name="v1.0.1"))

    def test_recreated_release_with_same_tag_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(latest=published(id=43))

    def test_wrong_api_tag_or_missing_id_is_rejected(self):
        for metadata in (published(tag_name="v0.9.0"), published(id=None)):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.validate(release=metadata)

    def test_moved_tag_and_artifact_commit_mismatch_are_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(remote_sha=OTHER_COMMIT)
        with self.assertRaises(ValueError):
            self.validate(local_sha=OTHER_COMMIT, remote_sha=OTHER_COMMIT, expected_sha=COMMIT)

    def test_commit_outside_main_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(on_main=False)

    def test_only_full_shas_and_stable_semver_tags_are_allowed(self):
        for changes in ({"tag": "v1.0.0-rc.1"}, {"tag": "--all"}, {"tag": "v01.0.0"},
                        {"local_sha": "abc"}, {"remote_sha": None}, {"expected_sha": "main"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.validate(**changes)


class ReleaseCommandTests(unittest.TestCase):
    def invoke(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return policy.main(list(arguments))

    def test_success_writes_verified_sha_for_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "outputs"
            with patch.dict(os.environ, {
                "GITHUB_REPOSITORY": "IYBA-ORG/help-center", "GH_TOKEN": "test-token",
                "GITHUB_OUTPUT": str(output),
            }), patch.object(policy, "gh_api", side_effect=[
                published(), published(), {"sha": COMMIT},
            ]), patch.object(policy, "git_state", return_value=(COMMIT, True)):
                self.assertEqual(self.invoke("--tag", "v1.0.0"), 0)
                self.assertEqual(output.read_text(), f"sha={COMMIT}\n")

    def test_invalid_tag_is_rejected_before_any_external_call(self):
        with patch.object(policy, "gh_api") as api:
            self.assertEqual(self.invoke("--tag=--all"), 1)
            api.assert_not_called()

    def test_missing_release_api_failure_fails_closed(self):
        with patch.dict(os.environ, {
            "GITHUB_REPOSITORY": "IYBA-ORG/help-center", "GH_TOKEN": "test-token",
        }), patch.object(policy, "gh_api", side_effect=subprocess.CalledProcessError(1, ["gh", "api"])):
            self.assertEqual(self.invoke("--tag", "v1.0.0"), 1)


if __name__ == "__main__":
    unittest.main()
