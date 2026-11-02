# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Nicolas -> Agy | Turno: Agy | 2026-11-02
**STATUS:** [PEDIDO] Fase 2 (meta v1.5): preparar mutation testing (`mutmut`) na suite rapida.
**ACEITE/RESUMO:** Mutar so `src/domain` e `src/application`, rodando so `tests/domain` e `tests/application` (nunca `tests/real`). Usar `mutmut==2.5.1` ja instalado pelo Nicolas (o 3.x nao funciona com imports `src.`). Criar `setup.cfg` e `make mutation`, por `.mutmut-cache` no `.gitignore`, registrar o score base (mortos/sobreviventes) sem ler codigo. Nunca interromper o mutmut com Ctrl+C (ele trava); se precisar, `kill -9` e `git restore src/`. Ao terminar: `git status --short src/` limpo e sem `.bak`; commit + `Turno: Claude`.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy (QA). Depois Claude (DEV). Nicolas so entra nas paradas (v1.5 e v2.0) ou em `[BLOQUEIO]`.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (retomada: Nicolas revisa negocio e planejamento contra o que foi construido) -> v2.0 (entrega com PR). Versoes intermediarias (v1.1 a v1.4): so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo: mutation testing (Score > 80% na suite rapida) + validacao em mar aberto (sandboxes publicos sem WAF). Burner Run no LinkedIn real e bonus stealth ficam para depois da v1.5; o Burner Run so com o "vai" do Nicolas.
* **Branch Ativa:** `feat/v1.5` (criada a partir de `origin/master`). A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 81 PASSED. Suite geral homologada pelo QA = 98 PASSED (inclui 2 hostil E2E no Chromium).
* **Proxima Acao Esperada:** Agy prepara o mutation testing (ver topo). Em seguida Claude sobe o score. So Nicolas faz: push, tag, PR, trocar de branch.

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
   - Commitar com caminhos explicitos: `git commit -m "..." -- <seus arquivos> NOTAS.md` (nao leva o que o outro agente deixou preparado).
   - Prefixos de commit obrigatorios: `[Agy] v1.x: ...` ou `[Claude] v1.x: ...`.
   - Agentes NAO fazem push, tag, PR, troca de branch nem reescrita de historico (`rebase`, `--amend`, `filter-branch`, `--no-verify`). So o Nicolas.

---

## 3. Papeis e Territorios de Escrita

| Papel | Agente | Territorio Permitido de Escrita |
|---|---|---|
| Decisor / Merge PR / Tag / Push | Nicolas | `master` (PR manual via GitHub), `.claude/`, `.gemini/`, `scripts/maestro/` |
| DEV (Arquitetura e Contratos) | Claude | `src/domain/`, `src/application/`, `tests/domain/`, `tests/application/`, `NOTAS.md` |
| QA, Runtime e Infraestrutura | Antigravity (Agy) | `src/infrastructure/`, `src/main.py`, `tests/infrastructure/`, `tests/real/`, `Makefile`, `requirements.txt`, configs de ferramentas na raiz, `.env*`, `.gitignore`, `NOTAS.md` |
| Auditoria e Revisao | Argon | Somente leitura |

---

## 4. Historico de Handoffs

* [2026-11-02] [PEDIDO] [Nicolas -> Agy] Makefile, requirements.txt, config na raiz - Fase 2 (meta v1.5): mutation testing com `mutmut` so em `src/domain` e `src/application`, rodando so `tests/domain` e `tests/application` (nunca `tests/real`: ~56 s por rodada inviabiliza rodar centenas de mutantes). Criar `make mutation` e registrar o score base.
  Aceite: `make mutation` roda ponta a ponta e o NOTAS traz killed/survived e o score. Instalar dependencia so com OK do Nicolas. Depois: `Turno: Claude`, que sobe o score para > 80% (testes e codigo do territorio dele).
* [2026-10-31] [PRONTO] [Claude] src/application, tests/application - Cronometro por chamada da aplicacao ao navegador ('e50e4e7'); log INFO "Tempo por chamada" (`pytest -s -o log_cli=true -o log_cli_level=INFO`).
  Teste 2 (34,4 s): 6 `element_exists` negativos = 18,5 s (overlay x3, submit x2, discard x1; ~3,1 s cada). Proposta de nao sondar overlay nas vagas (-8,8 s) VETADA pelo Agy: overlays tardios ocorrem em sites reais. Codigo mantido.

* [2026-10-31] [PRONTO] [Claude] src/application, tests/application - queries booleanas (`build_boolean_keywords`, `build_linkedin_boolean_search_url`), `SELECTOR_PROFILES` (linkedin, orangehrm, linkedin_clone), titulo/empresa repassados ao extrator, `_prepare_page` (loader + overlay, timeouts 5 s/3 s, sem sleep) usando metodos ja existentes da infra.
  Contrato usado no clone: `Dismiss overlay`, `[role='status']`, `Continue to next step`, `Submit application`, `Dismiss`; apply = texto "Candidatura Simplificada"/"Easy Apply" (HIPOTESE que passou). `orangehrm` e `discard_button`/`modal_container` do clone NAO validados. Hostil: 33.9 s + 20.3 s (ver entrada do cronometro acima).


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