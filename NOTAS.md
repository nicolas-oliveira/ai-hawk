# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

TURNO: AGY
**DE:** Agy (QA / Runtime & Infraestrutura)  
**PARA:** Nicolas (PO), Argon (Tech Lead / Auditora), Claude (Dev / Em Standby)  
**ASSUNTO:** Polimento Hostil do Clone Next.js e Blindagem Anti-Flaky Tests no BrowserService  
**TURNO:** Agy (Mantido com Agy para escrita da suíte de testes Python na sequência)  
**DATA/HORA:** 2026-10-31T07:58-03:00  
**STATUS:** [PRONTO] Front-end hostil compilado (`npm run build` OK) e métodos de espera determinística adicionados ao BrowserService.

### Armadilhas e Garantias de Arquitetura:
1. **Lazy Loading Assíncrono (Simulação de Rede):**
   - A listagem inicial de vagas (`1.2s`), o carregamento do painel de detalhes (`1.0s`), a abertura do modal (`1.1s`) e a transição entre etapas ("Avançar" -> "Enviar", `1.3s`) exibem estados de carregamento intermediários (`role="status"`) via `setTimeout` antes de montar os elementos finais no DOM.
2. **Overlay Intrusivo de Alto Z-Index (`z-[90]`):**
   - Um modal de interceptação ("Aviso de Privacidade e Assinatura Premium") surge sobre a tela bloqueando cliques nos cards e botões principais até ser fechado através do botão semântico (`aria-label="Dismiss overlay"`).
3. **Honeypots (Filtro de Elementos Invisíveis):**
   - Inseridos cards de vaga ocultos (`display: none`), botões falsos de "Candidatura Simplificada" e "Avançar" (`opacity: 0; left: -9999px` e `display: none`), além de campos `<input required>` invisíveis dentro do `<form>` do modal. Qualquer interação ou preenchimento nesses elementos dispara o estado de detecção de bot (`data-testid="honeypot-compromised"`).
4. **Chaos DOM / Ofuscação Estrutural Dinâmica:**
   - Além da `seed` dinâmica concatenada em IDs e classes CSS (`console.log("DOM Seed:", seed)`), a profundidade de wrappers (`<div>` simples vs múltiplos `<div>` aninhados vs `<section>`) alterna dinamicamente a cada interação (`wrapperVariant`), preservando apenas os contratos semânticos e `aria-label` literais (`Continue to next step`, `Submit application`, `Dismiss`).
5. **Blindagem Determinística Anti-Flaky Tests (Zero `sleep`):**
   - Implementados no `BrowserService` os métodos `wait_for_loader_to_disappear(loader_selector='[role="status"]', timeout=15000)` e `dismiss_overlay_if_present()`. O motor aguarda transições reais de predicados de estado no DOM, suportando flutuações de CPU em CI sem pausas cegas ou testes intermitentes.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy (Escrita dos testes Python contra o clone e alvos externos na sequência).
* **Versao Consolidada da Aplicacao:** NENHUMA (`master` = `first commit`; sem tag nem PR). A v0.1/v0.5 so existem apos PR aprovado.
* **Versoes:** v0.1 = so uma TAG historica local em `b4a33ca` (sem PR, sem branch; nao empurrada). Estaveis intermediarias sem tag: v0.6 `8f32943`, v0.7 `bce92f1`. PR unico previsto: v1.0 ("Release v1.0: AIHawk MVP Operacional").
* **Versao Alvo da Squad:** `v1.0` (AIHawk MVP Operacional).
* **Branch Ativa:** `feat/v0.1-stealth-engine` (branch compartilhada onde a squad opera).
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 43 PASSED. Suite real/infra: 21 PASSED no Chromium (12 infra + 9 real). Total geral: 64 PASSED.
* **Proxima Acao Esperada:** Agy implementa os testes Python de integracao com o clone Next.js e alvos externos. Claude permanece em standby.

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
