# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Este documento e a fonte unica de verdade (Single Source of Truth) para coordenacao assincrona,
troca de turnos e especificacao de contratos entre o Antigravity (Agy) e o Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

```text
================================================================================
DE:        Agy (Antigravity - QA, Runtime & Infra)
PARA:      Claude (DEV - Arquitetura & Contratos)
CC:        Nicolas (PO/Tech Lead), Argon (Auditor Senior)
DATA:      31 de Outubro de 2026
HORARIO:   03:25:00 BRT (UTC-3)
VERSAO:    v0.5 (Loop Easy Apply Seco Completo)
ASSUNTO:   Protocolo Oficial do NOTAS.md e Especificacao Tecnica da v0.5
================================================================================

Claude, recebemos ordem direta de Nicolas e Argon para operarmos de forma 100% autonoma
ate a entrega final da v0.5, sem tags Git intermediarias.

1. REGRA DO TOPO VIVO DO NOTAS.MD (INNEGOCIAVEL):
- O topo contem SEMPRE APENAS 1 E-MAIL: o comunicado ativo do agente que detem o turno.
- Quando voce concluir sua parte e for passar o bastao de volta para mim:
  Substitua este e-mail do topo pelo seu novo e-mail fresco de retorno,
  obrigatoriamente informando no cabecalho: DIA, MES, ANO e HORARIO exato.
- Se quiser arquivar o texto anterior, mova-o para a secao de historico ao final.
- O topo NUNCA pode acumular mensagens antigas ou obsoletas.

2. INFRAESTRUTURA V0.5 IMPLEMENTADA (Commit caaca36):
`src/infrastructure/browser_service.py` e `tests/conftest.py` implementam 100% síncrono:
- navigate(url, timeout) [alias: open_url]
- scroll_container(container_selector, steps, delay)
- scroll_container_to_end(container_selector, steps, delay)
- extract_links(card_selector, link_selector) -> List[str]
- extract_job_cards(card_selector) -> List[Dict[str, str]] (url, title, company)
- has_empty_required_inputs(modal_selector) -> bool (Heuristica 3C com DOM real)
- click_element(selector, timeout) [alias: click]
- is_visible(selector, timeout) [alias: element_exists]

3. STATUS DA SUITE PYTEST (.venv/bin/python -m pytest):
Total: 34 testes coletados | 29 PASSED | 5 FAILED (Red Phase planejada).
- Infraestrutura real no Chromium do Ubuntu: 9/9 PASSED (100% GREEN).
- Loop Easy Apply Seco: 7/7 PASSED (100% GREEN).

4. SEUS 3 OBJETIVOS EXCLUSIVOS (Passo 2 - Green Phase) PARA ZERAR AS 5 FALHAS:
A) Em `src/domain/entities/job.py`:
   - Implementar `Job.canonicalize_url(raw_url: str) -> str` (metodo estatico/classmethod)
     removendo query strings (?refId=...&trackingId=...&utm_source=...), fragmentos (#...)
     e garantindo barra no final (ex: 'https://www.linkedin.com/jobs/view/123/').
B) Em `src/application/dtos/search_request.py`:
   - Validar em `__post_init__` que `max_applications >= 1` (ValueError se < 1).
   - Validar em `selectors` a presenca das 8 chaves obrigatorias:
     `jobs_list_container`, `job_card`, `apply_button`, `next_button`, `submit_button`,
     `close_button`, `discard_button`, `modal_container` (ValueError se alguma faltar).
C) Em `src/application/app_service.py`:
   - Na coleta de vagas (`_collect_jobs`), aplicar `Job.canonicalize_url(url)` antes
     de instanciar a entidade `Job`.

5. PROCEDIMENTO DE DEVOLUCAO DE TURNO (HANDOFF PARA O AGY):
- Rode `.venv/bin/python -m pytest` ate confirmar 34 PASSED.
- Atualize a Secao 1 (Estado Atual) mudando "Turno Atual" para "Agy".
- Substitua este e-mail do topo pelo seu e-mail de conclusao (com data/hora atualizados).
- Comite apenas seus arquivos (src/domain/, src/application/ e NOTAS.md) com o prefixo:
  `[Claude] v0.5: Implementacao de contratos e canonizacao (Green Phase)`
================================================================================
```

---

## 1. Estado Atual da Squad

* **Turno Atual:** Claude (Passo 2 da esteira autonoma para v0.5 - Green Phase).
* **Versao em Andamento:** v0.5 (Loop Easy Apply Seco Completo - salto direto sem tags intermediarias).
* **Branch Ativa:** `feat/v0.1-stealth-engine` (branch compartilhada onde a squad opera).
* **Placar do Pytest:** 34 testes coletados | **29 PASSED** | **5 FAILED** (Red Phase planejada).
* **Proxima Acao Esperada:** Claude realizar os 3 ajustes de dominio/aplicacao para zerar os 5 testes e alcancar 100% GREEN.

---

## 2. Regras de Governanca e Etiquetas do NOTAS.md

1. **Leitura Obrigatoria do Topo:** Cada agente deve ler o e-mail ativo no topo e o Estado Atual antes de qualquer acao.
2. **Regra do Topo Vivo:** O topo contem SEMPRE APENAS 1 E-MAIL (o do turno corrente). Ao passar o bastao, o e-mail e substituido pelo novo com Data e Hora atualizadas.
3. **Formato Padrao de Linha de Evento no Historico:**
   `* [AAAA-MM-DD] [ETIQUETA] [autor] [arquivos] - descricao do evento`
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
* [2026-10-31] [Claude] CLAUDE.md - esteira TDD/QA-first (QA -> Dev -> QA -> PR) aplicada por comunicado do Argon repassado pelo Nicolas.
* [2026-10-31] [Argon] AGENTS.md, CLAUDE.md, GEMINI.md - Nova esteira oficial de trabalho TDD/QA-First estabelecida (QA -> Dev -> QA -> PR).
* [2026-10-31] [Agy] GEMINI.md, AGENTS.md, NOTAS.md - Protocolo do Argon consolidado em toda a documentacao. Branch unica `feat/v0.1-stealth-engine`, proibicao estrita de `git add .`, turnos sequenciais e Chromium stealth aprovados.
* [2026-10-31] [Claude] CLAUDE.md, AGENTS.md - protocolo definitivo de git aplicado por ordem do Argon repassada pelo Nicolas.
* [2026-10-31] [Claude] src/ - a pedido do Nicolas, diretorios movidos para `src/`.
* [2026-10-31] [Claude] AGENTS.md - secao 6 ajustada (tag pos-merge), secoes 7 e 8 adicionadas.
* [2026-10-31] [Agy] - alinhamento de papeis, comunicacao via NOTAS.md e fluxo de merge aprovados.
