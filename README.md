# AI Project Starter

Um ponto de partida reutilizável para desenvolver projetos com **Codex como agente
principal**, instruções compartilhadas, memória entre sessões e verificações de
qualidade desde o início.

A base funciona como uma fábrica local: você escolhe uma pasta e um nome, gera
um projeto independente, prepara as integrações e começa a descrever seu produto
ao agente. Framework, banco, hospedagem e linguagem da aplicação são
escolhidos depois, conforme os requisitos.

O template reúne documentação, instruções e scripts de preparação. O setup usa
as ferramentas já instaladas na máquina; não instala Codex, plugins ou servidor
de memória. Python é necessário apenas para os scripts e testes desta base.

## O que compõe a base

| Componente | Responsabilidade |
|---|---|
| Codex | Agente principal de desenvolvimento |
| Superpowers | Orientar descoberta de requisitos, planejamento, TDD e revisão |
| Ponytail `full` | Evitar complexidade desnecessária e manter a menor solução completa |
| AI Memory | Manter contexto e conhecimento entre sessões, com escopo por projeto |
| Context7 | Consultar documentação de bibliotecas e APIs |
| AGENTS.md | Compartilhar instruções e convenções do projeto |
| Quality gates | Verificar a base e orientar os checks da aplicação quando houver stack |

O ambiente de referência é **Fedora/Linux**. O fluxo foi validado nesse ambiente;
macOS e Windows ainda não foram validados para esta versão.

## Instalação e primeiro uso

### 1. Prepare a máquina uma vez

Você precisa de Git, Python 3.11+, Codex autenticado, Superpowers, Ponytail,
Context7 e AI Memory com serviço, MCP e hooks nativos em modo allowlist.

Se essas integrações ainda não estiverem prontas, comece pelo
[guia de preparação da máquina](docs/setup.md). Essa etapa é feita uma vez por
máquina; copiar o template não transporta login, plugins ou serviços.

### 2. Obtenha a fábrica uma vez

Clone esta base em uma pasta própria. Essa pasta guarda a fábrica; o produto será
criado em outra pasta, com o nome escolhido por você:

```bash
git clone https://github.com/JulioLafre/ai-project-starter.git
cd ai-project-starter
```

Se já clonou a base, use essa cópia. Não é necessário criar um repositório no
GitHub antes de começar o desenvolvimento local.

### 3. Gere um projeto com pasta e nome próprios

Na pasta da fábrica:

```bash
python3 scripts/create-project.py
```

Exemplo de respostas:

```text
Pasta base [~/dev/projetos]: ~/dev/projetos
Nome do projeto: controle-financeiro
Novo projeto: .../dev/projetos/controle-financeiro
Criar neste caminho? [s/N]: s
Executar a preparação agora? [s/N]: s
```

O gerador copia somente arquivos versionados da base, excluindo dados locais.
Cria um Git novo na branch `main`, sem histórico, remoto ou commit herdados, e um
README com o nome escolhido. Recusa destinos existentes e pastas dentro da fábrica.
Links simbólicos versionados são recusados. Não desenvolva o produto na fábrica.

O assistente oferece executar o setup já na pasta nova. Se preferir preparar
depois, ou se algum diagnóstico falhar, a pasta gerada é preservada. Entre nela
e execute:

```bash
cd ~/dev/projetos/controle-financeiro
python3 scripts/setup-project.py
```

O assistente vai pedir a identidade de memória e sua confirmação para ativar a
captura. Exemplo de respostas:

```text
Workspace: pessoal
Projeto [controle-financeiro]:
Ativar captura neste projeto? [s/N]: s
```

**Workspace** agrupa projetos; **projeto** identifica o histórico desta aplicação.
Enter aceita o nome da pasta sugerido para o projeto. Isso não muda a pasta física.
Use nomes em minúsculas, com letras, números, ponto, hífen ou underscore. Para
uma aplicação nova, escolha um par que ainda não pertença a outro projeto. O
assistente não verifica exclusividade desses nomes no servidor.

