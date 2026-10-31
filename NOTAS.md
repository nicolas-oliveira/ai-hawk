# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Este documento e a fonte unica de verdade (Single Source of Truth) para coordenacao assincrona,
troca de turnos e especificacao de contratos entre o Antigravity (Agy) e o Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

```text
================================================================================
DE:                  Agy (Antigravity - QA, Runtime & Infra)
PARA:                Claude (DEV), Nicolas (Tech Lead), Argon (Auditor Senior)
DATA:                2026-10-31T03:52:00-03:00
VERSAO CONSOLIDADA:  NENHUMA (aguardando PR/merge na master)
CANDIDATAS:          v0.1 = b4a33ca (12 passed) | v0.5 = HEAD (41 passed)
VERSAO ALVO:         v0.5 (Loop Easy Apply Seco Completo)
AGUARDA:             Nicolas e Argon (Passo 5 - Revisao Humana da squad para aprovacao de PR)
ASSUNTO:             Passo 3 (QA Real) CONCLUIDO: 41 PASSED (7 testes reais no Chromium do Ubuntu)
================================================================================

Claude, Nicolas e Argon:

Missao de QA da Realidade Crua (Passo 3) CONCLUIDA com Skin in the Game absoluto!
Criei a suite `tests/real/` com servidor HTTP local embutido e testes de ponta a ponta
da aplicacao (`AppService` + `BrowserService`) rodando direto no Chromium real do Patchright.

RESULTADO DA SUITE COMPLETA (.venv/bin/python -m pytest):
============================= 41 passed in 20.23s =============================
- tests/application/ (DTOs e orquestracao rapida): 17 PASSED
- tests/domain/ (Entidade Job e canonizacao): 8 PASSED
- tests/infrastructure/ (Engine síncrona no Chromium): 9 PASSED
- tests/real/ (Integracao Real E2E no Chromium do Patchright sem mocks): 7 PASSED
  1. `test_real_lazy_loading_and_deduplication`: Container com overflow rola fisicamente, dispara
     evento JS de scroll real, anexa novos cards dinamicamente e canoniza todas as 5 vagas.
  2. `test_real_job_101_direct_submission`: Formulario direto submete e marca APPLIED.
  3. `test_real_job_102_css_trap_anti_ban`: Campo obrigatorio com display:none (trap/honeypot) e ignorado
     pela Heuristica 3C (`checkVisibility`), evitando falso-positivo e submetendo como APPLIED.
  4. `test_real_job_103_complex_modal_discards_cleanly`: Campo obrigatorio visivel vazio detectado pela 3C,
     clica em Close, confirma no popup real de descarte e marca SKIPPED_COMPLEX.
  5. `test_real_job_104_multi_step_submission`: Avanco real de etapas no DOM e submissao como APPLIED.
  6. `test_real_job_105_external_redirect_skipped_complex`: Vaga externa sem Easy Apply tratada como SKIPPED_COMPLEX.
  7. `test_real_full_orchestration_with_max_applications_ceiling`: Loop completo atinge o teto max_applications=2
     e encerra imediatamente sem tocar nas vagas restantes.

AJUSTE REAL FEITO NA INFRAESTRUTURA:
- Em `BrowserService.scroll_container`, adicionado `el.dispatchEvent(new Event('scroll', { bubbles: true }))`
  para garantir que o motor Blink do Chromium emita o evento de scroll para os listeners JS das plataformas.

STATUS: Codigo 100% blindado contra a realidade do navegador no Ubuntu 24.04.
AGUARDA: Revisao Humana (Nicolas e Argon - Passo 5 da Esteira).
Apos a aprovacao humana, o Claude assume o Passo 6 (fechamento, PRs e criacao das tags).
================================================================================
```

---

## 1. Estado Atual da Squad

* **Turno Atual:** Nicolas e Argon (Passo 5 da esteira: Revisao Humana e Aprovacao de PR).
* **Versao Consolidada da Aplicacao:** NENHUMA (`master` = `first commit`; sem tag nem PR). A v0.1 so existe apos PR aprovado.
* **Candidatas:** v0.1 = `b4a33ca` (12 passed) | v0.5 = HEAD (41 passed). Dois PRs/tags previstos: v0.1 e v0.5.
* **Versao Alvo da Squad:** `v0.5` (Loop Easy Apply Seco Completo).
* **Branch Ativa:** `feat/v0.1-stealth-engine` (branch compartilhada onde a squad opera).
* **Placar do Pytest:** 41 testes coletados | **41 PASSED** | **0 FAILED** (20.23s).
* **Proxima Acao Esperada:** Nicolas e Argon realizam a revisao humana; Claude assume o Passo 6 (PR e Tags).

---

## 2. Regras de Governanca e Etiquetas do NOTAS.md

1. **Leitura Obrigatoria do Topo:** Cada agente deve ler o e-mail ativo no topo e o Estado Atual antes de qualquer acao.
2. **Regra do Topo Vivo:** O topo contem SEMPRE APENAS 1 E-MAIL (o do turno corrente). Ao passar o bastao, o e-mail e substituido pelo novo com Data e Hora atualizadas.
   Commit OBRIGATORIO entre turnos: o recado anterior e removido do topo (o git guarda o historico).
3. **Formato Padrao de Linha de Evento no Historico:**
   `* [AAAA-MM-DD] [ETIQUETA] [autor] [arquivos] - descricao do evento`
   **Limite do Historico (automatico):** teto de 15 entradas, minimo de 10, cada uma com ate 5 linhas. Um hook de pre-commit
   (`.git/hooks/pre-commit`, local e NAO versionado) poda sozinho em todo commit que inclua o `NOTAS.md`: acima de 15 entradas,
   mantem so as 10 mais recentes. NUNCA toca no e-mail do topo nem em nada acima do Historico; em duvida ou erro nao faz nada e
   nao bloqueia o commit. O git guarda as entradas removidas. Se o repositorio for clonado de novo, o hook precisa ser reinstalado.
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

* [2026-10-31] [PRONTO] [Agy] tests/real/, src/infrastructure/browser_service.py - Passo 3 (QA Real) concluido. Criada suite de Realidade Crua (7 testes no Chromium real sem mocks). Total: 41 passed.
* [2026-10-31] [PRONTO] [Agy] GEMINI.md - Formalizada a Missao Magna (Guardiao Incorruptivel da Realidade & Anti-Ban).
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py, src/application/app_service.py, src/application/app_controller.py - Green Phase v0.5 entregue (`2567bf3`). Job.canonicalize_url, validacoes no SearchRequest, deduplicacao na listagem. Placar: 34 passed.
* [2026-10-31] [PRONTO] [Agy] NOTAS.md - Formalizada a Regra do Topo Vivo e e-mails de especificacao com timestamp completo.
* [2026-10-31] [PRONTO] [Agy] src/infrastructure/browser_service.py, src/main.py, tests/ - Bateria completa de Infraestrutura e TDD v0.5 implementada (commit `caaca36`). 29 passed.
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py - ajuste por exigencias do PO/Tech Lead (`b4a33ca`, 12 passed).
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py - Passo 2 / Green Phase (`2e1eddd`): Job e SearchRequest.
* [2026-10-31] [PRONTO] [Agy] tests/, requirements.txt, GEMINI.md, NOTAS.md - Aplicada a Diretriz Global de Shift-Left Testing (conftest e espelhamento).
* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py - Refatoracao completa para API 100% sincrona do Patchright (Decisao 4).
