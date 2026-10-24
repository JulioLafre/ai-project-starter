# Fábrica de projetos locais

## Objetivo

Manter uma cópia do starter como fábrica reutilizável. Cada execução gera um
projeto independente no diretório e com o nome escolhidos, pronto para preparar
as integrações e começar o desenvolvimento local. GitHub entra posteriormente.

## Abordagem proposta

Adicionar `python3 scripts/create-project.py`, usando Python e Git já exigidos
pela base. O assistente solicita pasta de destino e nome do projeto. Por exemplo,
uma pasta base `~/dev/projetos` e um nome `meiproject` geram
`~/dev/projetos/meiproject`.

Gerar uma cópia dos arquivos versionados da base, sem copiar seu diretório `.git`,
marcador de memória, credenciais, relatórios ou outros dados locais. Recusar um
destino que já exista e impedir a criação dentro da própria fábrica. Inicializar
um repositório Git independente na branch `main`, sem remoto e sem commit inicial.
Mostrar a pasta resolvida antes de criar os arquivos.

Adaptar o título do README ao nome escolhido e manter as instruções necessárias
para começar. Nenhuma stack de aplicação será escolhida.

## Preparação e memória

Ao terminar a geração, oferecer a execução do `scripts/setup-project.py` dentro
do projeto novo. Esse script continua responsável por validar pré-requisitos,
allowlist, captura, MiniLM e conexão MCP, bem como pelo opt-in de memória.

Usar o nome escolhido como sugestão para o identificador de memória, preservando
a escolha de workspace e a confirmação explícita de captura. A fábrica não
recebe nem compartilha o marcador do projeto gerado.

Se a preparação falhar, preservar a pasta e informar o comando para continuar
dentro dela. Não declarar o projeto configurado quando somente a geração passou.

## Alternativas consideradas

- Gerador local: resolve pasta, nome e independência do Git em um fluxo; recomendado.
- Apenas renomear o clone e trocar seu remoto: mantém a preparação manual e o risco
  de desenvolver na própria fábrica; não atende ao fluxo solicitado.

## Validação

Testar geração em pasta escolhida, arquivos exportados, README personalizado,
Git sem remoto e sem histórico herdado, destino existente preservado, rejeição de
destinos internos e continuidade quando o setup não puder terminar. Executar os
gates reais de `docs/quality.md` e documentar o novo caminho de primeiro uso.

Desenho aprovado para implementação. O gerador mantém a preparação e a captura
como etapas explícitas e não publica o projeto gerado.
