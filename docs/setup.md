# Instalação, configuração e diagnóstico

O uso tem duas etapas: preparar as integrações na máquina uma vez e executar o
assistente em cada projeto novo. Este repositório fornece a segunda etapa e os
checks; não é um instalador global de ferramentas.

O fluxo de referência foi validado no Fedora/Linux. Outros sistemas operacionais
ainda precisam de validação. Comece pelo [passo a passo do README](../README.md)
para obter a base pelo GitHub ou por ZIP.

## 1. Preparar a máquina uma vez

Antes de executar o assistente, confira os itens abaixo. Preserve integrações
que já funcionam; use a documentação oficial para instalar ou configurar o que
faltar, sem copiar credenciais ou configurações pessoais de outra máquina.

| Componente | O que deve estar pronto | Referência |
|---|---|---|
| Git | Comando `git` disponível no terminal | [Instalação oficial](https://git-scm.com/install/) |
| Python | Comando `python3`, versão 3.11 ou superior | [Distribuições oficiais](https://www.python.org/downloads/) |
| Codex | CLI disponível, login concluído e modelo escolhido | [Guia oficial do CLI](https://learn.chatgpt.com/docs/codex/cli) |
| Superpowers | Skills descobertas pelo Codex na instalação compatível com seu cliente | [Projeto oficial](https://github.com/obra/superpowers) |
| Ponytail | Plugin/skill funcionando no Codex, modo `full` | [Projeto oficial](https://github.com/DietrichGebert/ponytail) |
| Context7 | Plugin ou MCP funcional, sem duplicar a mesma integração | [Projeto oficial](https://github.com/upstash/context7) |
| AI Memory | Binário no PATH, serviço acessível, autenticação e MCP configurados; skills gerenciadas disponíveis | [Instalação oficial](https://github.com/akitaonrails/ai-memory) |

Confira os executáveis básicos:

```bash
git --version
python3 --version
codex --version
ai-memory --version
```

Confirme o login pelo fluxo do Codex e reinicie o cliente após configurar plugins
ou MCPs. Teste as skills e uma consulta pública no Context7 em uma sessão nova.
Para memória, use `ai-memory status --json` e `ai-memory doctor --json` no ambiente
correto. Executáveis no PATH e entradas de config são pré-requisitos, não provas
suficientes de funcionamento das integrações.

### Embeddings locais no serviço

Esta base espera o provedor `local`, modelo `all-MiniLM-L6-v2`, com 384 dimensões.
O modelo pertence ao serviço da máquina e é compartilhado entre os projetos;
não é instalado dentro de cada repositório. Uma LLM de consolidação é separada
e não é necessária para essa busca semântica.

Execute o diagnóstico somente leitura:

```bash
python3 scripts/check-embeddings.py
```

Ele consulta `ai-memory status --json`, sem gerar embeddings, criar memórias ou
chamar provedores. Embeddings desativados, em erro ou com outro provedor/modelo
interrompem o check. O comando mostra também contagens globais de indexação;
elas não comprovam a indexação de um projeto específico. Zero páginas é válido
num serviço novo, e páginas ainda não indexadas podem indicar backfill em curso.

O estado `unknown` do AI Memory significa que o provedor ainda não recebeu
chamadas. Nesse caso, o diagnóstico retorna `pending`, permite preparar o projeto
e orienta repetir a verificação após a primeira sessão real; não afirma sucesso
funcional. A conclusão dessa verificação requer `status: ok`.

No primeiro uso, o AI Memory pode baixar o modelo em segundo plano e continuar
sem embeddings até a próxima inicialização. Confira os logs para confirmar o
término do download. No Fedora com serviço de usuário, reinicie manualmente:

```bash
systemctl --user restart ai-memory.service
python3 scripts/check-embeddings.py
```

O assistente não reinicia o serviço, baixa modelos ou altera a configuração da
máquina. Um modelo local diferente exige revisar esta expectativa da base;
o diagnóstico nunca substitui um provedor existente automaticamente.

### Captura allowlist na máquina

O serviço e os hooks do AI Memory precisam estar configurados antes de preparar
os projetos. No modo allowlist, apenas repositórios com marcador local participam
da captura. Uma instalação com captura ampla não atende aos requisitos desta base.

Se precisar configurar os hooks nativos do Codex, o comando do AI Memory é:

```bash
ai-memory install-hooks --agent codex --capture-mode allowlist --apply
```

Essa é uma **etapa manual de configuração global de hooks**: faça backup, revise
os ajustes e preserve hooks de outras integrações. Ela não é executada pelo
assistente deste template. Siga a documentação do AI Memory para configurar seu
serviço, credencial e MCP; não grave tokens no repositório ou na conversa.

AI Memory é a memória principal. Na preparação da máquina, confira também a
configuração de memória nativa do cliente para evitar uma segunda fonte de
memória. O template não faz essa alteração global automaticamente.

O [Vibe Coding Toolkit](https://github.com/soumatheusgomes/vibe-coding-toolkit)
é uma referência adicional de ambiente. Seus guias mais amplos podem incluir
ferramentas e stacks que esta base não exige; adote apenas o escopo necessário.

## 2. Preparar cada projeto

Crie um repositório novo pelo template ou extraia o ZIP em uma pasta própria.
Se usou ZIP, execute `git init` na pasta extraída. Entre na raiz do projeto, onde
estão AGENTS.md, README.md e a pasta scripts, antes de executar o assistente.

O caminho recomendado é o assistente local:

```bash
python3 scripts/setup-project.py
```

Ele não instala pré-requisitos ausentes nem modifica a configuração global. Antes
de criar um marcador, exige os executáveis Git, Codex e AI Memory, passa nos testes
offline e confirma que a política instalada é allowlist. Para um checkout novo,
pede o escopo e confirmação para captura; depois cria o marcador com as exclusões
abaixo, testa a captura, diagnostica os embeddings locais e consulta o status pelo
bridge MCP. Uma configuração existente é preservada e validada; nunca é completada
ou substituída automaticamente.

Também aceita `--workspace` e `--project` juntos para opt-in sem perguntas. Um
escopo diferente do marcador atual é recusado. Escolha um par próprio: o comando
não reserva nomes nem confirma exclusividade no servidor.

Se um diagnóstico falhar depois da criação, o marcador permanece local. Corrija
o problema e execute o comando novamente; não há rollback que apague configurações.
O check MCP exige acesso ao serviço. Ao terminar, confirme skills e Context7 numa
nova sessão Codex; isso não é inferido da presença dos executáveis no PATH.

O assistente usa `check-memory-mcp.py --status-only`: valida initialize, catálogo e
status global por `ai-memory status --json`. Não chama `memory_status` nem busca
no escopo de um projeto ainda não registrado no servidor. A
primeira sessão real do agente registra o escopo. Depois dela, o comando sem essa
opção também testa a busca com workspace/project explícitos. Não são criadas
sessões artificiais nem páginas de teste para contornar essa etapa.

### Alternativa manual

Faça isso no repositório novo, antes da primeira sessão do agente:

```bash
ai-memory project init
```

Escolha workspace e project explicitamente. Para um projeto novo, use um par
que ainda não identifique outro projeto. Checkouts do mesmo projeto podem usar
o mesmo par quando compartilhar histórico for intencional. O comando cria o
marcador e preserva um arquivo existente; não copie um marcador de outro projeto.

No `.ai-memory.toml` gerado, mantenha os dois valores escolhidos e acrescente as
exclusões abaixo. Se já houver `[capture]`, mescle a lista sem duplicar a tabela:

```toml
[capture]
ignore_paths = [".env", ".env.*", "**/.env", "**/.env.*", ".setup/**", "secrets/**", "**/*.pem", "**/*.key", "docs/adr/**"]
```

O marcador real é ignorado pelo Git. Cada checkout precisa do próprio opt-in;
um clone novo não herda autorização de captura. Não coloque marcador em diretório
pai compartilhado e não abra o agente enquanto o escopo/exclusões estiverem
incompletos. Um projeto sensível pode permanecer sem marcador e sem captura.

Os hooks devem estar em allowlist na máquina; o marcador sozinho não muda essa
política global. O check de captura exige allowlist e um marcador com escopo
explícito e testa diretório não marcado e exclusões sem enviar eventos.
Se o pré-requisito falhar, relate o diagnóstico e solicite a preparação da máquina;
não mude a configuração global automaticamente.

AGENTS.md já contém o bloco de roteamento do ai-memory. Se precisar atualizar as
skills ou o bloco, use o binário instalado, com backup e preservação de regras:

```bash
ai-memory install-instructions --target AGENTS.md --compact --skills-agent agents
```

Esse comando modifica arquivos do projeto e não faz parte dos checks somente
leitura. Skills geradas ficam locais. Não use `--force` para substituir skills
customizadas. No Codex estático, chamadas MCP devem ler e passar o workspace e
o project deste marcador; não confiar no último projeto ativo do servidor.

## 3. Validar e começar a desenvolver

Antes da primeira sessão do agente, estes checks podem ser executados sem criar
sessões artificiais ou memórias de teste:

```bash
python3 scripts/check-capture.py
python3 scripts/check-embeddings.py
python3 scripts/check-memory-mcp.py --status-only
```

Depois, abra `codex` na raiz do projeto, confirme as integrações e use o
[prompt inicial](start-project.md). Com os hooks funcionando, a primeira sessão
real registra o escopo. Só então execute o diagnóstico que inclui busca:

```bash
python3 scripts/check-capture.py
python3 scripts/check-embeddings.py
python3 scripts/check-memory-mcp.py
ai-memory doctor --json
```

O primeiro comando é seco: não usa rede nem grava eventos. O diagnóstico de
embeddings consulta a saúde passiva do serviço, conforme explicado acima.
O check MCP usa o bridge nativo já instalado, consulta status e busca com escopo explícito, sem
criar páginas ou chamar LLM. Ele valida esse caminho de acesso; não comprova
que a configuração MCP do cliente Codex foi carregada.

Em uma sessão nova do Codex, confirme descoberta das skills e ferramentas MCP.
Use uma consulta pública no Context7 e consulte AI Memory no escopo do marcador.
Não envie segredos ou código privado para documentação externa. Autenticação,
serviço e ferramentas descobertas precisam de evidência; um arquivo de config
sozinho não comprova funcionamento.

Se o sandbox bloquear localhost, o barramento do serviço ou a execução de um
check, solicite apenas o acesso necessário. Não relaxe permissões globais nem
apresente o bloqueio como falha comprovada do serviço. Em Fedora com serviço de
usuário, `systemctl --user is-active ai-memory.service` é um diagnóstico possível,
não uma dependência do template em todas as máquinas.

## Problemas comuns

| Sintoma | Próximo passo |
|---|---|
| Pré-requisito ausente | Prepare o componente na máquina; o assistente não instala ferramentas |
| Política diferente de allowlist | Revise a etapa global de hooks antes de ativar um projeto |
| Marcador com outro escopo | Confira se está na pasta correta; o assistente não troca a identidade existente |
| Serviço MCP inacessível | Verifique serviço, credencial e restrições de rede/sandbox; o script não inicia o servidor |
| Embeddings desativados | Confira download/logs e a configuração; após o download inicial reinicie manualmente o serviço e repita o diagnóstico |
| Embeddings com `pending` | O modelo está configurado, mas ainda sem chamadas; repita o check após a primeira sessão real |
| Projeto não encontrado na busca | Confirme o escopo e a captura da primeira sessão real do agente; antes disso use `--status-only` |
| Check falhou após criar o marcador | Corrija o diagnóstico e repita o setup; o marcador existente é preservado |
| Context7 ou skills ausentes no Codex | Revise a integração do cliente e abra uma nova sessão; o setup não instala plugins |

## Memória e dados locais

AI Memory é a referência entre sessões. Não adicione MEMORY.md concorrente ou
Obsidian. Preserve dados existentes; qualquer migração/exclusão é separada.
Regras ficam em AGENTS.md e ADRs revisados no repositório. Não habilite provedores
pagos para validar captura ou busca.

Exclusões não garantem filtragem de segredos em comandos arbitrários, prompts ou
ferramentas desconhecidas. Não forneça segredos em conversas. As opções de memória
nativa do cliente devem ser verificadas na preparação da máquina para evitar uma
segunda fonte de memória; este template não reescreve configurações globais.

Backups e diagnósticos locais devem ficar em `.setup/` ou `reports/`, ignorados.
Não armazene credenciais nesses relatórios e não copie o diretório de trabalho
inteiro para distribuir o template.

## Distribuir esta base como template no GitHub

Ao publicar sua cópia da base, inclua os arquivos revisados e preserve LICENSE e
THIRD_PARTY.md. Não inclua o marcador local, configurações globais, backups ou
relatórios. O `.gitignore` não remove do histórico arquivos já versionados;
revise o que será enviado antes do primeiro push.

Para habilitar a criação de projetos pelo botão do GitHub, ative **Template
repository** em **Settings** do repositório publicado, conforme a
[documentação oficial](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository).
A distribuição usa os arquivos versionados; o ZIP local e dados ignorados de
uma máquina não são dependências do repositório público.
