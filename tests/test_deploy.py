# tests/test_deploy.py
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import deploy


class TestDeploy(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_deploy_copies_files_and_writes_build_info(self):
        release_dir = deploy.deploy(self.target, "42", "abc1234")

        self.assertTrue((release_dir / "app.py").is_file())
        self.assertTrue((release_dir / "requirements.txt").is_file())
        info = (release_dir / deploy.BUILD_INFO_FILE).read_text("utf-8")
        self.assertIn("build_number=42", info)
        self.assertIn("git_commit=abc1234", info)

    def test_smoke_test_passes_on_deployed_app(self):
        release_dir = deploy.deploy(self.target, "1", "abc1234")
        self.assertEqual(
            deploy.smoke_test(release_dir), deploy.EXPECTED_GREETING
        )

    def test_redeploy_replaces_previous_release(self):
        deploy.deploy(self.target, "1", "aaa")
        release_dir = deploy.deploy(self.target, "2", "bbb")

        info = (release_dir / deploy.BUILD_INFO_FILE).read_text("utf-8")
        self.assertIn("build_number=2", info)

    def test_refuses_to_overwrite_unmanaged_folder(self):
        (self.target / "current").mkdir()
        (self.target / "current" / "important.txt").write_text("keep me")

        with self.assertRaises(RuntimeError):
            deploy.deploy(self.target, "1", "abc1234")
        self.assertTrue((self.target / "current" / "important.txt").exists())

    def test_deploy_dir_inside_project_is_rejected(self):
        inside = str(deploy.PROJECT_ROOT / "build")
        with mock.patch.dict(os.environ, {"DEPLOY_DIR": inside}):
            with self.assertRaises(ValueError):
                deploy.get_deploy_dir()

    def test_deploy_dir_filesystem_root_is_rejected(self):
        root = Path(deploy.PROJECT_ROOT.anchor)
        with mock.patch.dict(os.environ, {"DEPLOY_DIR": str(root)}):
            with self.assertRaises(ValueError):
                deploy.get_deploy_dir()

    def test_default_deploy_dir_is_used_when_unset(self):
        with mock.patch.dict(os.environ, {"DEPLOY_DIR": ""}):
            self.assertEqual(
                deploy.get_deploy_dir(), deploy.DEFAULT_DEPLOY_DIR.resolve()
            )

    def test_main_deploys_and_returns_zero(self):
        env = {"DEPLOY_DIR": str(self.target), "BUILD_NUMBER": "7"}
        with mock.patch.dict(os.environ, env):
            with mock.patch("builtins.print"):
                self.assertEqual(deploy.main(), 0)
        self.assertTrue((self.target / "current" / "app.py").is_file())

    def test_main_returns_one_on_invalid_target(self):
        env = {"DEPLOY_DIR": str(deploy.PROJECT_ROOT)}
        with mock.patch.dict(os.environ, env):
            with mock.patch("builtins.print"):
                self.assertEqual(deploy.main(), 1)


if __name__ == "__main__":
    unittest.main()
