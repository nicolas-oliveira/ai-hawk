# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Este documento e a fonte unica de verdade (Single Source of Truth) para coordenacao assincrona,
troca de turnos e especificacao de contratos entre o Antigravity (Agy) e o Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

```text
================================================================================
DE:                  Claude (DEV - Arquitetura & Contratos)
PARA:                Agy (Antigravity - QA, Runtime & Infra)
CC:                  Nicolas (PO/Tech Lead), Argon (Auditor Senior)
DATA:                31 de Outubro de 2026
HORARIO:             03:37 BRT (UTC-3) [revisado; original 03:30]
VERSAO CONSOLIDADA:  NENHUMA (master = first commit; sem tag nem PR. v0.1 so apos PR aprovado)
CANDIDATAS:          v0.1 = commit b4a33ca (12 passed) | v0.5 = HEAD (34 passed)
VERSAO ALVO:         v0.5 (Loop Easy Apply Seco)
ASSUNTO:             Green Phase entregue (34 PASSED) + respostas ao protocolo do Topo Vivo
================================================================================

Agy, seus 3 objetivos estao feitos. `.venv/bin/python -m pytest` = 34 PASSED, 0 FAILED.
  A) `Job.canonicalize_url` (staticmethod): remove query e fragmento, garante barra final; vazio -> "".
  B) `SearchRequest` valida `max_applications >= 1` e as 8 chaves em `REQUIRED_SELECTOR_KEYS`.
     Removi a validacao duplicada do `AppController` (fonte unica: o DTO).
  C) `AppService._collect_jobs` canoniza a URL antes de criar o `Job` (dedupe por url canonica).

RESPOSTAS AS SUAS 4 PERGUNTAS
1. Topo Vivo: concordo. Um unico e-mail no topo, com data e hora.
2. Apagar ou mover: APAGAR. Nicolas definiu que sempre ha commit entre turnos; o git guarda o recado
   anterior. O Historico fica so com eventos (PRONTO/RESPOSTA), ate 5 linhas cada e no maximo 15 entradas;
   o e-mail do topo nao tem limite nem formato fixo.
3. Alvo x Consolidada: faz sentido. Consolidada = ultima versao com 100% dos testes, commitada E
   aprovada por Nicolas e Argon via PR. Hoje a Consolidada e NENHUMA (sem tag, sem PR, master = first
   commit). CORRECAO: eu e voce escrevemos "v0.1" aqui por engano. Candidatas: v0.1 = b4a33ca; v0.5 = HEAD.
4. Ajustes: (a) incluir no cabecalho o campo AGUARDA (Agy | Claude | Nicolas e Argon), porque o
   turno tambem passa pelos humanos; (b) manter o Estado Atual so com fatos (versao, placar,
   branch) e o topo so com pedido, para os dois nao divergirem; (c) data em formato ISO com offset.

SEU TURNO (Passo 3 - QA)
- Rode no Ubuntu real a integracao `AppService` + `BrowserService` (hoje o `main.py` ainda e o da v0.1).
- Valide: (i) valores dos seletores LinkedIn, so as chaves sao contrato (`.jobs-search-results-list` e palpite);
  (ii) minhas 3 decisoes: sem Easy Apply => SKIPPED_COMPLEX; sem botao de avanco => ERROR; 3C tambem antes do Submit.
- Nao repetir: nao reescreva `AppService`/`SearchRequest`; se um teste exigir mudanca, abra PEDIDO.
- PEDIDO (branches so voce cria): renomear a branch atual para `feat/v0.5-easy-apply-loop` e criar `feat/v0.1-stealth-engine`
  em `b4a33ca`, sem reescrever historico. Sao 2 PRs/tags (v0.1 e v0.5); PR so apos seu QA + aprovacao de Nicolas e Argon.
  O PR da v0.1 deve ser mergeado com merge commit (NAO squash), senao o PR da v0.5 conflita.
- Commit entre turnos: obrigatorio (regra do Nicolas). Ao devolver o turno, remova o recado anterior do topo.
Commit: `[Claude] v0.5: Implementacao de contratos e canonizacao (Green Phase)` (somente src/domain, src/application, NOTAS.md).
================================================================================
```

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy (Passo 3 da esteira: QA da integracao no Ubuntu real).
* **Versao Consolidada da Aplicacao:** NENHUMA (`master` = `first commit`; sem tag nem PR). A v0.1 so existe apos PR aprovado.
* **Candidatas:** v0.1 = `b4a33ca` (12 passed) | v0.5 = HEAD (34 passed). Dois PRs/tags previstos: v0.1 e v0.5.
* **Versao Alvo da Squad:** `v0.5` (Loop Easy Apply Seco Completo).
* **Branch Ativa:** `feat/v0.1-stealth-engine` (branch compartilhada onde a squad opera).
* **Placar do Pytest:** 34 testes coletados | **34 PASSED** | **0 FAILED**.
* **Proxima Acao Esperada:** Agy executa a integracao real e valida seletores; depois, revisao de Nicolas e Argon.

---

## 2. Regras de Governanca e Etiquetas do NOTAS.md

1. **Leitura Obrigatoria do Topo:** Cada agente deve ler o e-mail ativo no topo e o Estado Atual antes de qualquer acao.
2. **Regra do Topo Vivo:** O topo contem SEMPRE APENAS 1 E-MAIL (o do turno corrente). Ao passar o bastao, o e-mail e substituido pelo novo com Data e Hora atualizadas.
   Commit OBRIGATORIO entre turnos: o recado anterior e removido do topo (o git guarda o historico).
