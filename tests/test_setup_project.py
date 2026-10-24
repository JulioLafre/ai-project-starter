"""Project initialization must never overwrite configuration or accept TOML injection."""

from pathlib import Path
import contextlib
import io
import runpy
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/setup-project.py"


class SetupProjectTests(unittest.TestCase):
    def initializer(self):
        self.assertTrue(SCRIPT.is_file(), "O comando único de preparação ainda não existe")
        return runpy.run_path(str(SCRIPT))["create_marker"]

    def test_creates_explicit_scope_and_capture_exclusions(self):
        create_marker = self.initializer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_marker(root, "my-workspace", "my-project")
            marker = tomllib.loads((root / ".ai-memory.toml").read_text())
            self.assertEqual(marker["workspace"], "my-workspace")
            self.assertEqual(marker["project"], "my-project")
            self.assertIn(".env", marker["capture"]["ignore_paths"])
            self.assertIn("docs/adr/**", marker["capture"]["ignore_paths"])

    def test_preserves_existing_marker_byte_for_byte(self):
        create_marker = self.initializer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / ".ai-memory.toml"
            original = b'# custom settings\nworkspace = "existing"\nproject = "keep"\n'
            marker.write_bytes(original)
            with self.assertRaises(FileExistsError):
                create_marker(root, "different", "different")
            self.assertEqual(marker.read_bytes(), original)

    def test_rejects_invalid_scope_before_creating_files(self):
        create_marker = self.initializer()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for invalid in ["", "../other", 'name"\nserver = "other', "two words", "UPPER"]:
                for workspace, project in [(invalid, "valid"), ("valid", invalid)]:
                    with self.subTest(workspace=workspace, project=project):
                        with self.assertRaises(ValueError):
                            create_marker(root, workspace, project)
                        self.assertFalse((root / ".ai-memory.toml").exists())

    def test_embedding_failure_stops_setup_before_mcp_and_preserves_marker(self):
        setup = runpy.run_path(str(SCRIPT))
        main = setup["main"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            setup["create_marker"](root, "personal", "application")
            marker = root / ".ai-memory.toml"
            original = marker.read_bytes()

            def command(args, **kwargs):
                if args[1] == "hook":
                    return subprocess.CompletedProcess(args, 0, stdout='{"capture_mode":"allowlist"}')
                if str(root / "scripts/check-embeddings.py") in args:
                    raise subprocess.CalledProcessError(1, args)
                return subprocess.CompletedProcess(args, 0)

            with patch.dict(main.__globals__, ROOT=root), patch("sys.argv", [str(SCRIPT)]), \
                    patch("shutil.which", return_value="installed"), \
                    patch("subprocess.run", side_effect=command) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    main()
            self.assertEqual(marker.read_bytes(), original)
            self.assertFalse(any("check-memory-mcp.py" in str(call.args[0])
                                 for call in run.call_args_list))

    def test_interactive_setup_suggests_folder_name_and_still_requires_capture_opt_in(self):
        main = runpy.run_path(str(SCRIPT))["main"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "meiproject"
            root.mkdir()
            for consent in ("n", "s"):
                with self.subTest(consent=consent), \
                        patch.dict(main.__globals__, ROOT=root), \
                        patch("sys.argv", [str(SCRIPT)]), \
                        patch("shutil.which", return_value="installed"), \
                        patch("subprocess.run", return_value=subprocess.CompletedProcess(
                            [], 0, stdout='{"capture_mode":"allowlist"}')), \
                        patch("builtins.input", side_effect=["pessoal", "", consent]) as prompt, \
                        contextlib.redirect_stdout(io.StringIO()):
                    if consent == "n":
                        with self.assertRaises(SystemExit):
                            main()
                        self.assertFalse((root / ".ai-memory.toml").exists())
                    else:
                        main()
                        marker = tomllib.loads((root / ".ai-memory.toml").read_text())
                        self.assertEqual((marker["workspace"], marker["project"]), ("pessoal", "meiproject"))
                    self.assertIn("meiproject", prompt.call_args_list[1].args[0])


if __name__ == "__main__":
    unittest.main()
