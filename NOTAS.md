# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Nicolas -> Claude (copia: Gemini Argon, Maestro, Agy) | Turno: Claude | 2026-11-02
**STATUS:** [PEDIDO] Ponto estavel da v1.5 ainda NAO aprovado: ajustes da revisao do Maestro antes do PR. Mutation Score informado: 95,0%.
**ACEITE/RESUMO:** Claude commita o teste residual, fecha a parada estrita na listagem e corrige o fluxo da tag, e repassa ao Agy a lista de PROVA, testes reais e CI; o Agy homologa no commit exato e passa `Turno: Nicolas`.

**ASSUNTO:** Ajustes da revisao do Maestro antes do PR da v1.5 | commit anterior: 'd6732df'

Claude (Dev), cc Gemini Argon (Tech Lead), Maestro (Revisor), Agy (QA/Infra),

Contexto: o Maestro leu o seu pedido de aprovacao ('d6732df'). O avanco e real: mutation 89,3% -> 95,0%, rapida 174, infra+real 27/27 no commit '2db53a6'. Mesmo assim ainda nao aprovamos. O nome da versao segue v1.5 e a linha `AUTORIZO` so entra quando tudo abaixo fechar.

O que a revisao encontrou:

* O 'd6732df' nao contem o `test_mutantes_residuais.py` (esta staged). Os 174 testes e os 95,0% nao se reproduzem nesse hash.
* A parada estrita so checa o `abort_indicator` na pagina da vaga e no modal, nao na listagem. O teste real atual so passa porque o `/checkpoint` do clone tem um link para si mesmo.
* O contrato "nenhuma vaga subsequente" esta so no docstring do teste real, sem assercao.
* A PROVA perdeu o teste negativo da tabela, e o teste cego mede o teto (`max_applications=3`).
* O CI vai ficar verde sem testar nada.
* O seu pedido diz que voce cria a tag antes do PR; pela regra 8 a tag so existe depois do merge.

Regras deste pedido: so sandboxes publicos e o clone local, sem LinkedIn real. Cada um escreve so no seu territorio (regra 6).

Itens do Claude (um commit por entrega, nomeando os arquivos; nao passe o turno antes de todos):

1. Commite `tests/application/test_mutantes_residuais.py` como PRIMEIRO commit, nomeando so esse arquivo. Os numeros do pedido anterior so valem com ele.

2. Parada estrita na listagem: checar o `abort_indicator` logo apos navegar para cada URL de listagem, inclusive quando ela traz zero cards. Hoje um checkpoint na busca nao para o lote. Cubra com teste rapido (porta falsa).

3. Desvio de dominio: o Agy ja expos `get_current_url()` e `current_url` no `BrowserService`. Leve ao `BrowserPort`, use na parada estrita e cubra com teste rapido.

4. Corrija o fluxo da tag no seu pedido: Agy homologa, Nicolas escreve `AUTORIZO`, Claude faz push e abre o PR, Nicolas faz o merge, e so entao Claude cria a tag.

5. Reporte a Mutation Score do zero no commit exato (regra 7), por status e por arquivo, listando os sobreviventes por arquivo e dizendo quais sao texto de log ou decorador equivalente e quais nao. Entrega: carta para o Agy com a lista abaixo, commit nomeando seus arquivos, `Turno: Agy`.

O que vem depois (para voce repassar ao Agy na sua carta, descrevendo o comportamento esperado):

1. Teste real novo: pagina de checkpoint SEM link (rota nova no clone, sem depender de link para si mesma) como primeira URL da fila e a URL do clone como segunda. Esperado: zero vagas, `last_abort_reason` preenchido e a segunda URL nunca aberta.

2. No teste atual de parada estrita, afirmar que nenhuma vaga da segunda URL existe (`len(jobs) == 1`).

3. Restaurar `test_prova_tabela_paginada_nao_vira_link_falso` (seletor inexistente devolve lista vazia) e manter o de paginacao como teste adicional.

4. Teste cego do `AppService`: `max_applications` maior que a contagem da pagina (ex: 10), com `len(jobs)` igual a contagem real e `company == ""`.

5. CI (`.github/workflows/ci.yml`): criar a venv em `.venv` (o `setup.cfg` usa `.venv/bin/python`), tirar o `|| true`, catraca de sobreviventes (falha se passar do numero do placar do Claude), mesma versao de Python da venv, e confirmar que o `requirements.txt` traz `pytest` e `mutmut`.

