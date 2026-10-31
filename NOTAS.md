# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Formato: `[AAAA-MM-DD] [autor] [arquivo] - evento`. Uma linha por evento, mais recente no topo de cada secao.

## Papeis

| Papel | Agente | Territorio de escrita |
|---|---|---|
| Decisor / merge / tag | Nicolas | `master` (PR manual) |
| DEV (arquitetura e contratos) | Claude | `src/domain/`, `src/application/` |
| QA e infraestrutura | Antigravity (Agy) | `src/infrastructure/`, `src/main.py`, `requirements.txt`, `.env` |
| Revisao | Argon | somente leitura |

## Ambiente

* Ubuntu 24.04.5 LTS (noble)
* Python 3.14.4 - Patchright 1.63.0 com Chromium e headless shell 1243: VERIFICADO E FUNCIONAL

## Estado atual

* Versao em andamento: v0.1 (Fundacao e Engine Stealth) - Concluida por Agy, pronta para Revisao Humana (Passo 5).
* Branch ativa: `feat/v0.1-stealth-engine` (criada a partir da `master`).
* Repositorio: Git ativo.

## Pedidos pendentes

* (nenhum)

## Historico

* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py - Refatoracao completa para API 100% sincrona do Patchright (Decisao 4). Remocao de asyncio/await, adocao de sync_playwright() e metodos lineares. Teste de fumaca e persistencia de storage reexecutados e validados 100% no Ubuntu.
* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py, requirements.txt, .env.example, .gitignore - Implementacao v0.1 concluida. Suporte a sessoes persistentes parametrizadas por pasta (./sessions/{platform}), flags stealth anti-deteccao, remocao do rastreio de .env/.idea do Git. Testes de persistencia de localStorage e ciclo de vida validados 100% no Ubuntu.
* [2026-10-31] [Agy] NOTAS.md - Plano de testes da v0.1 registrado e executado: (1) criacao e checkout de feat/v0.1-stealth-engine; (2) instalacao e teste do Patchright Chromium; (3) isolamento de sessoes persistentes; (4) teste de bootstrap e cleanup via `python -m src.main`.

* [2026-10-31] [Claude] .gitignore - criado a pedido explicito do Nicolas (excecao ao territorio do Agy). Cobre `.env`, `.venv/`, `sessions/`, `.cache/`, caches Python e IDE. NAO commitado: o `git add .gitignore` e do Agy. Agy: acrescentar entradas dos seus arquivos de teste. Pendente tambem: `git rm --cached .env` (o `.env` esta versionado) e `git rm -r --cached .idea` (5 arquivos versionados; ignorar nao basta).
* [2026-10-31] [Claude] CLAUDE.md - esteira TDD/QA-first (QA -> Dev -> QA -> PR) aplicada por comunicado do Argon repassado pelo Nicolas. A secao 7 estava DUPLICADA no CLAUDE.md (a minha e uma copia do Agy, ambas com o fluxo antigo); unifiquei em uma so, alinhada ao AGENTS.md. Backup do arquivo anterior no scratchpad da sessao. Agy: ao abrir a v0.1, registre aqui o plano de testes; eu leio antes de escrever qualquer codigo de `domain/` ou `application/`.
* [2026-10-31] [Argon] AGENTS.md, CLAUDE.md, GEMINI.md - Nova esteira oficial de trabalho TDD/QA-First estabelecida (QA -> Dev -> QA -> PR). Agy planeja testes e cria branch compartilhada -> Claude desenvolve para passar os testes -> Agy valida no Ubuntu -> Loop de correcoes seletivo -> Revisao humana (Nicolas/Argon) -> Claude cria PR, aguarda merge e cria tag estavel.
* [2026-10-31] [Agy] GEMINI.md, AGENTS.md, NOTAS.md - Protocolo do Argon consolidado em toda a documentacao. Branch unica `feat/v0.1-stealth-engine`, proibicao estrita de `git add .`, turnos sequenciais e Chromium stealth aprovados.
* [2026-10-31] [Claude] CLAUDE.md, AGENTS.md - protocolo definitivo de git aplicado por ordem do Argon repassada pelo Nicolas: secao 7 criada no CLAUDE.md, secao 6 do AGENTS.md alinhada (tag so apos merge, por Claude ou Nicolas). Agy: criar `feat/v0.1-stealth-engine` a partir da `master` antes de commitar; `.gitignore` e `.env.example` ainda pendentes (o `.env` esta versionado no first commit).
* [2026-10-31] [Claude] src/ - a pedido do Nicolas, `application/`, `domain/`, `infrastructure/` e `main.py` foram movidos da raiz para `src/` (so os caminhos mudaram, conteudo intacto). Agy: executar a partir da raiz com `python -m src.main` e conferir se os imports funcionam sem `src/__init__.py`.
* [2026-10-31] [Claude] AGENTS.md - secao 6 ajustada (tag pos-merge), secoes 7 e 8 adicionadas, com aprovacao do Agy.
* [2026-10-31] [Agy] - alinhamento de papeis, comunicacao via NOTAS.md e fluxo de merge aprovados.
