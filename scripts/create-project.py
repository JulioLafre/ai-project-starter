"""Generate an independent local project from the factory's tracked files."""

from pathlib import Path
import os
import re
import shlex
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCAL_NAMES = {".git", ".ai-memory.toml", ".agents", ".codex", ".aws", ".ssh",
               ".setup", "reports", "secrets", "__pycache__", "MEMORY.md"}


def git_environment():
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def project_path(source, base, name):
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name):
        raise ValueError("Use um nome em minúsculas, sem espaços, barras ou acentos.")
    target = Path(base).expanduser().resolve() / name
    if target.is_relative_to(source.resolve()):
        raise ValueError("Escolha uma pasta fora da fábrica para o novo projeto.")
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"O destino já existe; nenhum arquivo foi alterado: {target}")
    return target


def export_files(source):
    environment = git_environment()
    prefix = subprocess.run(["git", "-C", str(source), "rev-parse", "--show-prefix"],
                            capture_output=True, text=True, check=True, env=environment).stdout.strip()
    if prefix:
        raise ValueError("Execute o gerador de uma fábrica na raiz do seu próprio repositório Git.")
    result = subprocess.run(["git", "-C", str(source), "ls-files", "--cached", "-z"],
                            capture_output=True, text=True, check=True, env=environment)
    files = []
    for name in result.stdout.split("\0"):
        if not name:
            continue
        relative = Path(name)
        if (LOCAL_NAMES.intersection(relative.parts)
                or relative.suffix.lower() in {".pem", ".key", ".pyc"}
                or any(part == ".env" or (part.startswith(".env.") and part != ".env.example")
                       for part in relative.parts)):
            continue
        path = source / relative
        if (relative.is_absolute() or ".." in relative.parts
                or any((source / parent).is_symlink() for parent in (relative, *relative.parents))
                or not path.resolve().is_relative_to(source.resolve()) or not path.is_file()):
            raise ValueError(f"Arquivo versionado ausente ou não regular; exportação recusada: {relative}")
        files.append(relative)
    if not {Path("README.md"), Path("scripts/setup-project.py")} <= set(files):
        raise ValueError("A fábrica precisa versionar README.md e scripts/setup-project.py.")
    return files


def create_project(source, base, name):
    source = source.resolve()
    target = project_path(source, base, name)
    files = export_files(source)
    target.mkdir(parents=True, exist_ok=False)
    for relative in files:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    (target / "README.md").write_text(f"""# {name}

Projeto criado com AI Project Starter. A stack e o objetivo da aplicação ainda
precisam ser definidos. Git local na branch `main`, sem remoto ou commit inicial.

## Começar

Se a preparação ainda não foi concluída, execute nesta pasta:

```bash
python3 scripts/setup-project.py
```

Depois abra `codex` aqui e descreva o produto usando o
[prompt inicial](docs/start-project.md). As regras ficam em [AGENTS.md](AGENTS.md).
O [guia de setup](docs/setup.md) explica a memória e os diagnósticos.

## Validar

```bash
python3 -m unittest discover -s tests -v
```

Adapte os [quality gates](docs/quality.md) quando escolher a stack.

## Publicar posteriormente

Crie um repositório vazio no GitHub e execute, substituindo a URL:

```bash
git add .
git commit -m "Initial commit"
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

Revise os arquivos antes de adicionar e enviar. O marcador de memória e dados
locais devem permanecer ignorados. Preserve [LICENSE](LICENSE) e
[THIRD_PARTY.md](THIRD_PARTY.md) da base ao adaptar o projeto.
""", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", "--initial-branch=main", "--template=", str(target)],
                   check=True, env=git_environment())
    return target


def main():
    base = input("Pasta base [~/dev/projetos]: ").strip() or "~/dev/projetos"
    name = input("Nome do projeto: ").strip()
    target = project_path(ROOT, base, name)
    print(f"Novo projeto: {target}")
    if input("Criar neste caminho? [s/N]: ").strip().lower() != "s":
        print("Geração cancelada; nenhuma pasta criada.")
        return 0
    try:
        create_project(ROOT, base, name)
    except (OSError, ValueError, subprocess.SubprocessError):
        print(f"Geração não concluída. Se o destino foi criado, ele foi preservado: {target}")
        raise
    print(f"Projeto gerado, com Git independente: {target}")
    print(f"Para entrar: cd {shlex.quote(str(target))}")
    print("Para preparar ou repetir a preparação nessa pasta: python3 scripts/setup-project.py")
    if input("Executar a preparação agora? [s/N]: ").strip().lower() == "s":
        result = subprocess.run([sys.executable, str(target / "scripts/setup-project.py")],
                                cwd=target, env=git_environment())
        if result.returncode:
            print("Projeto gerado e preservado; preparação pendente. Repita o comando acima no destino.")
            return 1
    else:
        print("Preparação pendente; execute o setup antes da primeira sessão do agente.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Geração interrompida: {error}") from None
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("Operação interrompida; pastas já geradas foram preservadas.") from None