6. Homologar infra+real no commit exato, sem tocar em `src/domain`, `src/application`, `tests/domain` nem `tests/application` (mostrar o `git diff --stat` na carta), e passar `Turno: Nicolas` com a carta pedindo a aprovacao final.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Claude.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (qualidade; a parada de revisao de 02/11 foi feita e restam os itens 10 a 19 do backlog) -> v2.0 (primeiro contato real: Shadow Mode no LinkedIn real com conta descartavel e Lote de Ignicao, na branch `feat/v2.0`) -> PR aprovado com revisao da Argon e do Maestro -> `feat/v2.1` (proxima fase, escopo conforme o backlog). Versoes intermediarias: so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo restante: homologacao final da v1.5 pela diretoria apos o fechamento pelo Claude. Sem LinkedIn real.
* **Branch Ativa:** `feat/v1.5`. A `feat/v2.0` sera criada pelo Nicolas depois da parada final. A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 174 PASSED (Mutation do zero em 02/11: 95,0%, 551/580). Suite infra+real = 27 PASSED (14 infra + 13 real Chromium). Total geral = 201 PASSED (0 falhas, 0 xfail).
* **Proxima Acao Esperada:** Claude comita `tests/application/test_mutantes_residuais.py` e redige o pedido formal de encerramento da v1.5 para a diretoria. Push, PR e tag so o Claude executa, com a linha `AUTORIZO` do Nicolas no topo e confirmacao no terminal (regra 6). O merge do PR e a troca de branch: so o Nicolas.

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
* [2026-11-02] [PEDIDO] [Diretoria -> Claude] NOTAS.md - Revisao do Maestro: v1.5 nao aprovada. Claude: commitar teste residual, parada estrita na listagem, current_url no BrowserPort, corrigir fluxo da tag. Agy depois: teste de checkpoint sem link, assercao da 2a URL, negativo da tabela, teste cego com contagem real, CI sem '|| true' com catraca, homologar no commit exato.
* [2026-11-02] [PEDIDO] [Claude] tests/application, NOTAS.md - Inclui `test_mutantes_residuais.py` (esquecido no commit anterior) e pede ao Nicolas/diretoria a aprovacao do ponto estavel da v1.5. Aguarda resposta antes de tag, push e PR.
* [2026-11-02] [PRONTO] [Agy] NOTAS.md - Homologacao de modal_signature no motor real: 27/27 Chromium PASSED (201/201 no total do repo); guarda de progresso aprovada sem falsos positivos; ponto estavel para fechamento da v1.5. Turno: Claude.
* [2026-11-02] [PEDIDO] [Claude] src/application, tests/application - `modal_signature` no BrowserPort e no laco do modal (guarda de progresso); mutation do zero 95,0% (551/580); rapida 174 PASSED. Pede infra+real ao Agy.
* [2026-11-02] [PRONTO] [Agy] src/infrastructure/, tests/, .github/ - Suite real 100% verde (27/27 Chromium PASSED): Shadow Mode (SIMULATED) e Parada Estrita validados; get_current_url exposto; modal_signature confirmado; CI/CD criado (.github/workflows/ci.yml). Turno: Claude.
* [2026-11-02] [PRONTO] [Claude] src/domain, src/application, tests/application - Shadow Mode (`shadow_mode`, `JobStatus.SIMULATED`), parada estrita (`strict_abort` + `abort_indicator`, `last_abort_reason`), perfil `orangehrm_vagas_publicas`, seletores fixados em teste. Rapida 162 PASSED; mutation do zero 93,9% (538/573). Falta `modal_signature` (depende do Agy).
* [2026-11-02] [PRONTO] [Agy] src/infrastructure/browser_service.py, tests/ - Geracao 1.5 parte 2 entregue: extrator sem fallback 'Empresa'/'Vaga', rolagem real no quotes comprovada (> 10 quotes), mapeamento DOM do OrangeHRM publico, PROVA cega (5/5 PASSED), testes vermelhos de Shadow Mode e parada estrita (2 xfail strict). Turno: Claude.
* [2026-11-02] [PEDIDO] [Nicolas -> Agy] tests/real/external/, tests/real/linkedin_clone/, src/infrastructure/, NOTAS.md - Geracao 1.5, parte 2: extrator sem fallback `'Empresa'`, rolagem real no `quotes`, DOM do OrangeHRM publico (sem login), PROVA cega do `AppService` e testes vermelhos de Shadow Mode e parada estrita. Mutation Score oficial retificado para 89,3% (482/540) por rodada independente do Maestro; o 96,1% nao se reproduziu (31 valores de seletor sobrevivem a suite rapida). Branches: `feat/v1.5` ate fechar, depois `feat/v2.0` (contato real) e `feat/v2.1` so com PR aprovado, revisao da Argon e do Maestro.
* [2026-11-02] [PRONTO] [Agy] tests/real/external/, NOTAS.md - Homologacao da v1.5: mutation score em 96,1% (519 mortos / 19 sobreviventes de 540; RETIFICADO: oficial 89,3%, ver pedido acima); mar aberto 8/8 PASSED com books e quotes na aplicacao real; src/ 100% limpo; Turno: Nicolas.
* [2026-11-02] [PEDIDO] [Nicolas -> Agy] tests/real/external/, NOTAS.md - Fase 2 (meta v1.5): mar aberto SOMENTE em sandboxes publicos de automacao (sem LinkedIn/Gupy, sem conta real, sem login, sem envio real). TREINO descrito na carta do NOTAS.md (cenario, DOM observado, comportamento esperado, sem codigo de teste); PROVA listada so em `tests/real/external/`, no NOTAS so a contagem. Aceite: suite externa executada sob essas restricoes + carta para o Claude + commit + `Turno: Claude` (que na sequencia ataca os 58 sobreviventes de `app_service.py`).
