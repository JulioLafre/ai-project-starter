"""Prepare this checkout using installed tools; never install or replace configuration."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
IGNORE_PATHS = [".env", ".env.*", "**/.env", "**/.env.*", ".setup/**",
                "secrets/**", "**/*.pem", "**/*.key", "docs/adr/**"]


def create_marker(root, workspace, project):
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name)
           for name in (workspace, project)):
        raise ValueError("Use nomes em minúsculas com letras, números, ponto, hífen ou underscore.")
    content = (f'workspace = "{workspace}"\nproject = "{project}"\n\n[capture]\n'
               f'ignore_paths = {json.dumps(IGNORE_PATHS)}\n')
    with (root / ".ai-memory.toml").open("x", encoding="utf-8") as marker:
        marker.write(content)


def main():
    parser = argparse.ArgumentParser(description="Prepara este projeto com as integrações já instaladas.")
    parser.add_argument("--workspace", help="Workspace de memória escolhido para este projeto")
    parser.add_argument("--project", help="Identificador exclusivo do projeto na memória")
    args = parser.parse_args()
    if bool(args.workspace) != bool(args.project):
        parser.error("Informe --workspace e --project juntos, ou omita ambos para usar o assistente.")

    missing = [name for name in ("git", "codex", "ai-memory") if not shutil.which(name)]
    if missing:
        raise SystemExit("Pré-requisitos ausentes: " + ", ".join(missing) +
                         ". Prepare a máquina conforme docs/setup.md; nada foi instalado ou criado.")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                   cwd=ROOT, check=True)
    policy = subprocess.run(
        ["ai-memory", "hook", "--agent", "codex", "--event", "pre-tool-use", "--check-capture"],
        input=json.dumps({"cwd": str(ROOT)}), text=True, capture_output=True, check=True, timeout=10,
    )
    if json.loads(policy.stdout)["capture_mode"] != "allowlist":
        raise SystemExit("A máquina precisa de captura allowlist; revise docs/setup.md. Configuração preservada.")

    path = ROOT / ".ai-memory.toml"
    if path.exists():
        marker = tomllib.loads(path.read_text())
        if args.workspace and (marker.get("workspace"), marker.get("project")) != (args.workspace, args.project):
            raise SystemExit("O marcador existente usa outro escopo. Nenhum valor foi substituído.")
        print("Marcador local existente preservado.", flush=True)
    else:
        workspace, project = args.workspace, args.project
        if workspace is None:
            print("O marcador autoriza captura neste repositório. Escolha um escopo próprio; não cole segredos.")
            workspace = input("Workspace: ").strip()
            project = input(f"Projeto [{ROOT.name}]: ").strip() or ROOT.name
            if input("Ativar captura neste projeto? [s/N]: ").strip().lower() != "s":
                raise SystemExit("Preparação cancelada; marcador não criado.")
        create_marker(ROOT, workspace, project)
        print("Marcador criado com escopo explícito e exclusões de captura.", flush=True)

    subprocess.run([sys.executable, str(ROOT / "scripts/check-capture.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/check-embeddings.py")], cwd=ROOT, check=True)
    # A first real agent session registers the scope; do not fabricate one for setup.
    subprocess.run([sys.executable, str(ROOT / "scripts/check-memory-mcp.py"), "--status-only"],
                   cwd=ROOT, check=True)
    print("Projeto preparado: base, política de captura e status do bridge AI Memory passaram nos checks.")
    print("A busca no escopo do projeto fica pendente até a primeira sessão real do agente.")
    print("Se o diagnóstico MiniLM mostrou pending, repita scripts/check-embeddings.py após essa sessão.")
    print("Abra uma nova sessão Codex e siga docs/start-project.md para verificar skills e Context7.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Preparação interrompida: {error}. Corrija o diagnóstico e execute novamente.")
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("Preparação cancelada. Configurações existentes foram preservadas.")
