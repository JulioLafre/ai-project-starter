"""Offline checks for the files a Git clone or repository template will carry."""

import ast
import json
from pathlib import Path
import re
import subprocess
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".toml", ".json", ".template"}


def export_files():
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return [Path(name) for name in result.stdout.split("\0") if name]


class TemplateTests(unittest.TestCase):
    def test_local_state_is_not_exported(self):
        for relative in export_files():
            with self.subTest(file=str(relative)):
                self.assertNotEqual(relative.name, ".ai-memory.toml")
                self.assertNotIn(relative.parts[0], {".setup", "reports", ".agents", ".codex"})
                self.assertNotIn(relative.name, {"MEMORY.md", ".env"})
                self.assertNotEqual(relative.suffix, ".pyc")

    def test_reusable_files_have_no_home_directory(self):
        for relative in export_files():
            if relative.parts[0] == "tests" or relative.suffix not in TEXT_SUFFIXES:
                continue
            with self.subTest(file=str(relative)):
                self.assertNotIn(str(Path.home()) + "/", (ROOT / relative).read_text())

    def test_syntax_and_whitespace(self):
        for relative in export_files():
            if relative.suffix not in TEXT_SUFFIXES and relative.name != ".gitignore":
                continue
            with self.subTest(file=str(relative)):
                text = (ROOT / relative).read_text()
                self.assertTrue(text.endswith("\n"))
                self.assertTrue(all(line == line.rstrip() for line in text.splitlines()))
                if relative.suffix == ".py":
                    ast.parse(text, filename=str(relative))
                if relative.suffix == ".toml" or relative.name.endswith(".toml.example"):
                    tomllib.loads(text)
                if relative.suffix == ".json":
                    json.loads(text)

    def test_markdown_links_exist_in_export(self):
        exported = set(export_files())
        for relative in exported:
            if relative.suffix != ".md":
                continue
            for target in re.findall(r"\]\(([^)]+)\)", (ROOT / relative).read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (ROOT / relative.parent / target.split("#")[0]).resolve()
                with self.subTest(file=str(relative), target=target):
                    self.assertTrue(resolved.is_relative_to(ROOT))
                    local = resolved.relative_to(ROOT)
                    self.assertTrue(local in exported or any(local in p.parents for p in exported))


if __name__ == "__main__":
    unittest.main()
