"""Project initialization must never overwrite configuration or accept TOML injection."""

from pathlib import Path
import runpy
import tempfile
import tomllib
import unittest


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


if __name__ == "__main__":
    unittest.main()
