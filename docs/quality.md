# Quality gates antes da stack

Nenhum framework, gerenciador de pacotes ou dependência de aplicação foi escolhido.
Python 3.11+ é usado apenas para os checks da base; não escolhe a linguagem do produto.

| Gate | Comando / critério | Estado |
|---|---|---|
| Integridade do template | `python3 -m unittest discover -s tests -v` | Offline: arquivos exportáveis, links, sintaxe e whitespace |
| Inicialização segura | Incluída na mesma suíte offline | Criação de escopo e exclusões; configuração existente preservada; entrada inválida recusada |
| Integridade do diff | `git diff --check` | Executável agora; não cobre arquivos untracked |
| Política de captura | `python3 scripts/check-capture.py` | Allowlist positiva, negativa e exclusões; não envia eventos |
| Embeddings locais | `python3 scripts/check-embeddings.py` | Consulta o serviço: MiniLM local e saúde; `pending` significa sem chamadas, não aprovação funcional |
| MCP AI Memory | `python3 scripts/check-memory-mcp.py` | Após a primeira sessão: status e busca no escopo; antes dela, `--status-only` valida conexão, catálogo e status global |
| Lint e formato da aplicação | Escolher ferramentas da stack adotada | Não aplicável ainda |
| Tipos | Comando real do compilador adotado | Não aplicável ainda |
| Testes | Regressões e comportamento de risco | Não aplicável ainda |
| Build | Build real do projeto | Não aplicável ainda |
| Segurança e acessibilidade | Revisar limites de confiança e fluxos alterados | Definir conforme produto |

Ao iniciar um projeto, registre comandos reais neste documento e em AGENTS.md,
use dependências já adotadas e rode checks explícitos antes de concluir.
ESLint/Biome são opções do toolkit para stacks compatíveis; não são pré-requisitos
desta base. Não instale hooks Git ou bloqueios de branch/push por padrão.

Um gate indisponível precisa de motivo; um comando vazio ou que apenas imprime
sucesso não pode representar lint, teste ou build. Separe checks rápidos de análise
de tipos mais cara. Não formate ou corrija arquivos automaticamente na validação.

O check offline inclui arquivos versionados e novos que o Git não ignora. Ele
detecta também estado local incluído por engano no índice; `.gitignore` não remove
arquivos já versionados. Os checks AI Memory são separados e exigem o setup da
máquina e o marcador deste checkout; não são aprovados automaticamente pelo teste
offline. Os testes do próprio template não substituem os testes da aplicação.
