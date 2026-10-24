# Prompt para começar um projeto

Abra o agente na nova pasta, depois de concluir o opt-in de memória descrito no
[setup](setup.md). Cole o texto abaixo e substitua o objetivo:

```text
Leia AGENTS.md, docs/setup.md e docs/quality.md deste projeto.

Quero construir: [objetivo do produto, público e problema a resolver].

Antes de implementar:
1. Verifique as integrações disponíveis e o escopo local de AI Memory.
   Não presuma que as validações de outra máquina valem aqui.
2. Consulte o contexto do próprio projeto. Se não houver histórico, diga isso.
3. Use Superpowers para esclarecer os requisitos relevantes e propor o menor MVP.
4. Mantenha Ponytail em full. Consulte Context7 para a stack que vier a ser escolhida.
5. Proponha a stack conforme os requisitos e preserve escolhas que eu já informar.
6. Registre comandos reais de lint, tipos, testes e build quando existirem.

Não instale extras, habilite APIs pagas, sobrescreva configurações, publique ou
faça push como efeito desta preparação. Peça autorização para ações privilegiadas
ou destrutivas. Depois de esclarecer e aprovar o escopo necessário, execute o
trabalho autorizado e verifique o resultado.
```

Este prompt inicia um produto; ele não instala o ambiente da máquina nem define
framework, banco, provedor, hospedagem ou gerenciador de pacotes antecipadamente.
