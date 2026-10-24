"""Read the running service's embedding health without model calls or configuration changes."""

import json
import subprocess


def check_status(report):
    embedding = report["providers"]["embedding"]
    if embedding.get("status") == "disabled":
        raise ValueError("Embeddings desativados. Confira o download do modelo e os logs; "
                         "após o download inicial, reinicie o serviço manualmente. Veja docs/setup.md.")
    if (embedding.get("provider"), embedding.get("model"), embedding.get("dim")) != (
            "local", "all-MiniLM-L6-v2", 384):
        raise ValueError("O serviço não informa o MiniLM local esperado por esta base. "
                         "Revise a configuração da máquina conforme docs/setup.md.")
    state = embedding.get("status")
    if state not in {"ok", "unknown"}:
        raise ValueError("Saúde dos embeddings não confirmada. Confira ai-memory status --json "
                         "e os logs do serviço; nenhuma configuração foi alterada.")
    derived = report.get("derived", {})
    return {"status": "ok" if state == "ok" else "pending",
            "provider": "local", "model": "all-MiniLM-L6-v2", "dim": 384,
            "embedding_rows": derived.get("embedding_rows"),
            "latest_pages_missing_embeddings": derived.get("latest_pages_missing_embeddings")}


def main():
    try:
        result = subprocess.run(["ai-memory", "status", "--json"],
                                capture_output=True, text=True, check=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        raise SystemExit("Não foi possível consultar o serviço. Confira conexão, autenticação e "
                         "permissões de rede/sandbox com ai-memory status --json.") from None
    try:
        summary = check_status(json.loads(result.stdout))
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError):
        raise SystemExit("Status do serviço sem diagnóstico de embeddings válido. "
                         "Confira a versão e ai-memory status --json.") from None
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print(json.dumps(summary))
    if summary["status"] == "pending":
        print("MiniLM configurado, mas ainda sem chamadas: validação funcional pendente. "
              "Repita este diagnóstico após a primeira sessão real.")


if __name__ == "__main__":
    main()
