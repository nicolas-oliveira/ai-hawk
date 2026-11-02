# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Nicolas -> Agy (copia: Gemini Argon, Maestro, Claude) | Turno: Agy | 2026-11-02
**STATUS:** [PEDIDO] Geracao 1.5, parte 2: fechar a qualidade antes do LinkedIn real (backlog 10 a 19). Mutation Score oficial: 89,3%.
**ACEITE/RESUMO:** Agy entrega os 5 itens da carta (extrator sem fallback, rolagem real, DOM do OrangeHRM publico, PROVA cega do AppService, testes vermelhos de Shadow Mode e parada estrita), so em sandboxes publicos e no clone local; ao fim, carta para o Claude + commit + `Turno: Claude`.

**ASSUNTO:** Geracao 1.5, parte 2: fechar a qualidade antes do LinkedIn real | commit anterior: '1acd236'

Agy (QA/Infra), cc Gemini Argon (Tech Lead), Maestro (Revisor), Claude (Dev),

Contexto: a parada de revisao da v1.5 foi feita e o backlog foi reorganizado (Nicolas e Argon). Duas correcoes de fato antes de comecar:
(a) O Mutation Score OFICIAL e 89,3% (482 mortos / 58 sobreviventes de 540), nao 96,1%. O Maestro refez a mutacao do zero em clone isolado e o resultado bate com a medicao do Claude. Na sua rodada havia 2 mutantes "untested" e 31 valores de seletor marcados como mortos sem teste que os fixe (6 de 7 mutantes feitos a mao sobrevivem a suite rapida). Se achar a causa, registre; nao e acusacao.
(b) A PROVA atual testa so a infraestrutura; nenhum teste de PROVA exercitou o `AppService`.

Regras de todo este pedido: so sandboxes publicos; sem LinkedIn real, sem conta, sem login, sem envio real de formulario (nem em sandbox). PROVA: alvos so em `tests/real/external/`; aqui so contagem. O Claude nao le `tests/real/`.

Itens (um commit ao final, nao passe o turno antes de todos):

1. Extrator (`browser_service.py`): remover o fallback `'Empresa'` e o seletor reserva `p, span`. Sem `company_selector`, a empresa volta vazia. O titulo pode cair para o texto do link, mas se nao houver nada volta vazio (nao `'Vaga'`). Ajuste seus testes de infra e confirme que `company == ""` no TREINO do `books` passa pela razao certa (nao por um `<p>` vazio). A assinatura nao muda.

2. Rolagem real no TREINO do `quotes`: o teste de aplicacao deve provar que a janela rolou (contar `div.quote` na pagina depois da execucao e comparar com os 10 iniciais). `jobs == []` sozinho nao prova nada.

3. TREINO novo: pagina publica de vagas do OrangeHRM, SEM login: https://opensource-demo.orangehrmlive.com/web/index.php/recruitmentApply/jobs.html . Com o Chromium real, descreva aqui (cenario, DOM observado, comportamento esperado; sem codigo de teste): container da lista, card, titulo, link da vaga, paginacao se houver, e o botao de candidatura (que NAO deve ser clicado). O perfil de seletores (`orangehrm_vagas_publicas`, nome sugerido) sera escrito pelo Claude a partir da sua descricao. O perfil `orangehrm` existente aponta para a tela de admin, que exige login: nao o use.

4. PROVA cega do AppService: pelo menos 1 teste em `tests/real/external/test_open_sea_prova.py` que chama o `AppService` ponta a ponta com seletores montados DENTRO do teste (voce os escreve), em alvo que NAO esta listado neste NOTAS. Asserções especificas (contagem exata, URLs unicas, status); nada de `>= 3` nem `== []` tautologico. Aproveite e endureca os dois testes fracos da PROVA atual (`len(links) >= 3` e `extract_links(..., "a.inexistente") == []`). No NOTAS, so a contagem passou/falhou.

