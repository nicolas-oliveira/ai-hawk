# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Agy -> Claude (copia: Gemini Argon, Maestro, Nicolas) | Turno: Claude | 2026-11-02
**STATUS:** [PRONTO] Mar aberto: TREINO 2 alvos (2 passaram); PROVA 4 alvos (4 passaram); infra+real 30 PASSED.
**ACEITE/RESUMO:** Achado de realidade no motor (scroll em `body` nao rolava a janela) corrigido por mim em `browser_service.py`. Claude: ajustar perfis de seletores com base no TREINO abaixo e atacar os 58 sobreviventes de `app_service.py`.

**ASSUNTO:** Validacao em mar aberto: TREINO e contagem da PROVA | commit anterior: '6e12372'

Claude (Dev), cc Gemini Argon (Tech Lead), Maestro (Revisor), Nicolas (PO),

1. Capacidades do motor: nenhuma assinatura mudou. `scroll_container` agora tambem rola a janela quando o alvo e `body`/`html` (antes, so rolava containers com overflow). Garantia: container interno continua igual.

2. TREINO (sandboxes publicos, somente leitura, sem login e sem envio):
- books.toscrape.com (listagem paginada). Cenario: pagina de catalogo com cartoes. DOM observado: 20 cartoes `article.product_pod` por pagina, titulo e link em `h3 a`, links 100% unicos, sem conceito de empresa (so preco). Esperado: extrair 20 URLs unicas, sem duplicar, sem inventar empresa.
- quotes.toscrape.com/scroll (scroll infinito na janela). Cenario: lazy loading que so dispara com rolagem do documento. DOM observado: 10 itens `div.quote` iniciais; apos rolagens sobem para 90; os itens nao tem link proprio. Esperado: a aplicacao rola ate o fim, conta itens novos e para quando a contagem estabiliza, sem travar e sem depender de container interno.

3. PROVA: 4 alvos, 4 passaram, 0 falharam (lista so em arquivo dentro de `tests/real/external/`). Cobre cartoes/links unicos em lista AJAX, tabela paginada sem link falso, overlay modal intrusivo e carregamento dinamico com loader.

4. Placar: `tests/domain` + `tests/application` 113 PASSED (nao rodei de novo, `src/` intocado fora da infra); infra+real 30 PASSED em 183 s (inclui os 6 de mar aberto).

5. Realidade crua para a aplicacao: a vida real nao tem os seletores LinkedIn. Perfis precisam aceitar listas sem empresa, itens sem link proprio e rolagem de janela. A aplicacao deve se comportar sem dar erro nesses casos e sem tratar ausencia de empresa como falha. Como codificar e com os 58 sobreviventes de `app_service.py` e com voce.
---

## 1. Estado Atual da Squad

* **Turno Atual:** Claude (perfis de seletores + 58 sobreviventes de `app_service.py`). Nicolas so entra nas paradas (v1.5 e v2.0) ou em `[BLOQUEIO]`.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (retomada: Nicolas revisa negocio e planejamento contra o que foi construido) -> v2.0 (entrega com PR). Versoes intermediarias (v1.1 a v1.4): so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo: mutation testing (Score > 80% na suite rapida) + validacao em mar aberto (sandboxes publicos sem WAF). Burner Run no LinkedIn real e bonus stealth ficam para depois da v1.5; o Burner Run so com o "vai" do Nicolas.
* **Branch Ativa:** `feat/v1.5` (criada a partir de `origin/master`). A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 113 PASSED. Suite infra+real homologada pelo QA = 30 PASSED (Chromium real, 183 s; inclui 6 de mar aberto). Mutation Score = 81,2% (415 mortos / 96 sobreviventes; base 67,9%).
* **Proxima Acao Esperada:** Claude ajusta os perfis de seletores com base no TREINO e ataca os 58 sobreviventes de `app_service.py` (restam tambem 30 em `search_request.py`: seletores literais). So Nicolas faz: push, tag, PR, trocar de branch.

---

## 2. Regras de Governanca e Etiquetas do NOTAS.md

