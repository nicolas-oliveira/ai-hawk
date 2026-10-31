# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Formato: `[AAAA-MM-DD] [ETIQUETA] [autor] [arquivo] - evento`. Mais recente no topo de cada secao.
Etiquetas: `PEDIDO` (pede algo, com dono e aceite), `PRONTO` (parte concluida), `BLOQUEIO` (precisa de decisao humana), `RESPOSTA` (atende um PEDIDO).
Regras: maximo 5 linhas por entrada (detalhe longo vai no commit). `PRONTO` traz: hash do commit, comando exato do pytest, criterio de aceite e "nao repetir".
Quem tem o "Turno atual" e o unico que altera "Estado atual". Quem atende um PEDIDO o move para o Historico com um RESPOSTA.
Cada agente le este arquivo no inicio de cada turno de trabalho. Entradas anteriores a estas regras podem ficar sem etiqueta.

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

* Turno atual: Claude (Passo 2 da esteira autônoma para v0.5).
* Versao em andamento: Salto direto para v0.5 (Loop Easy Apply Seco Completo) por ordem de Nicolas e Argon. Sem tags intermediarias.
* Branch ativa: `feat/v0.1-stealth-engine` (aguardando fechamento e tag v0.5 pelo Claude apos PR).
* Suite de testes: 34 testes totais (29 PASSED, 5 FAILED em Red Phase planejada). Infraestrutura 100% GREEN no Chromium real do Ubuntu.

## Pedidos pendentes

* (nenhum)

## Comunicado Especial: E-mail de Especificação Completa da v0.5 para o Claude

```text
Para: Claude
De: Agy (Antigravity)
Assunto: Especificacao Completa da Infraestrutura e Bateria TDD v0.5 (Loop Easy Apply Seco)

Claude, recebemos diretriz direta e inegociavel do Nicolas e da Gemini Argon:
Chega de microgerenciamento e tags intermediarias. Saltamos direto da v0.1 para o marco estavel v0.5.
Trabalharemos de forma autonoma entre nos dois para entregar o pacote completo.

1. INFRAESTRUTURA IMPLEMENTADA (100% Sincrona e Validada no Chromium Real do Ubuntu):
O `src/infrastructure/browser_service.py` e o `mock_browser_service` em `tests/conftest.py` implementam
integralmente tanto a interface canonica do AIHawk quanto o seu `BrowserPort`:
- `navigate(url: str, timeout: int = 30000)` [alias: `open_url`]
- `scroll_container(container_selector: str, steps: int = 5, delay: float = 0.5)`
- `scroll_container_to_end(container_selector: str, steps: int = 5, delay: float = 0.5)`
- `extract_links(card_selector: str, link_selector: str = "a") -> List[str]`
- `extract_job_cards(card_selector: str) -> List[Dict[str, str]]` (retorna dicts com url, title, company)
- `has_empty_required_inputs(modal_selector: str) -> bool` (Heuristica 3C estrita com DOM real)
- `click_element(selector: str, timeout: int = 5000)` [alias: `click`]
- `is_visible(selector: str, timeout: int = 3000)` [alias: `element_exists`]

2. RESULTADO ATUAL DA SUITE DE TESTES:
Comando: `.venv/bin/python -m pytest` -> 29 PASSED, 5 FAILED (Red Phase planejada).
Os 9 testes de infraestrutura e todos os 7 testes do Step C (Easy Apply Seco) ja estao passando!

3. O QUE FALTA PARA 100% VERDE (Seu territorio exclusivo em src/domain/ e src/application/):
Apenas 3 ajustes pontuais nos seus arquivos:
A) Em `src/domain/entities/job.py`:
   - Implementar o metodo `Job.canonicalize_url(raw_url: str) -> str` (estatico ou classmethod)
     que remove query params de tracking (?refId=...&trackingId=...&utm_source=...), fragmentos (#...)
     e normaliza com barra no final (ex: 'https://www.linkedin.com/jobs/view/123/').
B) Em `src/application/dtos/search_request.py`:
   - Validar em `__post_init__` que `max_applications >= 1` (lancar ValueError se < 1).
   - Validar a presenca das 8 chaves obrigatorias em `selectors`:
     `jobs_list_container`, `job_card`, `apply_button`, `next_button`, `submit_button`,
     `close_button`, `discard_button`, `modal_container` (lancar ValueError se alguma faltar).
C) Em `src/application/app_service.py`:
   - Na coleta de vagas (`_collect_jobs` / `extract_jobs`), aplicar `Job.canonicalize_url(url)`
     antes de instanciar a entidade `Job`, garantindo a deduplicacao correta no loop.

Assim que fizer esses 3 ajustes, todos os 34 testes ficarao 100% verdes!
```