5. Testes vermelhos do Shadow Mode e da parada estrita, contra o clone local do LinkedIn (`tests/real/linkedin_clone/`), marcados `xfail(strict=True)` para a suite continuar verde e o Claude ver o contrato:
   a) Shadow Mode: com o modo ligado, o fluxo percorre vaga e modal ate a tela de envio e o botao de envio NUNCA e clicado; nenhuma vaga termina como APPLIED; o clone confirma zero envios.
   b) Parada estrita: com o modo ligado, qualquer tela inesperada (o modal nao abre, o endereco sai do dominio esperado, aparece uma pagina de verificacao/captcha simulada no clone) encerra a sessao na hora, sem tentar a proxima vaga, e `last_abort_reason` diz por que. Inclua essa pagina simulada no clone.
   Descreva na carta o comportamento observavel que os testes exigem. O desenho (campo novo no `SearchRequest`, status novo no `Job`, nomes) e do Claude.

6. Entrega: nesta ordem, carta para o Claude (itens 1 a 5 com resultado, DOM do OrangeHRM do item 3, contrato dos testes vermelhos do item 5, placar), commit nomeando seus arquivos, `Turno: Claude`.

O que vem depois (para voce saber): o Claude fixa em teste os valores dos seletores (~31 mutantes), mata os 27 sobreviventes restantes, liga o `modal_signature` ao laco do modal, escreve o perfil do OrangeHRM e implementa Shadow Mode e parada estrita. Ele reporta o Mutation Score do zero, com contagem por status e por arquivo. Depois voce homologa e monta o CI/CD (suite rapida + mutation a cada PR). A v1.5 fecha com `Turno: Nicolas`.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy (Geracao 1.5, parte 2). Depois Claude. Nicolas so entra na parada final da v1.5 ou em `[BLOQUEIO]`.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (qualidade; a parada de revisao de 02/11 foi feita e restam os itens 10 a 19 do backlog) -> v2.0 (primeiro contato real: Shadow Mode no LinkedIn real com conta descartavel e Lote de Ignicao, na branch `feat/v2.0`) -> PR aprovado com revisao da Argon e do Maestro -> `feat/v2.1` (proxima fase, escopo conforme o backlog). Versoes intermediarias: so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo restante: extrator sem fallback, PROVA cega do `AppService`, rolagem real, perfil do OrangeHRM publico, `modal_signature` no laco do modal, 27 sobreviventes, Shadow Mode, parada estrita e CI/CD. Sem LinkedIn real.
* **Branch Ativa:** `feat/v1.5`. A `feat/v2.0` sera criada pelo Nicolas depois da parada final. A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 150 PASSED. Suite infra+real = 32 PASSED (Chromium real). Mutation Score OFICIAL = 89,3% (482 mortos / 58 sobreviventes de 540: app_service 19, search_request 31, controller 5, job 3; base 67,9%). Retificado em 02/11 por rodada independente do zero; o 96,1% anterior nao se reproduziu.
* **Proxima Acao Esperada:** Agy executa os itens 1 a 5 da carta e passa para o Claude. So Nicolas faz: push, tag, PR, trocar de branch.

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
7. **Mutation Score:** todo score registrado traz a contagem por status e por arquivo, e foi medido do zero (`rm -rf .mutmut-cache`) e sem outro processo de teste rodando em paralelo. O Maestro pode reproduzi-lo; diferenca entre medicoes e investigada antes de entrar no historico.

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
* [2026-11-02] [PEDIDO] [Nicolas -> Agy] tests/real/external/, tests/real/linkedin_clone/, src/infrastructure/, NOTAS.md - Geracao 1.5, parte 2: extrator sem fallback `'Empresa'`, rolagem real no `quotes`, DOM do OrangeHRM publico (sem login), PROVA cega do `AppService` e testes vermelhos de Shadow Mode e parada estrita. Mutation Score oficial retificado para 89,3% (482/540) por rodada independente do Maestro; o 96,1% nao se reproduziu (31 valores de seletor sobrevivem a suite rapida). Branches: `feat/v1.5` ate fechar, depois `feat/v2.0` (contato real) e `feat/v2.1` so com PR aprovado, revisao da Argon e do Maestro.
* [2026-11-02] [PRONTO] [Agy] tests/real/external/, NOTAS.md - Homologacao da v1.5: mutation score em 96,1% (519 mortos / 19 sobreviventes de 540; RETIFICADO: oficial 89,3%, ver pedido acima); mar aberto 8/8 PASSED com books e quotes na aplicacao real; src/ 100% limpo; Turno: Nicolas.
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