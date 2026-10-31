# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

```text
DE: Claude (Dev) | PARA: Agy (QA/Infra), Nicolas, Argon | TURNO: Agy (finalizar infra: seletores de titulo/empresa do card) | 2026-10-31T04:43-03:00
STATUS: PRONTO (ajuste fino de desacoplamento) + PEDIDO ao Agy | PR da v1.0 NAO aberto; plano de tags segue parado ate a infra fechar
ACEITE/RESUMO: commits d35516f (chaves opcionais `job_card_title`/`job_card_company`) e 7fe2b46 (`canonicalize_url` preserva id/jobId/gh_jid so se o path nao tem ID). `pytest tests/domain tests/application` = 38 passed; suite real NAO rodada.
```

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy (finalizar a infraestrutura: seletores de titulo/empresa vindos do dicionario).
* **Versao Consolidada da Aplicacao:** NENHUMA (`master` = `first commit`; sem tag nem PR). A v0.1/v0.5 so existem apos PR aprovado.
* **Versoes:** v0.1 = so uma TAG historica local em `b4a33ca` (sem PR, sem branch; nao empurrada). Estaveis intermediarias sem tag: v0.6 `8f32943`, v0.7 `bce92f1`. PR unico previsto: v1.0, depois da v0.9 e dos testes de borda.
* **Versao Alvo da Squad:** `v0.9` (app completa); depois, com testes de borda, `v1.0`.
* **Branch Ativa:** `feat/v0.1-stealth-engine` (branch compartilhada onde a squad opera).
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 38 PASSED. Suite real/infra: ultimo placar do Agy = 56 PASSED; o Claude so a roda no pre-PR.
* **Proxima Acao Esperada:** Agy escreve os testes da v0.6/v0.7 e o metodo `modal_signature` (v0.8); depois devolve o turno ao Claude. `CLAUDE.md` esta modificado SEM commit (nao e meu): Nicolas decide.

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

* [2026-10-31] [PRONTO] [Claude] src/application/dtos, src/domain - d35516f: `job_card_title` e `job_card_company` em `LINKEDIN_DEFAULT_SELECTORS` (OPCIONAIS, valores copiados do browser_service; sem chaves duplicadas, conferido por AST). 7fe2b46: `Job.canonicalize_url` mantem `id`/`jobId`/`gh_jid` so quando o path nao tem 6+ digitos.
  Verificacao: `pytest tests/domain tests/application` = 38 passed. Limite documentado: outros parametros de ID (ex.: `currentJobId` do LinkedIn em /collections/) exigem ampliar a whitelist na Fase 2.
* [2026-10-31] [PEDIDO] [Claude -> Agy] `BrowserService.extract_job_cards(card_selector, title_selector=None, company_selector=None)`: use os parametros no lugar dos seletores LinkedIn das linhas ~214 e ~217 (None = padrao generico). Compativel com a assinatura atual.
  Aceite: testes reais verdes. Quando voce devolver o turno, eu passo `sel.get("job_card_title")` e `sel.get("job_card_company")` no AppService (nao passei agora para nao quebrar a assinatura atual).
* [2026-10-31] [RESPOSTA] [Claude] Check-in Mutex: o ultimo commit era `f50a809` [Claude] (o Agy nao commitou no turno dele; a diretoria passou o turno direto). Arvore sem arquivo do Agy pendente (so `CLAUDE.md`, sem dono), entao nao devolvi com BLOQUEIO.
* [2026-10-31] [PRONTO] [Claude] src/domain, src/application - v0.6 `8f32943`: `JsonJobCache` (opt-in, `AppService(browser, cache=...)`); so APPLIED/SKIPPED_COMPLEX/ALREADY_APPLIED persistem (ERROR nao); vaga em cache nao reabre o card nem consome o teto.
  v0.7 `bce92f1`: `SearchRequest.max_consecutive_errors`=3 interrompe a sessao; telemetria ganha `aborted_reason` e `cache.hits` (fora do funil). Verificacao: scripts manuais + 38 passed; tests/real NAO rodado.
  Validar: APPLIED em cache vira ALREADY_APPLIED; `Job.from_cache`; o cache vem DESLIGADO (cache=None) para nao contaminar testes.
* [2026-10-31] [PEDIDO] [Claude -> Agy] Testes (`tests/`) da v0.6/v0.7: (a) `JsonJobCache`: ERROR fora do cache, arquivo corrompido preservado, vaga em cache nao consome `max_applications`; (b) freio: 3 ERROR seguidos interrompem, vaga ok no meio zera; `aborted_reason` no JSON.
  Decisao sua: ligar o `JsonJobCache(".cache/...")` no `main.py` (`.cache/` ja esta no .gitignore) e cobrir no E2E real.
* [2026-10-31] [PEDIDO] [Claude -> Agy] v0.8: expor no `BrowserService` `modal_signature(container_selector) -> str` (texto/hash do passo atual do modal). Eu uso para abortar e descartar se um clique em Next/Review nao mudar o passo (hoje o laco pode repetir ate 15 cliques).
  Plano: v0.8 = guarda de progresso do modal; v0.9 = app completa integrada (cache + freio ligados na CLI) com E2E real; v1.0 = v0.9 + testes de borda + PR unico.
* [2026-10-31] [BLOQUEIO] [Claude -> Nicolas] PR "Release v1.0" NAO aberto, por ordem sua. A tag `v0.1` NAO existia (git tag -l vazio): criei localmente em `b4a33ca`; empurrar ao GitHub so com seu OK.
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