## Historico

* [2026-10-31] [PRONTO] [Agy] src/infrastructure/browser_service.py, src/main.py, tests/ - Bateria completa de Infraestrutura e TDD v0.5 implementada (commit [Agy] v0.5).
  - BrowserService com Heuristica 3C, scroll_container, extract_job_cards, extract_links, navigate, click_element e aliases BrowserPort.
  - Testes reais no Chromium: 9/9 PASSED.
  - Suíte completa: 29 PASSED, 5 FAILED (Red Phase planejada para canonizacao e validacoes DTO).
* [2026-10-31] [RESPOSTA] [Agy] src/infrastructure/browser_service.py - Atendido PEDIDO do Claude: implementados todos os metodos do BrowserPort e adicionadas fixtures em tests/conftest.py.


* [2026-10-31] [PRONTO] [Claude] src/application/app_service.py, app_controller.py - v0.2-v0.5 escritas, NAO commitadas. Verificacao: script manual com navegador falso (8 cenarios) + `.venv/bin/python -m pytest` = 12 passed.
  `AppService.run` lista vagas, aplica regra 3C antes de Next/Review/Submit (campo vazio => Fechar->Descartar, SKIPPED_COMPLEX), blinda por card (ERROR). `AppController.execute` valida e gera o sumario.
  Validar: sem Easy Apply => SKIPPED_COMPLEX; sem botao de avanco => ERROR; 3C tambem antes do Submit. Nao repetir: nao reimplementar o BrowserPort na aplicacao.
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py - ajuste por exigencias do PO/Tech Lead (`b4a33ca`, 12 passed).
  `JobStatus` (StrEnum) com default PENDING; `timestamp` automatico; `max_applications` default 10; `LINKEDIN_DEFAULT_SELECTORS` com `jobs_list_container`. Ordem dos campos do `SearchRequest`: platform, static_urls, selectors, max_applications.
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py - Passo 2 / Green Phase (`2e1eddd`): `Job` (identidade por url+platform, valida url/platform/status) e `SearchRequest` (valida platform e static_urls).

* [2026-10-31] [Agy] tests/, requirements.txt, GEMINI.md, NOTAS.md - Aplicada a Diretriz Global de Shift-Left Testing (ordem de Gemini Argon):
  1) `tests/conftest.py` criado como fonte unica de fixtures, com `mock_browser_service` usando pytest-mock para que testes de aplicacao rodem em milissegundos sem acionar o Chromium.
  2) Estrutura espelhada:
     - `tests/infrastructure/test_browser_service.py` (4 testes passando 100% no Ubuntu).
     - `tests/domain/test_job.py` (5 testes em Red Phase planejada).
     - `tests/application/dtos/test_search_request.py` (3 testes em Red Phase planejada).
  3) Comandos de execucao para o Claude:
     - Dominio puro: `.venv/bin/python -m pytest tests/domain/ -v`
     - Aplicacao / DTOs: `.venv/bin/python -m pytest tests/application/ -v`
     - Infraestrutura real: `.venv/bin/python -m pytest tests/infrastructure/ -v`
     - Suite completa: `.venv/bin/python -m pytest`
  Bastao passado formalmente para o Claude (Green Phase em `src/domain/entities/job.py` e `src/application/dtos/search_request.py`).

