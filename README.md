# Web Sorter

Aplicação web em **Flask** para organizar arquivos, fotos e vídeos de pastas
do computador. Depois de entrar na conta, o usuário tem três abas:

- **Organizar por extensão** (tela inicial): escolhe pastas de origem, as
  extensões e uma pasta de destino, e copia ou move tudo de uma vez.
- **Explorar pasta (grade)**: navega pelas subpastas, seleciona arquivos e
  move ou deleta, com confirmação e painel de erros.
- **Decidir arquivo a arquivo**: marca cada arquivo para mover, excluir ou
  manter, e retoma de onde parou ao voltar à mesma pasta.

O **Histórico** mostra as operações das duas primeiras abas e permite
**retomar** uma operação que foi fechada no meio. As telas seguem os
[wireframes do Figma](https://www.figma.com/design/otIHV04hUsnAm4Noq71uxI/).

Trabalho 2 de Engenharia de Software: Clean Architecture, SOLID e testes
unitários com Pytest.

## Histórias de usuário

| # | História | Caso de uso |
|---|----------|-------------|
| 1 | Como visitante, quero criar uma conta para guardar meu progresso. | `RegisterUser` |
| 2 | Como usuário, quero entrar e sair da minha conta. | `AuthenticateUser` |
| 3 | Como usuário, quero abrir uma pasta e ver as decisões que já tomei nela. | `OpenSession`, `ListSessions` |
| 4 | Como usuário, quero decidir o que fazer com cada arquivo, cadastrar destinos, desfazer decisões e aplicá-las na pasta. | `AddDestination`, `RecordDecision`, `UndoDecision`, `MarkDecisionApplied` |
| 5 | Como usuário, quero ver o resumo do meu progresso. | `GetSessionSummary` |
| 6 | Como usuário, quero ver as extensões das pastas de origem e suas quantidades (SCRUM-56). | `SummarizeExtensions` |
| 7 | Como usuário, quero conferir um resumo e confirmar antes de copiar, mover ou deletar (SCRUM-41 e 57). | `PlanBatch`, `StartBatch` |
| 8 | Como usuário, quero ver quais arquivos falharam e por quê (SCRUM-42). | `RecordItemResult`, `FinishBatch` |
| 9 | Como usuário, quero retomar ou descartar uma operação interrompida. | `ResumeBatch`, `DiscardBatch` |
| 10 | Como usuário, quero consultar o histórico de operações. | `ListBatches`, `GetBatch` |

A navegação por subpastas (SCRUM-40) acontece toda no navegador e não gera
caso de uso. `ResolveTargetName` apoia a história 4: escolhe um nome livre
quando já existe um arquivo igual no destino.

## Entidades

- **User**: usuário e hash da senha.
- **SortingSession**: o trabalho de um usuário em uma pasta (nome da pasta,
  destinos cadastrados, datas).
- **FileDecision**: decisão sobre um arquivo (`move`, `delete` ou `keep`),
  com destino e indicação de que já foi aplicada.
- **Batch**: lote de cópia, movimentação ou exclusão (origens, destino,
  situação). Planeja os nomes finais e decide quando pode ser concluído.
- **BatchItem**: um arquivo do lote, com nome final, resultado e motivo da
  falha em linguagem simples.

## Como rodar (Windows / PowerShell)

Requer Python 3.10 ou superior.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main
```

Abra <http://127.0.0.1:5000>, crie uma conta e entre. Use **Chrome ou Edge**:
a escolha de pasta usa a File System Access API, que o Firefox e o Safari
ainda não oferecem. O banco SQLite e a chave de sessão ficam em `instance/`
(ignorada pelo Git).

## Testes e qualidade

```powershell
pytest                                   # 187 testes
pytest --cov=domain --cov=use_cases --cov=infra --cov=app
flake8 app domain use_cases infra tests  # PEP-8
```

## Arquitetura (Clean Architecture)

```
domain/        Entidades e regras de negócio (não importa nada de fora)
use_cases/     Casos de uso + portas (interfaces) exigidas da infraestrutura
app/           Interface adapters: rotas Flask, presenters, segurança,
               composição (container) e arquivos estáticos/templates
infra/         Frameworks & drivers: SQLite, hash de senha (Werkzeug)
tests/         domain/, use_cases/ (com dublês em memória), infra/, app/
```

Regra da dependência: `app` e `infra` dependem de `use_cases`, que depende de
`domain`. Nada em `domain` ou `use_cases` importa Flask, SQLite ou Werkzeug.
Os casos de uso falam com `ports.py` (`UserRepository`, `SessionRepository`,
`DecisionRepository`, `BatchRepository`, `BatchItemRepository`,
`PasswordHasher`); `infra/` implementa essas portas e `app/container.py` é o
único lugar que escolhe as implementações.

O navegador só faz o que o servidor não pode fazer: ler e gravar nas pastas
do usuário. As regras (agrupar extensões, nomes repetidos, validações,
tradução dos erros, retomada) ficam em `domain/` e `use_cases/`. O JavaScript
é dividido em módulos em `app/static/js/`: um por aba, mais `fs.js` (pastas),
`batch-runner.js` (execução dos lotes) e `handle-store.js` (IndexedDB).

## Princípios SOLID

| Princípio | Onde aparece |
|-----------|--------------|
| **S**: responsabilidade única | Cada caso de uso é uma classe com um único método `execute`. Rotas só traduzem HTTP; repositórios só persistem; `presenters.py` só serializa. |
| **O**: aberto/fechado | Trocar SQLite por outro banco = nova classe que implementa as portas, sem mexer em casos de uso. As tabelas de lote entraram sem alterar as entidades e casos de uso existentes. |
| **L**: substituição de Liskov | Os repositórios SQLite e os dublês em memória dos testes são intercambiáveis: os mesmos casos de uso funcionam com ambos. |
| **I**: segregação de interfaces | Seis portas pequenas; cada caso de uso recebe só as que usa (`ListSessions` não conhece decisões nem hash de senha). |
| **D**: inversão de dependência | Casos de uso dependem de abstrações (`ports.py`); as implementações são injetadas em `app/container.py`. O relógio também é injetável (`Clock`). |

## Decisões e limites conhecidos

- O navegador não revela o caminho completo de uma pasta. A sessão é
  identificada pelo **nome da pasta** e o usuário escolhe a pasta de novo ao
  voltar; as decisões são reencontradas pelo nome do arquivo.
- O servidor guarda apenas **nomes de pastas e arquivos, decisões e
  resultados**, nunca o conteúdo. Copiar, mover e excluir acontece no
  navegador, sempre depois de uma confirmação.
- **RNF1 do Jira ("nada é persistido")**: o trabalho pede persistência, então
  a regra foi lida como "o conteúdo dos arquivos nunca sai do navegador". A
  navegação e a seleção continuam só em memória.
- **Mover** copia, confere o tamanho e só depois remove o original. Nada é
  sobrescrito: nomes repetidos ganham sufixo, como `foto (1).jpg`.
- **Retomar**: a referência das pastas fica no IndexedDB do navegador, e o
  usuário só autoriza de novo. Sem ela, escolhe as mesmas pastas, conferidas
  pelo nome. Só os arquivos sem resultado são processados; no pior caso, um
  arquivo é copiado duas vezes ou, ao mover, aparece como ausente na origem.
- **Organizar** e **Decidir** usam só os arquivos do primeiro nível da pasta;
  **Explorar** navega por todas as subpastas, sem subir além da raiz escolhida.
- O caminho completo só aparece para pastas dentro da raiz aberta em
  **Explorar**. Fora dela, o navegador revela apenas o nome da pasta.
- Segurança: senhas com hash (Werkzeug), cookie `HttpOnly` + `SameSite=Lax`,
  token CSRF em todas as requisições que alteram dados, cabeçalho CSP, e
  cada usuário só acessa as próprias sessões (resposta 404 caso contrário).
- A aplicação escuta apenas em `127.0.0.1`, pensada para uso local.

## Uso de IA (bônus)

> **Rascunho: o grupo deve revisar este texto e ajustá-lo ao que realmente
> fez antes da entrega.**

Usamos o Claude (Anthropic) como apoio, com uma estratégia em etapas:

1. **Entrevista antes do código.** Com a skill *grill me* (pocock-skills), a
   IA leu o enunciado, os wireframes do Figma, as histórias do Jira e o
   código, e fez 21 perguntas em três rodadas, cada uma com uma recomendação.
   O código só começou depois da confirmação.
2. **Decisões humanas.** Rafael respondeu à entrevista e recusou duas
   recomendações da IA: ela propôs substituir a tela de decisões, que ficou
   como terceira aba; e propôs não retomar operações interrompidas, o que
   virou uma história do sistema. A leitura da RNF1 também foi submetida à
   aprovação humana antes do código.
3. **Geração de código.** A IA gerou a primeira versão das camadas, das telas
   e dos testes, começando pelo domínio e pelos casos de uso.
4. **Verificação.** Os casos de uso são testados com dublês em memória, sem
   infraestrutura, e o código passa no `flake8`. A IA também testou as telas
   no navegador com pastas de teste. Nessa etapa ela encontrou e corrigiu uma
   falha própria: um lote interrompido deixava um arquivo vazio no destino.
5. **Limites.** O JavaScript não tem testes automatizados. A conferência usou
   pastas virtuais do navegador; falta testar em pastas reais no Chrome ou
   no Edge.
