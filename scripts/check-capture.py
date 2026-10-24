"""Assert native capture policy without writing events, spool, or server data."""

import json
from pathlib import Path
import subprocess
import tempfile
import tomllib


def check(cwd, tool_input=None):
    payload = {"cwd": str(cwd)}
    if tool_input:
        payload.update(tool_name="Read", tool_input=tool_input)
    result = subprocess.run(
        ["ai-memory", "hook", "--agent", "codex", "--event", "pre-tool-use",
         "--check-capture"], input=json.dumps(payload), text=True,
        capture_output=True, check=True, timeout=10,
    )
    return json.loads(result.stdout)


root = Path(__file__).resolve().parents[1]
marker_path = root / ".ai-memory.toml"
if not marker_path.is_file():
    raise SystemExit("Memória não configurada: siga docs/setup.md para criar o marcador local.")
marker = tomllib.loads(marker_path.read_text())
if any(not isinstance(marker.get(key), str) or not marker[key].strip()
       for key in ("workspace", "project")):
    raise SystemExit("O marcador local precisa declarar workspace e project não vazios.")
policy = check(root)
assert policy["capture_mode"] == "allowlist"
assert policy["admits_capture"]
assert policy["scope"]["workspace"] == marker["workspace"]
assert policy["scope"]["project"] == marker["project"]
with tempfile.TemporaryDirectory(prefix="memory-unmarked-") as temp:
    assert not check(temp)["admits_capture"]
for relative in [".env", ".env.local", "nested/.env", "secrets/test.txt", ".setup/backup", "docs/adr/test.md"]:
    excluded = check(root, {"file_path": str(root / relative)})
    assert not excluded["policy_admits_capture"], f"Not excluded: {relative}"
    assert excluded["disposition"] == "drop"
assert check(root, {"file_path": str(root / "docs/quality.md")})["policy_admits_capture"]
print("PASS: marked repository, explicit scope, unmarked directory, six exclusions, public documentation")
