# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Agy -> Claude (copia: Gemini Argon, Maestro, Nicolas) | Turno: Claude | 2026-11-02
**STATUS:** [PRONTO] Geracao 1.5, parte 2: motor sem fallback, rolagem provada, OrangeHRM mapeado, PROVA cega e testes vermelhos de Shadow/Parada.
**ACEITE/RESUMO:** Itens 1 a 5 entregues; PROVA: 5 alvos (5 passaram); suite infra+real verde (com 2 xfail estritos); src/ intocado fora da infra. Claude assume para implementar perfis e contratos.

**ASSUNTO:** Entrega Geracao 1.5 parte 2: extrator limpo, DOM OrangeHRM, PROVA cega e contratos de Shadow/Parada | commit anterior: '31e227b'

Claude (Dev), cc Gemini Argon (Tech Lead), Maestro (Revisor Consultor), Nicolas (PO),

Entrega concluida de todos os 5 itens da Geracao 1.5 (parte 2) nos termos de Shift-Left Testing e isolamento estrito de Caixa Preta. Nenhum arquivo comercial de `src/domain/` ou `src/application/` foi alterado.

### 1. Capacidades e Contratos Disponibilizados pela Infraestrutura

* **Extrator Desacoplado sem Fallback Sintetico (`browser_service.py`):**
  - Removido o fallback `'Empresa'` e o seletor reserva generico `p, span`.
  - Contrato: se `company_selector` for omitido/nulo/vazio, o campo `company` retorna string vazia `""`.
  - O campo `title` recorre ao texto visivel do link (`linkEl.innerText.trim()`) caso `title_selector` nao seja fornecido ou nao encontre elemento interno; se nenhum texto existir, retorna `""` (eliminado o fallback `'Vaga'`).
  - Assinatura mantida estritamente compativel com `BrowserPort`. Testes de infraestrutura e `books.toscrape` atualizados e validados com `company == ""`.

* **Rolagem Real Comprovada no Sandbox de Treino (`quotes.toscrape`):**
  - O teste de aplicacao em `test_open_sea_app_treino.py` agora verifica diretamente no DOM da pagina que a janela rolou efetivamente: `page.locator("div.quote").count() > 10` apos a execucao do `AppService`.

### 2. Mapeamento do DOM Real do OrangeHRM Publico (Sem Login)

Analise efetuada no Chromium real na URL publica: `https://opensource-demo.orangehrmlive.com/web/index.php/recruitmentApply/jobs.html`
* **Cenario:** Portal aberto de recrutamento sem autenticacao.
* **DOM Observado:**
  - Container da listagem: `div.orangehrm-container`
  - Cards de vagas: `div.orangehrm-card-container`
  - Titulo da vaga: `p.oxd-text--card-title`
  - Link da vaga: **Nao existem tags `<a>` nem atributos `href` nos cards de vagas.** A acao e puramente orientada a eventos via botao: `<button class="oxd-button--secondary">Apply</button>`.
  - Paginacao: Ausente (lista corrida em tela unica).
  - Fluxo de Candidatura: Ao clicar no botao `Apply`, a aplicacao dispara uma navegacao SPA interna para `/recruitmentApply/applyVacancy/id/{id}`, onde exibe formulario com multiplos campos obrigatorios (`input.orangehrm-firstname`, `input[name="lastName"]`, `input[name="email"]`, upload de curriculo) e `button[type="submit"]`.
* **Comportamento Ideal Esperado:** O perfil de seletores sugerido (`orangehrm_vagas_publicas`) deve refletir esses seletores para que a engine extraia o titulo via `p.oxd-text--card-title`. Note que como nao ha link estatico `<a>` no card, se a aplicacao exigir links href diretos, a estrategia de extracao devera tratar cards orientados a SPA ou identificadores sinteticos. Nao efetuar submissao real.

### 3. Placar da Suite de Testes

* **Testes Rapidos (`tests/domain` + `tests/application`):** 150 PASSED (0.14s).
* **Testes de Infraestrutura (`tests/infrastructure`):** 13 PASSED (7.13s).
* **Testes Reais no Chromium (`tests/real/external`):**
  - Hostil Clone Next.js: 2 PASSED
  - Sandboxes de Treino (`test_open_sea_app_treino.py` e `test_open_sea_treino.py`): 4 PASSED
  - Sandboxes de PROVA (`test_open_sea_prova.py`): 5 PASSED (5/5 alvos passaram, 0 falhas)
  - Contratos de Shadow Mode e Parada Estrita: 2 XFAIL (strict=True)
* **Placar Geral Infra + Real:** 24 PASSED + 2 XFAIL = 26 itens operacionais.

### 4. Cenarios de Estresse e Contratos Observaveis dos Testes Vermelhos

Em `tests/real/external/test_shadow_and_strict_abort.py`, deixamos 2 contratos rigorosos marcados como `@pytest.mark.xfail(strict=True)` para orientar a sua implementacao:

1. **Shadow Mode (Dry-Run de Seguranca):**
   - **Comportamento Observavel:** Quando configurado no modo Shadow/Dry-Run, o loop de execucao do `AppService` deve navegar pelas vagas e preencher/avancar nos passos do modal, mas o botao final de submissao (`submit_button`) NUNCA deve ser clicado.
   - **Garantias de Auditoria:** Nenhuma vaga pode receber o status `JobStatus.APPLIED` (devem ser marcadas com status de simulacao ou descarte seguro); o `sessionStorage` e o backend do clone confirmam exatamente 0 submissoes (`modal_submission_success` nulo).
2. **Parada Estrita (Strict Abort):**
   - **Comportamento Observavel:** Quando o modo de parada estrita estiver ativado, caso a engine depare com uma tela inesperada, desvio de dominio ou desafio de seguranca (ex: rota simulada `/checkpoint` com `data-testid="security-checkpoint"` ou `data-testid="captcha-challenge"` adicionada no clone), o motor DEVE abortar imediatamente o lote inteiro.
   - **Garantias de Auditoria:** O processamento para na hora sem tentar as vagas seguintes; a sessao registra o motivo do encerramento (ex: `last_abort_reason` ou telemetria compativel).

O design comercial interno (novos campos no `SearchRequest`, enums no `JobStatus`, etc.) fica sob sua concepcao. A base esta 100% pronta para voce matar os mutantes sobreviventes e elevar a qualidade da engine.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Claude.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (qualidade; a parada de revisao de 02/11 foi feita e restam os itens 10 a 19 do backlog) -> v2.0 (primeiro contato real: Shadow Mode no LinkedIn real com conta descartavel e Lote de Ignicao, na branch `feat/v2.0`) -> PR aprovado com revisao da Argon e do Maestro -> `feat/v2.1` (proxima fase, escopo conforme o backlog). Versoes intermediarias: so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo restante: extrator sem fallback, PROVA cega do `AppService`, rolagem real, perfil do OrangeHRM publico, `modal_signature` no laco do modal, 27 sobreviventes, Shadow Mode, parada estrita e CI/CD. Sem LinkedIn real.
* **Branch Ativa:** `feat/v1.5`. A `feat/v2.0` sera criada pelo Nicolas depois da parada final. A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 150 PASSED. Suite infra+real = 24 PASSED + 2 XFAIL (strict=True) = 26 itens (Chromium real). Mutation Score OFICIAL = 89,3% (482 mortos / 58 sobreviventes de 540: app_service 19, search_request 31, controller 5, job 3; base 67,9%).
* **Proxima Acao Esperada:** Claude fixa seletores em teste, mata sobreviventes restantes, escreve perfil do OrangeHRM publico e implementa Shadow Mode e parada estrita para tornar os testes verdes. Push, PR e tag so o Claude executa, com a linha `AUTORIZO` do Nicolas no topo e confirmacao no terminal (regra 6). O merge do PR e a troca de branch: so o Nicolas.

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
   - Agentes NAO fazem troca de branch (so o Nicolas), merge de PR, force push, push direto na `master` nem reescrita de historico (`rebase`, `--amend`, `filter-branch`, `--no-verify`).
   - Push, PR e tag: so o Claude, depois da revisao aprovada, com a linha `AUTORIZO: ...` do Nicolas no topo do NOTAS.md e confirmacao dele no terminal. O Agy nunca. O hook `pre-push` recusa qualquer push para `master`/`main`.
7. **Mutation Score:** todo score registrado traz a contagem por status e por arquivo, e foi medido do zero (`rm -rf .mutmut-cache`) e sem outro processo de teste rodando em paralelo. O Maestro pode reproduzi-lo; diferenca entre medicoes e investigada antes de entrar no historico.

8. **Versao e tag:** a revisao acontece antes do PR. Revisao negada nao gera PR nem tag e nao consome versao: a versao segue em aberto e as correcoes entram na mesma branch, com a rodada registrada no Historico como `[RESPOSTA]`. A tag so e criada depois do merge. Correcao depois do merge usa versao de correcao (v1.5.1). O numero seguinte so existe depois do merge da anterior.

---

## 3. Papeis e Territorios de Escrita

| Papel | Agente | Territorio Permitido de Escrita |
|---|---|---|
| Decisor / Autorizacao / Merge do PR | Nicolas | `master` (PR manual via GitHub), `.claude/`, `.gemini/`, `scripts/maestro/` |
| DEV (Arquitetura e Contratos) | Claude | `src/domain/`, `src/application/`, `tests/domain/`, `tests/application/`, `NOTAS.md`; entrega Git (push, PR, tag) so com autorizacao |
| QA, Runtime e Infraestrutura | Antigravity (Agy) | `src/infrastructure/`, `src/main.py`, `tests/infrastructure/`, `tests/real/`, `tests/conftest.py`, `Makefile`, `requirements.txt`, configs de ferramentas na raiz, `.env*`, `.gitignore`, `NOTAS.md` |
| Auditoria e Revisao | Argon | Somente leitura |

---

## 4. Historico de Handoffs
* [2026-11-02] [PRONTO] [Agy] src/infrastructure/browser_service.py, tests/ - Geracao 1.5 parte 2 entregue: extrator sem fallback 'Empresa'/'Vaga', rolagem real no quotes comprovada (> 10 quotes), mapeamento DOM do OrangeHRM publico, PROVA cega (5/5 PASSED), testes vermelhos de Shadow Mode e parada estrita (2 xfail strict). Turno: Claude.
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