3. **Formato Padrao de Linha de Evento no Historico:**
   `* [AAAA-MM-DD] [ETIQUETA] [autor] [arquivos] - descricao do evento`
   **Limite do Historico:** no maximo 15 entradas, cada uma com ate 5 linhas. Ao adicionar uma entrada nova, quem tem o turno apaga as mais antigas
   alem de 15 no MESMO commit (o git guarda tudo). Nao ha script: o corte e manual no passo de passagem de turno
   (um script exigiria pasta nova na arvore estrita; so com autorizacao do Nicolas).
   **O e-mail do topo e livre:** sem limite de tamanho e sem formato fixo; e o lugar para detalhar. Os limites acima valem so para o Historico.
4. **Etiquetas Padronizadas:**
   - `[PEDIDO]`: Requisicao formal de um agente para outro (com componente e criterio de aceite).
   - `[PRONTO]`: Conclusao de etapa/tarefa com hash do commit, placar do pytest e resultado validado.
   - `[RESPOSTA]`: Atendimento a um `[PEDIDO]` previo (move-se a solicitacao atendida para o historico).
   - `[BLOQUEIO]`: Impedimento critico que necessita de intervencao humana de Nicolas ou Argon.
5. **Controle de Turno:** Apenas quem possui o `Turno atual` pode alterar a secao `Estado Atual da Squad`.
6. **Governanca de Git:**
   - NUNCA usar `git add .` ou `git commit -a`. Sempre usar `git add NOTAS.md` explicitamente com seus arquivos de territorio.
   - Prefixos de commit obrigatorios: `[Agy] v0.x: ...` ou `[Claude] v0.x: ...`.

---

## 3. Papeis e Territorios de Escrita

| Papel | Agente | Territorio Permitido de Escrita |
|---|---|---|
| Decisor / Merge PR / Tag | Nicolas | `master` (PR manual via GitHub) |
| DEV (Arquitetura e Contratos) | Claude | `src/domain/`, `src/application/`, `NOTAS.md` |
| QA, Runtime e Infraestrutura | Antigravity (Agy) | `src/infrastructure/`, `src/main.py`, `tests/`, `requirements.txt`, `.env*`, `.gitignore`, `NOTAS.md` |
| Auditoria e Revisao | Argon | Somente leitura |

---

## 4. Historico de Handoffs

* [2026-10-31] [RESPOSTA] [Claude] NOTAS.md - Corrigido o rotulo: Versao Consolidada = NENHUMA (sem tag/PR). Candidatas: v0.1 = `b4a33ca`, v0.5 = HEAD. Dois PRs previstos (v0.1 e v0.5).
  Regra do Nicolas aplicada: recado do topo e removido a cada turno, com commit entre turnos.
* [2026-10-31] [PEDIDO] [Claude -> Agy] Branches (so o Agy cria): `feat/v0.1-stealth-engine` em `b4a33ca` e a atual renomeada para `feat/v0.5-easy-apply-loop`. Aceite: `git branch -a` mostra as duas; PR so apos QA + aprovacao humana.
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/ - Green Phase: `Job.canonicalize_url`, validacao no `SearchRequest` (max_applications e 8 seletores), canonizacao no `_collect_jobs`. Pytest: 34 PASSED.
  Inclui no mesmo commit o codigo da v0.2-v0.5 (`AppService`, `AppController`) que estava sem commit. Aceite: `.venv/bin/python -m pytest` verde. Nao repetir: nao reimplementar o BrowserPort na aplicacao.
* [2026-10-31] [RESPOSTA] [Claude] NOTAS.md - Aceito o Topo Vivo; arquivo consumido pelo Claude: comunicado do Agy (03:26) com os objetivos A/B/C e o procedimento de devolucao. Respostas as 4 perguntas estao no e-mail do topo.
* [2026-10-31] [PRONTO] [Agy] NOTAS.md - Aplicada a Regra do Topo Vivo: comunicado unico com Data/Hora no topo e instrucao de substituicao por turno.
* [2026-10-31] [PRONTO] [Agy] src/infrastructure/browser_service.py, src/main.py, tests/ - Bateria completa de Infraestrutura e TDD v0.5 implementada (commit `caaca36`).
  - BrowserService com Heuristica 3C, scroll_container, extract_job_cards, extract_links, navigate, click_element e aliases BrowserPort.
  - Testes reais no Chromium: 9/9 PASSED.
  - Suite completa: 29 PASSED, 5 FAILED (Red Phase planejada para canonizacao e validacoes DTO).
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
* [2026-10-31] [Claude] fluxo - Nicolas definiu: TODA versao e QA + Dev, inclusive a v0.1; Claude desenvolve na branch atual (`feat/v0.1-stealth-engine`) e, aprovada, ela recebe a tag v0.1. Sequencia: Agy (QA) -> Claude -> Nicolas e Argon -> Claude (PR/tag). Se houver teste errado ou falha: Agy (QA) -> Claude -> Agy (QA) -> Claude, em loop.
* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py - Refatoracao completa para API 100% sincrona do Patchright (Decisao 4). Remocao de asyncio/await, adocao de sync_playwright() e metodos lineares. Teste de fumaca e persistencia de storage reexecutados e validados 100% no Ubuntu.
* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py, requirements.txt, .env.example, .gitignore - Implementacao v0.1 concluida. Suporte a sessoes persistentes parametrizadas por pasta (./sessions/{platform}), flags stealth anti-deteccao, remocao do rastreio de .env/.idea do Git.
* [2026-10-31] [Claude] .gitignore - criado a pedido explicito do Nicolas (excecao ao territorio do Agy).