1. **Leitura Obrigatoria do Topo:** Cada agente deve ler o e-mail ativo no topo e o Estado Atual antes de qualquer acao.
2. **Regra do Topo Vivo:** o topo comeca SEMPRE com 3 linhas fixas, lidas por script: (1) DE / PARA / TURNO + data; (2) STATUS (PRONTO | BLOQUEIO | PEDIDO); (3) ACEITE / RESUMO TECNICO. Logo ABAIXO delas vem a carta do turno para o proximo agente (formato da secao 7 do GEMINI.md: ASSUNTO, commit anterior, corpo). Nunca escreva nada acima das 3 linhas. Excecao: quando o turno vai para o Nicolas, a carta completa vai no chat (no NOTAS.md, so as 3 linhas e o Historico).
   Commit OBRIGATORIO entre turnos: as 3 linhas e a carta anteriores sao substituidas pelas novas (o git guarda o historico). Um resumo de ate 5 linhas vai para o Historico.
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
   - Prefixos de commit obrigatorios: `[Agy] ...` ou `[Claude] ...` (sem versao na mensagem).
   - Agentes NAO fazem push, tag, PR, troca de branch nem reescrita de historico (`rebase`, `--amend`, `filter-branch`, `--no-verify`). So o Nicolas.

---

## 3. Papeis e Territorios de Escrita

| Papel | Agente | Territorio Permitido de Escrita |
|---|---|---|
| Decisor / Merge PR / Tag / Push | Nicolas | `master` (PR manual via GitHub), `.claude/`, `.gemini/`, `scripts/maestro/` |
| DEV (Arquitetura e Contratos) | Claude | `src/domain/`, `src/application/`, `tests/domain/`, `tests/application/`, `NOTAS.md` |
| QA, Runtime e Infraestrutura | Antigravity (Agy) | `src/infrastructure/`, `src/main.py`, `tests/infrastructure/`, `tests/real/`, `tests/conftest.py`, `Makefile`, `requirements.txt`, configs de ferramentas na raiz, `.env*`, `.gitignore`, `NOTAS.md` |
| Auditoria e Revisao | Argon | Somente leitura |

---

## 4. Historico de Handoffs
* [2026-11-02] [PEDIDO] [Nicolas -> Agy] tests/real/external/, NOTAS.md - Fase 2 (meta v1.5): mar aberto SOMENTE em sandboxes publicos de automacao (sem LinkedIn/Gupy, sem conta real, sem login, sem envio real). TREINO descrito na carta do NOTAS.md (cenario, DOM observado, comportamento esperado, sem codigo de teste); PROVA listada so em `tests/real/external/`, no NOTAS so a contagem. Aceite: suite externa executada sob essas restricoes + carta para o Claude + commit + `Turno: Claude` (que na sequencia ataca os 58 sobreviventes de `app_service.py`).
* [2026-11-02] [PRONTO] [Agy] NOTAS.md - 'f77acb0': mutation score homologado com `make mutation` do zero (cache apagado): 81,2% (415 mortos / 96 sobreviventes de 511). Rapida 113 PASSED; infra+real 24 PASSED (Chromium, 151 s). `src/` limpo, sem `.bak`. Turno: Nicolas (parada v1.5).
* [2026-11-02] [PRONTO] [Claude] tests/domain, tests/application - mutation score 67,9% -> 81,2% (415/511). Novos: `test_app_controller_telemetry.py`, `test_job_validation_and_urls.py`, `test_search_request_messages.py` (mensagens exatas, telemetria, arquivo corrompido, falha de I/O, whitelist de URL).
  Sobraram 96: 58 em `app_service.py`, 30 em `search_request.py` (valores literais dos perfis de seletores), 5 no controller, 3 no job (constantes/decoradores, em parte equivalentes). `src/` nao alterado.
* [2026-11-02] [PRONTO] [Agy] Makefile, setup.cfg, requirements.txt, .gitignore, NOTAS.md - Setup de mutation testing com mutmut==2.5.1; make mutation roda ponta a ponta; score base registrado (347 mortos / 164 sobreviventes = 67.9%); src/ 100% limpo; Turno: Claude.
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