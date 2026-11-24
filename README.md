# Web Sorter

Aplicação web em **Flask** para organizar arquivos, fotos e vídeos de uma
pasta do computador. O usuário cria uma conta, entra, escolhe uma pasta e
decide o que fazer com cada arquivo (**mover** para um destino, **excluir**
ou **manter**). Tudo o que ele decide fica salvo na conta dele: ao entrar de
novo e escolher a mesma pasta, ele **retoma de onde parou**.

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

## Entidades

- **User**: usuário e hash da senha.
- **SortingSession**: o trabalho de um usuário em uma pasta (nome da pasta,
  destinos cadastrados, datas).
- **FileDecision**: decisão sobre um arquivo (`move`, `delete` ou `keep`),
  com destino e indicação de que já foi aplicada.

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
pytest                                   # 85 testes
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
`DecisionRepository`, `PasswordHasher`); `infra/` implementa essas portas e
`app/container.py` é o único lugar que escolhe as implementações.

## Princípios SOLID

| Princípio | Onde aparece |
|-----------|--------------|
| **S**: responsabilidade única | Cada caso de uso é uma classe com um único método `execute`. Rotas só traduzem HTTP; repositórios só persistem; `presenters.py` só serializa. |
| **O**: aberto/fechado | Trocar SQLite por outro banco = nova classe que implementa as portas, sem mexer em casos de uso. Nova ação de arquivo = novo valor em `Action`. |
| **L**: substituição de Liskov | Os repositórios SQLite e os dublês em memória dos testes são intercambiáveis: os mesmos casos de uso funcionam com ambos. |
| **I**: segregação de interfaces | Quatro portas pequenas; cada caso de uso recebe só as que usa (`ListSessions` não conhece decisões nem hash de senha). |
| **D**: inversão de dependência | Casos de uso dependem de abstrações (`ports.py`); as implementações são injetadas em `app/container.py`. O relógio também é injetável (`Clock`). |

## Decisões e limites conhecidos

- O navegador não revela o caminho completo de uma pasta. A sessão é
  identificada pelo **nome da pasta** e o usuário escolhe a pasta de novo ao
  voltar; as decisões são reencontradas pelo nome do arquivo.
- O servidor guarda apenas **nomes de arquivos e decisões**, nunca o conteúdo
  dos arquivos. Mover/excluir acontece no navegador, só quando o usuário
  clica em **Aplicar decisões na pasta** (com confirmação).
- Por enquanto só os arquivos do primeiro nível da pasta são listados. O
  domínio já aceita caminhos relativos (`sub/arquivo.jpg`) para evoluir.
- Segurança: senhas com hash (Werkzeug), cookie `HttpOnly` + `SameSite=Lax`,
  token CSRF em todas as requisições que alteram dados, cabeçalho CSP, e
  cada usuário só acessa as próprias sessões (resposta 404 caso contrário).
- A aplicação escuta apenas em `127.0.0.1`, pensada para uso local.

## Uso de IA (bônus)

> **Rascunho: o grupo deve ajustar este texto ao que realmente fez.**

Usamos o Claude (Anthropic) como apoio, não como substituto do raciocínio do
grupo:

- **Escopo e arquitetura:** o grupo definiu o tema, o requisito de login com
  persistência e a estrutura de pastas; a IA ajudou a mapear as camadas e a
  listar os casos de uso.
- **Geração de código:** a IA gerou a primeira versão das camadas e dos
  testes; o grupo revisou cada arquivo, rodou `pytest` e `flake8` e
  corrigiu o que não atendia aos critérios.
- **Verificação:** os testes dos casos de uso usam dublês em memória para
  provar que a regra de negócio não depende da infraestrutura.
- **Limites:** o que a IA sugeriu e o grupo recusou ou alterou deve ser
  listado aqui, com o motivo.
