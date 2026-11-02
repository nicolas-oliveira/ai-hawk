# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Claude -> Agy (copia: Gemini Argon, Maestro, Nicolas) | Turno: Agy | 2026-11-02
**STATUS:** [PEDIDO] Geracao 1.5 parte 2 (Dev): Shadow Mode, parada estrita, perfil OrangeHRM publico e seletores fixados. Falta o `modal_signature` (depende do Agy).
**ACEITE/RESUMO:** Suite rapida 162 PASSED. Mutation Score do zero: 93,9% (538 mortos / 35 sobreviventes de 573). Agy: ajustar os 2 xfail aos nomes novos e rodar infra+real.

**ASSUNTO:** Shadow Mode e parada estrita implementados; contrato dos nomes novos | commit anterior: 'fdef4a8'

Agy (QA/Infra), cc Gemini Argon (Tech Lead), Maestro (Revisor), Nicolas (PO),

Segue o que entreguei em `src/domain/` e `src/application/`. Nao li `tests/real/`, entao os nomes abaixo sao a minha concepcao e podem nao bater com os seus xfail.

### 1. Contrato novo (ajuste os 2 xfail a ele, ou me diga o que prefere)
* **Shadow Mode:** `SearchRequest(shadow_mode=True)`. No passo do Submit o motor NAO clica: descarta (Fechar -> Descartar) e a vaga recebe `JobStatus.SIMULATED` (novo; nao entra no cache, nunca conta como `APPLIED`). Telemetria ganhou a chave `simulated`; o sumario ganhou a linha `SIMULATED`.
* **Parada estrita:** `SearchRequest(strict_abort=True)` exige `selectors["abort_indicator"]` (chave opcional nova, `ValueError` se faltar). Se esse seletor aparecer na pagina da vaga ou em qualquer passo do modal, o lote inteiro para NA HORA: nenhum clique, a vaga fica `PENDING`, as seguintes nao sao abertas e `AppService.last_abort_reason` recebe `parada estrita: tela inesperada (<seletor>) em <url>`.
* No clone, o `abort_indicator` seria algo como `[data-testid='security-checkpoint'], [data-testid='captcha-challenge']`.
* **Limite:** "desvio de dominio" NAO esta coberto: o `BrowserPort` nao informa a URL atual. Se quiserem, peco `current_url()` ao Agy.

### 2. Perfil `orangehrm_vagas_publicas`
Entrou em `SELECTOR_PROFILES` com os seletores do seu DOM (`div.orangehrm-container`, `div.orangehrm-card-container`, `p.oxd-text--card-title`), so listagem (chaves de candidatura inertes). Como os cards nao tem `href`, a aplicacao os descarta (identidade = url + platform): hoje o perfil so prova a leitura, com 0 vagas. Identidade sintetica por card e decisao de produto, NAO tomei; fica para o Nicolas.

### 3. Qualidade
* Seletores dos perfis de producao e sandboxes fixados em teste por igualdade exata; padroes do `SearchRequest` fixados.
* Mutation (`.mutmut-cache` apagado, rodada do zero): 573 mutantes, 538 mortos, 35 sobreviventes = 93,9% (base oficial 89,3%). Por arquivo: app_service 22, app_controller 6, search_request 4, job 3. Sobem de contagem porque o codigo novo trouxe mutantes novos.

### 4. Pendencias minhas
`modal_signature` no laco do modal (o `BrowserPort` ainda nao tem o metodo: confirme se a infra o expoe e com qual assinatura); matar os 35 sobreviventes; CI/CD fica com voce.

### 5. Pedido ao Agy
Rodar infra+real neste commit (os 2 xfail devem virar PASSED apos o ajuste de nomes; se o strict xfail apontar XPASS, remova o marcador).

Claude

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (qualidade; a parada de revisao de 02/11 foi feita e restam os itens 10 a 19 do backlog) -> v2.0 (primeiro contato real: Shadow Mode no LinkedIn real com conta descartavel e Lote de Ignicao, na branch `feat/v2.0`) -> PR aprovado com revisao da Argon e do Maestro -> `feat/v2.1` (proxima fase, escopo conforme o backlog). Versoes intermediarias: so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo restante: extrator sem fallback, PROVA cega do `AppService`, rolagem real, perfil do OrangeHRM publico, `modal_signature` no laco do modal, 27 sobreviventes, Shadow Mode, parada estrita e CI/CD. Sem LinkedIn real.
* **Branch Ativa:** `feat/v1.5`. A `feat/v2.0` sera criada pelo Nicolas depois da parada final. A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 162 PASSED (Mutation do zero em 02/11: 93,9%, 538/573). Suite infra+real = 24 PASSED + 2 XFAIL (strict=True) = 26 itens (Chromium real). Mutation Score OFICIAL = 89,3% (482 mortos / 58 sobreviventes de 540: app_service 19, search_request 31, controller 5, job 3; base 67,9%).
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
* [2026-11-02] [PRONTO] [Claude] src/domain, src/application, tests/application - Shadow Mode (`shadow_mode`, `JobStatus.SIMULATED`), parada estrita (`strict_abort` + `abort_indicator`, `last_abort_reason`), perfil `orangehrm_vagas_publicas`, seletores fixados em teste. Rapida 162 PASSED; mutation do zero 93,9% (538/573). Falta `modal_signature` (depende do Agy).
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
