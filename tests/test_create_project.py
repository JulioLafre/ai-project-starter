"""Generate independent projects without copying the factory's local state."""

import contextlib
import io
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/create-project.py"


class CreateProjectTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Falta o gerador de projetos")
        self.module = runpy.run_path(str(SCRIPT))
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.factory = self.root / "factory"
        self.factory.mkdir()
        self.git(self.factory, "init", "--quiet", "--initial-branch=main", "--template=")
        for name, body in {"README.md": "# Factory\n", ".gitignore": "__pycache__/\n",
                           "AGENTS.md": "# Rules\n", "LICENSE": "License\n",
                           "scripts/setup-project.py": "raise SystemExit(9)\n"}.items():
            path = self.factory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        self.git(self.factory, "add", ".")

    def git(self, directory, *arguments):
        return subprocess.run(["git", "-C", str(directory), *arguments],
                              capture_output=True, text=True, check=True).stdout.strip()

    def create(self, name="my-project", base=None):
        return self.module["create_project"](self.factory, base or self.root / "projects", name)

    def test_creates_named_project_and_independent_git_without_commits_or_remote(self):
        self.git(self.factory, "-c", "user.name=Factory Test", "-c", "user.email=test@example.invalid",
                 "commit", "--quiet", "-m", "Factory history")
        self.git(self.factory, "remote", "add", "origin", "https://example.invalid/factory.git")
        target = self.create()
        self.assertEqual(target, self.root / "projects/my-project")
        self.assertTrue((target / "README.md").read_text().startswith("# my-project\n"))
        self.assertEqual((target / "LICENSE").read_bytes(), (self.factory / "LICENSE").read_bytes())
        self.assertEqual(self.git(target, "symbolic-ref", "--short", "HEAD"), "main")
        self.assertEqual(self.git(target, "remote"), "")
        result = subprocess.run(["git", "-C", str(target), "rev-parse", "--verify", "HEAD"],
                                capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.factory, "symbolic-ref", "--short", "HEAD"), "main")
        self.assertEqual((self.factory / "README.md").read_text(), "# Factory\n")
        self.assertEqual(self.git(self.factory, "remote"), "origin")

    def test_ignores_local_files_even_if_accidentally_tracked(self):
        for name in (".ai-memory.toml", ".env", ".env.private", ".setup/backup", "reports/log",
                     ".agents/config", ".codex/config", "secrets/key", "private.pem", "private.key",
                     "MEMORY.md", "__pycache__/script.pyc"):
            path = self.factory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("LOCAL_DATA")
            self.git(self.factory, "add", "--force", name)
        (self.factory / "untracked.txt").write_text("LOCAL_DATA")
        (self.factory / ".env.example").write_text("PLACEHOLDER=\n")
        self.git(self.factory, "add", ".env.example")
        target = self.create()
        self.assertTrue((target / ".env.example").is_file())
        for path in target.rglob("*"):
            if path.is_file() and ".git" not in path.relative_to(target).parts:
                self.assertNotIn("LOCAL_DATA", path.read_text())

    def test_preserves_existing_destination_and_broken_symlink(self):
        target = self.root / "projects/my-project"
        target.mkdir(parents=True)
        (target / "important.txt").write_text("keep")
        with self.assertRaises(FileExistsError):
            self.create()
        self.assertEqual((target / "important.txt").read_text(), "keep")
        (target.parent / "broken").symlink_to(self.root / "missing")
        with self.assertRaises(FileExistsError):
            self.create("broken")

    def test_rejects_names_and_destinations_inside_factory_before_writing(self):
        for name in ("", "..", "../escape", "/absolute", "two words", "UPPER", "--option"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.create(name)
        with self.assertRaises(ValueError):
            self.create(base=self.factory / "nested")
        alias = self.root / "factory-alias"
        alias.symlink_to(self.factory, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.create(base=alias)
        self.assertFalse((self.factory / "nested").exists())

    def test_rejects_tracked_symlinks_before_creating_destination(self):
        (self.factory / "link").symlink_to(self.factory / "README.md")
        self.git(self.factory, "add", "link")
        with self.assertRaises(ValueError):
            self.create()
        self.assertFalse((self.root / "projects").exists())

    def test_rejects_tracked_files_below_replaced_symlink_directory(self):
        (self.factory / "scripts").rename(self.factory / "redirected")
        (self.factory / "scripts").symlink_to(self.factory / "redirected", target_is_directory=True)
        with self.assertRaises(ValueError):
            self.create()
        self.assertFalse((self.root / "projects").exists())

    def test_git_environment_cannot_redirect_initialization_to_factory(self):
        with patch.dict(os.environ, GIT_DIR=str(self.factory / ".git"),
                        GIT_WORK_TREE=str(self.factory)):
            target = self.create()
        self.assertTrue((target / ".git").is_dir())

    def test_cancellation_does_not_create_project(self):
        main = self.module["main"]
        with patch.dict(main.__globals__, ROOT=self.factory), \
                patch("builtins.input", side_effect=[str(self.root / "projects"), "my-project", "n"]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)
        self.assertFalse((self.root / "projects").exists())

    def test_setup_failure_preserves_generated_project_and_reports_retry(self):
        main = self.module["main"]
        output = io.StringIO()
        with patch.dict(main.__globals__, ROOT=self.factory), \
                patch("builtins.input", side_effect=[str(self.root / "projects"), "my-project", "s", "s"]), \
                contextlib.redirect_stdout(output):
            self.assertNotEqual(main(), 0)
        self.assertTrue((self.root / "projects/my-project/.git").is_dir())
        self.assertIn("setup-project.py", output.getvalue())
        self.assertIn("pendente", output.getvalue())

    def test_setup_cannot_inherit_factory_git_environment(self):
        (self.factory / "scripts/setup-project.py").write_text(
            'import os\nfrom pathlib import Path\n'
            'Path("git-vars.txt").write_text(",".join(k for k in os.environ if k.startswith("GIT_")))\n')
        main = self.module["main"]
        with patch.dict(main.__globals__, ROOT=self.factory), \
                patch("builtins.input", side_effect=[str(self.root / "projects"), "my-project", "s", "s"]), \
                patch.dict(os.environ, GIT_INDEX_FILE=str(self.factory / ".git/index")), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)
        self.assertEqual((self.root / "projects/my-project/git-vars.txt").read_text(), "")


if __name__ == "__main__":
    unittest.main()