O comando verifica os executáveis necessários, roda os testes da base, confirma
allowlist e cria um `.ai-memory.toml` local com escopo e exclusões de captura.
Depois testa a política de captura, diagnostica o MiniLM local no serviço ativo
e verifica a conexão/status do bridge MCP do AI Memory.
Configurações existentes são preservadas; um escopo diferente é recusado.

Embeddings desativados, com erro ou com outro provedor/modelo interrompem o setup
com orientação. Se o MiniLM ainda não recebeu chamadas, o diagnóstico informa
`pending`; repita `python3 scripts/check-embeddings.py` após a primeira sessão real.

Para informar o escopo sem perguntas, este comando já autoriza o opt-in:

```bash
python3 scripts/setup-project.py --workspace pessoal --project controle-financeiro
```

### 4. Abra o Codex dentro do projeto gerado

Após o setup concluir:

```bash
codex
```

Use o [prompt inicial](docs/start-project.md) ou descreva o problema, o público e
o resultado que deseja construir. Confirme nessa sessão que as skills e as
ferramentas MCP estão disponíveis. A instalação de um executável não comprova
que seus plugins ou o Context7 foram carregados.

Com os hooks funcionando, a primeira sessão real registra o projeto no AI Memory.
Por isso, a busca nesse escopo novo fica pendente durante o setup; ela pode ser
testada depois. Os detalhes estão no [guia de setup e diagnóstico](docs/setup.md).

### 5. Publique no GitHub quando desejar

O projeto gerado não tem remoto. Crie um repositório vazio no GitHub e execute
na pasta do projeto, substituindo a URL:

```bash
git add .
git commit -m "Initial commit"
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

Revise os arquivos antes de adicionar e enviar. A fábrica não cria repositórios
no GitHub nem faz commits ou push por você.

**Alternativa:** o uso pelo botão **Use this template** do GitHub e por ZIP
continua possível. Nesse caso, obtenha a base diretamente na pasta do produto,
inicialize Git se necessário e execute `python3 scripts/setup-project.py` ali.
O gerador requer uma cópia Git da fábrica; ele não exporta arquivos não versionados.

## O que você recebe

| Arquivo | Uso |
|---|---|
| [AGENTS.md](AGENTS.md) | Instruções dos agentes e roteamento de memória |
| [CLAUDE.md](CLAUDE.md) | Importação das mesmas instruções para compatibilidade |
| [scripts/create-project.py](scripts/create-project.py) | Gerador de projetos locais com nome, pasta e Git independentes |
| [scripts/setup-project.py](scripts/setup-project.py) | Assistente de preparação de cada projeto |
| [docs/setup.md](docs/setup.md) | Pré-requisitos, configuração e diagnóstico |
| [docs/start-project.md](docs/start-project.md) | Prompt para começar a definir o produto |
| [docs/quality.md](docs/quality.md) | Checks da base e critérios para os gates da aplicação |
| [tests/](tests/) | Testes offline de integridade e inicialização segura |

O template não cria uma aplicação, escolhe stack ou instala dependências de
produto. Também não habilita APIs pagas, modifica configurações globais, cria
MEMORY.md concorrente ou adiciona Obsidian.

O marcador `.ai-memory.toml`, credenciais, backups e relatórios são locais e ficam
fora do Git. Cada clone precisa do próprio opt-in de captura. Projetos distintos
devem usar identidades distintas; checkouts da mesma aplicação podem compartilhar
histórico quando isso for intencional.

## Verificar a base sem usar IA

Com Git e Python 3.11+ disponíveis, execute:

```bash
python3 -m unittest discover -s tests -v
```

Esses testes não precisam de Codex, AI Memory ou rede. Eles verificam arquivos
exportáveis, links locais, sintaxe, whitespace e criação segura do marcador. Os
checks de lint, tipos, testes e build da aplicação são definidos quando a stack
for escolhida; veja os [quality gates](docs/quality.md).

## Licença e créditos

Disponível sob [licença MIT](LICENSE), com avisos de autoria preservados.
Esta base adapta instruções e práticas de outros projetos; consulte os
[créditos e componentes externos](THIRD_PARTY.md). A licença desta base não
substitui os termos das ferramentas externas usadas por ela.