* [2026-10-31] [RESPOSTA] [Claude] fluxo - Nicolas definiu: TODA versao e QA + Dev, inclusive a v0.1; Claude desenvolve na branch atual e, aprovada, ela recebe a tag v0.1.
  Normal: Agy (QA) -> Claude -> Nicolas e Argon -> Claude (PR/tag). Com falha: Agy -> Claude -> Agy -> Claude em loop. A excecao "na v0.1 o codigo e do Agy" (Passo 2) ainda consta em AGENTS.md/CLAUDE.md/GEMINI.md; correcao aguarda ordem do Nicolas.
* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py - Refatoracao completa para API 100% sincrona do Patchright (Decisao 4). Remocao de asyncio/await, adocao de sync_playwright() e metodos lineares. Teste de fumaca e persistencia de storage reexecutados e validados 100% no Ubuntu.
* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py, requirements.txt, .env.example, .gitignore - Implementacao v0.1 concluida. Suporte a sessoes persistentes parametrizadas por pasta (./sessions/{platform}), flags stealth anti-deteccao, remocao do rastreio de .env/.idea do Git. Testes de persistencia de localStorage e ciclo de vida validados 100% no Ubuntu.
* [2026-10-31] [Agy] NOTAS.md - Plano de testes da v0.1 registrado e executado: (1) criacao e checkout de feat/v0.1-stealth-engine; (2) instalacao e teste do Patchright Chromium; (3) isolamento de sessoes persistentes; (4) teste de bootstrap e cleanup via `python -m src.main`.

* [2026-10-31] [RESPOSTA] [Claude] .gitignore - criado a pedido do Nicolas (excecao ao territorio do Agy); o `git add .gitignore` e do Agy. Pendente do Agy: `git rm --cached .env` e `git rm -r --cached .idea`.
* [2026-10-31] [RESPOSTA] [Claude] CLAUDE.md - esteira TDD/QA-first aplicada por comunicado do Argon repassado pelo Nicolas; Secao 7 estava duplicada e foi unificada com o AGENTS.md. Backup no scratchpad da sessao.
* [2026-10-31] [Argon] AGENTS.md, CLAUDE.md, GEMINI.md - Nova esteira oficial de trabalho TDD/QA-First estabelecida (QA -> Dev -> QA -> PR). Agy planeja testes e cria branch compartilhada -> Claude desenvolve para passar os testes -> Agy valida no Ubuntu -> Loop de correcoes seletivo -> Revisao humana (Nicolas/Argon) -> Claude cria PR, aguarda merge e cria tag estavel.
* [2026-10-31] [Agy] GEMINI.md, AGENTS.md, NOTAS.md - Protocolo do Argon consolidado em toda a documentacao. Branch unica `feat/v0.1-stealth-engine`, proibicao estrita de `git add .`, turnos sequenciais e Chromium stealth aprovados.
* [2026-10-31] [RESPOSTA] [Claude] CLAUDE.md, AGENTS.md - protocolo de git aplicado por ordem do Argon repassada pelo Nicolas: Secao 7 no CLAUDE.md; Secao 6 do AGENTS.md alinhada (tag so apos o merge).
* [2026-10-31] [RESPOSTA] [Claude] src/ - a pedido do Nicolas, `application/`, `domain/`, `infrastructure/` e `main.py` foram movidos para `src/` (so caminhos). Rodar com `python -m src.main` a partir da raiz.
* [2026-10-31] [Claude] AGENTS.md - secao 6 ajustada (tag pos-merge), secoes 7 e 8 adicionadas, com aprovacao do Agy.
* [2026-10-31] [Agy] - alinhamento de papeis, comunicacao via NOTAS.md e fluxo de merge aprovados.
