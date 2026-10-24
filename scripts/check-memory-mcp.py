"""Read-only MCP smoke test; no LLM calls, memory writes, or credential output."""

import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import time
import tomllib


def main():
    parser = argparse.ArgumentParser(description="Verifica o bridge MCP instalado, sem escrita de memórias.")
    parser.add_argument("--status-only", action="store_true",
                        help="Valida conexão, catálogo e status global antes de registrar o projeto")
    args = parser.parse_args()
    marker_path = Path(__file__).resolve().parents[1] / ".ai-memory.toml"
    if not marker_path.is_file():
        raise SystemExit("Memória não configurada: siga docs/setup.md para criar o marcador local.")
    marker = tomllib.loads(marker_path.read_text())
    if any(not isinstance(marker.get(key), str) or not marker[key].strip()
           for key in ("workspace", "project")):
        raise SystemExit("O marcador local precisa declarar workspace e project não vazios.")
    process = subprocess.Popen(
        ["ai-memory", "mcp-bridge", "--no-session-id"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, bufsize=0,
    )
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    pending = b""

    def request(method, params, request_id):
        nonlocal pending
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        if request_id is not None:
            payload["id"] = request_id
        process.stdin.write((json.dumps(payload) + "\n").encode())
        if request_id is None:
            return None
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if b"\n" not in pending:
                if not selector.select(max(0, deadline - time.monotonic())):
                    break
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError("MCP bridge exited before response")
                pending += chunk
                continue
            line, pending = pending.split(b"\n", 1)
            response = json.loads(line)
            if response.get("id") == request_id:
                assert "error" not in response, f"MCP rejected {method}"
                result = response["result"]
                assert not result.get("isError"), f"Tool failed: {params.get('name')}"
                return result
        raise TimeoutError(f"No MCP response for {method}")

    try:
        initialized = request("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "base-readonly-check", "version": "1"},
        }, 1)
        request("notifications/initialized", {}, None)
        names = {tool["name"] for tool in request("tools/list", {}, 2)["tools"]}
        assert {"memory_status", "memory_query"} <= names
        if args.status_only:
            # A new scope does not exist until the first real lifecycle event.
            try:
                subprocess.run(["ai-memory", "status", "--json"], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            except (OSError, subprocess.SubprocessError):
                raise SystemExit("Status do serviço indisponível. Confira ai-memory status --json "
                                 "e as permissões de rede/sandbox.") from None
        else:
            # Static Codex clients must supply the marker's exact project scope.
            request("tools/call", {"name": "memory_status", "arguments": {
                "workspace": marker["workspace"], "project": marker["project"],
            }}, 3)
            request("tools/call", {"name": "memory_query", "arguments": {
                "workspace": marker["workspace"], "project": marker["project"],
                "query": "development environment validation", "limit": 1,
            }}, 4)
        print(json.dumps({"initialize": "pass", "server": initialized["serverInfo"],
                          "tool_count": len(names),
                          "service_status": "pass" if args.status_only else "not_requested",
                          "memory_status": "not_requested" if args.status_only else "pass",
                          "memory_query": "not_requested" if args.status_only else "pass", "writes": 0}))
    finally:
        selector.close()
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
