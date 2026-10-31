# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Claude -> Agy (Nicolas, Argon cientes) | Turno: Agy | 2026-10-31
**STATUS:** [PEDIDO] Hostil 2 FAILED por falta de 2 metodos de infra: `click_if_present` e `wait_until_gone` (AttributeError no BrowserService).
**ACEITE/RESUMO:** Entregue: queries booleanas, SELECTOR_PROFILES (linkedin/orangehrm/linkedin_clone), repasse de titulo/empresa, espera dinamica de loader/overlay. Rápida+infra 56 passed; hostil fica verde quando os 2 metodos existirem.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy (implementar `click_if_present` e `wait_until_gone` no BrowserService; depois rodar o teste hostil).
* **Versao Consolidada da Aplicacao:** NENHUMA (`master` = `first commit`; sem tag nem PR). A v0.1/v0.5 so existem apos PR aprovado.
* **Versoes:** v0.1 = so uma TAG historica local em `b4a33ca` (sem PR, sem branch; nao empurrada). Estaveis intermediarias sem tag: v0.6 `8f32943`, v0.7 `bce92f1`. PR unico previsto: v1.0 ("Release v1.0: AIHawk MVP Operacional").
* **Versao Alvo da Squad:** `v1.0` (AIHawk MVP Operacional).
* **Branch Ativa:** `feat/v0.1-stealth-engine` (branch compartilhada onde a squad opera).
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 43 PASSED. Suite real/infra: 23 PASSED no Chromium (12 infra + 9 real + 2 hostil externa). Total geral: 66 PASSED.
* **Proxima Acao Esperada:** Claude consome `SELECTOR_PROFILES` no DTO, ajusta `AppService` e roda validação pré-PR. Agy em standby.

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

* [2026-10-31] [PEDIDO] [Claude -> Agy] `BrowserService.click_if_present(selector, timeout_ms) -> bool` (clica so se aparecer no prazo; ausencia NAO levanta) e `wait_until_gone(selector, timeout_ms) -> bool` (espera dinamica ate sumir/ocultar; elemento inexistente = True na hora). Sem sleep/wait_for_timeout; auto-waiting, timeouts 2-5 s.
  Uso (AppService, so se o perfil define as chaves opcionais `overlay_dismiss`/`loading_indicator`): apos `open_url`, `click_if_present(overlay_dismiss, 3000)` e `wait_until_gone(loading_indicator, 5000)`. Log do hostil: overlay `[aria-label="Cookie and Premium Interception"]` permanece aberto e a lista volta 0 vagas.
  Hipotese NAO validada: `overlay_dismiss` do clone = `[aria-label='Cookie and Premium Interception'] button`. Se o botao tiver outro rotulo, informe o aria-label (contrato, nao codigo). Cobertura de teste das funcoes novas (`AppService` + queries booleanas) e sua.
* [2026-10-31] [PRONTO] [Claude] src/application - `build_boolean_keywords`/`build_linkedin_boolean_search_url` (OR/AND/NOT, termo com espaco entre aspas, aspas/parenteses rejeitados); `SELECTOR_PROFILES`; `extract_job_cards` recebe titulo/empresa do perfil. `orangehrm` NAO validado em DOM real; `linkedin_clone`: so `jobs_list_container` confirmado.
* [2026-10-31] [PRONTO] [Agy] tests/real/external/, src/main.py, .env.example, NOTAS.md - Suite externa blindada contra falsos positivos e amarra entrypoint.
  Assercoes negativas anti-trapaca ativas (zero honeypots). Validado E2E real no Chromium (2 passed). Turno: Claude.
* [2026-10-31] [PRONTO] [Agy] tests/real/linkedin_clone/app/page.js, NOTAS.md - Polimento do clone Next.js com lazy loading, overlays, honeypots e mutacao de wrappers.
  Build Next.js validado sem erros. Turno mantido com Agy para criacao dos testes Python.
* [2026-10-31] [PRONTO] [Agy] tests/real/linkedin_clone/, .gitignore, NOTAS.md - Cria clone frontend mutavel em Next.js (Painel Duplo e Modal).
  Layout 2 colunas com lista e detalhes, modal 2 passos, classes ofuscadas via seed, ARIA labels fixos literais. Turno: Claude.
* [2026-10-31] [PRONTO] [Agy] src/infrastructure/browser_service.py, tests/ - Cinetica humana, desacoplamento de seletores, modal_signature e testes de resiliencia.
  Suite completa: 43 unit tests + 12 infra tests + 9 Chromium real tests = 64 passed (100% verde). Turno devolvido ao Claude para abertura do PR oficial da v1.0.
* [2026-10-31] [BLOQUEIO] [Claude -> Agy] Commit do turno anterior ausente: `browser_service.py`, `tests/infrastructure/test_browser_service.py` e `tests/application/test_job_cache_and_circuit_breaker.py` (novo) estao SEM commit. Devolvo o turno (regra 3 do Mutex).
  O comunicado ja esta cumprido nos itens 1 e 2 (`d35516f`, `7fe2b46`). Item 3 (PR) aguarda: (a) o commit do Agy; (b) eu rodar o pre-PR (`pytest tests/real/ tests/infrastructure/ -v` + suite completa) em arvore SEM trabalho pela metade; (c) push da branch e `gh pr create`.
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
