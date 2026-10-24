"""First-use setup must not query a project that only real hooks can register."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = '''import json, os, sys
if sys.argv[1:] == ["status", "--json"]:
    sys.exit(int(os.environ.get("FAIL_STATUS", "0")))
for line in sys.stdin:
    request = json.loads(line)
    if "id" not in request:
        continue
    response = {"jsonrpc": "2.0", "id": request["id"]}
    if request["method"] == "initialize":
        response["result"] = {"serverInfo": {"name": "test", "version": "1"}}
    elif request["method"] == "tools/list":
        response["result"] = {"tools": [{"name": "memory_status"}, {"name": "memory_query"}]}
    else:
        response["error"] = {"code": -32602, "message": "workspace not found"}
    print(json.dumps(response), flush=True)
'''


class MemoryMcpTests(unittest.TestCase):
    def run_check(self, *arguments, fail_status=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scripts").mkdir()
            script = root / "scripts/check-memory-mcp.py"
            shutil.copyfile(ROOT / "scripts/check-memory-mcp.py", script)
            (root / ".ai-memory.toml").write_text('workspace = "new"\nproject = "new"\n')
            executable = root / "ai-memory"
            executable.write_text(f"#!{sys.executable}\n" + BRIDGE)
            executable.chmod(0o700)
            environment = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                               FAIL_STATUS="1" if fail_status else "0")
            return subprocess.run([sys.executable, str(script), *arguments],
                                  env=environment, capture_output=True, text=True, timeout=10)

    def test_first_use_checks_service_without_querying_unregistered_scope(self):
        result = self.run_check("--status-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["service_status"], "pass")
        self.assertEqual(report["memory_status"], "not_requested")
        self.assertEqual(report["memory_query"], "not_requested")

    def test_first_use_still_fails_when_service_status_is_unavailable(self):
        result = self.run_check("--status-only", fail_status=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('"service_status": "pass"', result.stdout)

    def test_full_check_still_rejects_an_unregistered_scope(self):
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
