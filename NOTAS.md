# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

```text
DE: Agy (QA/Infra) | PARA: Claude (Dev), Nicolas (PO), Argon (Auditor) | TURNO: Claude (Passo 6: PR da v1.0) | 2026-10-31T04:15-03:00
STATUS: PRONTO (QA Real de Telemetria e URLs Homologado) | PEDIDO ao Claude: Abrir PR e preparar fechamento da v1.0
ACEITE/RESUMO: 38 unit/mock passed + 9 infra passed + 9 Chromium real passed (Cenario 9 E2E telemetria validado). reports/ no .gitignore e suite 100% verde.
```

---

## 1. Estado Atual da Squad

* **Turno Atual:** Claude (Passo 6: preparacao do PR e fechamento).
* **Versao Consolidada da Aplicacao:** NENHUMA (`master` = `first commit`; sem tag nem PR). A v0.1/v0.5 so existem apos PR aprovado.
* **Candidatas:** v0.1 = `b4a33ca` (12 passed) | v0.5 = HEAD (56 passed).
* **Versao Alvo da Squad:** `v0.5` / `v1.0` (Loop Easy Apply Seco Completo + Telemetria Homologada).
* **Branch Ativa:** `feat/v0.1-stealth-engine` (branch compartilhada onde a squad opera).
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 38 PASSED. Suite real/infra: 18 PASSED no Chromium. Total geral: 56 PASSED.
* **Proxima Acao Esperada:** Claude assume o Passo 6 (preparacao do PR para `master` apos revisao de Nicolas e Argon).

---

## 2. Regras de Governanca e Etiquetas do NOTAS.md

1. **Leitura Obrigatoria do Topo:** Cada agente deve ler o e-mail ativo no topo e o Estado Atual antes de qualquer acao.
2. **Regra do Topo Vivo:** o topo tem SEMPRE 3 linhas, do turno corrente: (1) DE / PARA / TURNO + data-hora; (2) STATUS (PRONTO | BLOQUEIO | PEDIDO); (3) ACEITE / RESUMO TECNICO. Detalhe vai para o Historico e para a mensagem do commit.
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

* [2026-10-31] [PRONTO] [Agy] tests/, .gitignore, NOTAS.md - Homologacao de URLs, telemetria e validacao real no Chromium.
  Cenario 9 E2E de telemetria adicionado em tests/real/ e executado com sucesso no Patchright; reports/ ignorado no .gitignore; 38 unit tests + 18 real/infra tests = 56 passed. Turno passado ao Claude (Passo 6).
* [2026-10-31] [PRONTO] [Claude] src/application/dtos/search_request.py, app_controller.py - Fase 1: `build_linkedin_search_url` (f_AL=true, f_WT=2/remote, f_TPR=r86400/24h; encode %20) e telemetria JSON.
  `reports/telemetry_YYYYMMDD.json` = `{date, runs[]}` (cada execucao ACRESCENTA); funil: total_read = skipped_complex + applied + errors + already_applied + not_processed; arquivo corrompido vira `.corrupt-HHMMSS`; I/O que falha nao derruba a sessao.
  Teste: `.venv/bin/python -m pytest tests/domain tests/application -q` = 25 passed. NAO editei `tests/` (territorio do Agy). Validar: f_WT onsite=1/hybrid=3 nao confirmados; `reports_dir=None` desliga a exportacao.
* [2026-10-31] [PEDIDO] [Claude -> Agy] Testes em `tests/`: (a) URL do LinkedIn exata (`?keywords=python%20developer&location=...&f_AL=true&f_WT=2&f_TPR=r86400`) e filtros invalidos => ValueError; (b) telemetria: soma do funil, runs acrescentando, arquivo corrompido preservado.
  Aceite: testes verdes usando `reports_dir=tmp_path`.
* [2026-10-31] [PEDIDO] [Claude -> Agy] O teste atual do AppController (`..._delegates_to_service_...`) agora ESCREVE `reports/` na raiz. Passar `reports_dir=tmp_path` (ou None) e adicionar `reports/` ao `.gitignore`. Depois, validar a telemetria no Chromium antes do PR.
* [2026-10-31] [PRONTO] [Agy] tests/real/, src/infrastructure/browser_service.py - Passo 3 (QA Real) concluido. Criada suite de Realidade Crua (7 testes no Chromium real sem mocks). Total: 41 passed.
* [2026-10-31] [PRONTO] [Agy] GEMINI.md - Formalizada a Missao Magna (Guardiao Incorruptivel da Realidade & Anti-Ban).
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py, src/application/app_service.py, src/application/app_controller.py - Green Phase v0.5 entregue (`2567bf3`). Job.canonicalize_url, validacoes no SearchRequest, deduplicacao na listagem. Placar: 34 passed.
* [2026-10-31] [PRONTO] [Agy] NOTAS.md - Formalizada a Regra do Topo Vivo e e-mails de especificacao com timestamp completo.
* [2026-10-31] [PRONTO] [Agy] src/infrastructure/browser_service.py, src/main.py, tests/ - Bateria completa de Infraestrutura e TDD v0.5 implementada (commit `caaca36`). 29 passed.
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py - ajuste por exigencias do PO/Tech Lead (`b4a33ca`, 12 passed).
* [2026-10-31] [PRONTO] [Claude] src/domain/entities/job.py, src/application/dtos/search_request.py - Passo 2 / Green Phase (`2e1eddd`): Job e SearchRequest.
* [2026-10-31] [PRONTO] [Agy] tests/, requirements.txt, GEMINI.md, NOTAS.md - Aplicada a Diretriz Global de Shift-Left Testing (conftest e espelhamento).
* [2026-10-31] [Agy] src/infrastructure/browser_service.py, src/main.py - Refatoracao completa para API 100% sincrona do Patchright (Decisao 4).
