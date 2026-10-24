# Plano de implementação da fábrica

Desenho aprovado: [project-factory-design.md](project-factory-design.md).
Implementação direta, com Python 3.11+ e Git existentes, sem dependências novas.

- [x] Criar testes offline de geração: nome/pasta, Git independente, arquivos
  locais excluídos, destino existente preservado, nomes inválidos, caminhos dentro
  da fábrica, links simbólicos e falha de setup sem apagar o projeto gerado.
- [x] Implementar `scripts/create-project.py` com entradas interativas, confirmação
  do caminho e exportação dos arquivos versionados. Inicializar `main` sem remoto
  e sem commit; adaptar o README e oferecer o setup existente no destino.
- [x] Sugerir o nome da pasta no prompt de projeto de `scripts/setup-project.py`,
  mantendo workspace explícito e confirmação da captura. Testar essa interação.
- [x] Atualizar README, guia de setup e quality gates para o fluxo da fábrica,
  mantendo a preparação de clones como alternativa e a publicação Git posterior.
- [x] Executar a suíte offline, testes reais de geração em diretório temporário,
  `git diff --check` e os checks de captura, embeddings e MCP. Revisar o diff.

Limites: não sobrescrever destinos, copiar segredos ou marcador, configurar remoto,
criar memória artificial, instalar ferramentas ou alterar configurações globais.
Exportar apenas arquivos versionados regulares e recusar links simbólicos;
arquivos locais sensíveis são excluídos mesmo se adicionados ao índice por engano.

Evidência: 28 testes offline passaram na fábrica; o teste completo de geração
executou também a suíte dentro do projeto temporário
em um caminho com espaços. Captura allowlist, MiniLM local e status/busca MCP
passaram no serviço real. Nenhuma sessão artificial ou página de teste foi criada.

A revisão independente encontrou herança de variáveis Git ao iniciar o setup.
O teste `test_setup_cannot_inherit_factory_git_environment` reproduziu o problema
antes da correção e passou depois de isolar o ambiente do subprocesso.
