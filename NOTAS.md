# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Nicolas -> Claude (copia: Gemini Argon, Maestro, Agy) | Turno: Claude | 2026-11-03
**STATUS:** [PEDIDO] Abertura da Geracao 2.0, Portao A (bloco 1). Branch 'feat/v2.0-portao-a'. Sem LinkedIn real.
**ACEITE/RESUMO:** Claude entrega a chave `BROWSER_ENGINE`, o `requirements-firefox.txt`, a parada estrita (modal que nao abre e desafios) e a intencao pre-clique, e passa `Turno: Agy`; o Agy testa pelos criterios antes de ler o codigo, emite o relatorio go/no-go e passa `Turno: Nicolas`.

**ASSUNTO:** Abertura da Geracao 2.0, Portao A (bloco 1): chave de motor, parada estrita e intencao pre-clique | commit anterior: tag 'v1.5'

Claude (Dev), cc Gemini Argon (Tech Lead), Maestro (Revisor), Agy (QA/Infra),

Contexto: a v1.5 esta fechada (merge na master e tag 'v1.5'). Abrimos a Geracao 2.0 em tres portoes: A (motor e seguranca, sem LinkedIn), B (Shadow Mode no LinkedIn real, sem envio) e C (Burner Run). Se um portao falha, o proximo nao comeca. Este pedido cobre so o bloco 1 do Portao A. "Perfil por identidade" e "Residuos da esteira" ficam para o pedido seguinte, porque dependem do resultado do spike e de decisoes de regra do Nicolas. O backlog definitivo e a planilha.

Regras deste pedido:

* So sandboxes publicos e o clone local. Nenhum acesso ao LinkedIn real e nenhuma conta.
* Branch 'feat/v2.0-portao-a', criada pelo Nicolas. Quem nao estiver nela para e avisa; so o Nicolas troca de branch. Sem push e sem PR ate a linha `AUTORIZO`.
* Dependencia autorizada pelo Nicolas nesta carta, somente esta: `invisible-playwright==0.44.1` e `invisible-core==54.49.0`, em `requirements-firefox.txt`. Elas nao entram no `requirements.txt` nem no CI. Nenhuma outra dependencia nova.
* Sem `BROWSER_ENGINE` o comportamento e o de hoje: o padrao e `chromium`.
* A catraca de mutacao nao pode piorar (95,0% e no maximo 29 sobreviventes). Codigo novo em `src/domain` ou `src/application` vem com teste que mata os mutantes dele.
* Cada um escreve so no seu territorio (regra 6).

Criterios do go/no-go. Ficam fixos agora e ninguem os altera depois de rodar. O spike so vira GO se TODOS forem verdadeiros no mesmo commit:

1. Todos os testes reais que passam em chromium tambem passam em firefox.
2. A PROVA cega passa nos dois motores.
3. A suite rapida e a mutation seguem no placar acima.
4. Em 3 execucoes seguidas da suite real em firefox, zero falha intermitente.
5. Tempo da suite real em firefox de ate 2x o de chromium (limite proposto pelo Maestro; o Nicolas ajusta ANTES de rodar, se quiser).
6. `src/domain` intocado pela chave de motor, e chromium continua como padrao e verde.

Sempre registrar no relatorio, mesmo em GO: cada falha e atrito, o tamanho do download do motor, tempo e tamanho no CI (so medir, sem alterar o CI) e as chamadas de rede feitas pelo motor ao iniciar. Qualquer criterio falso e NO-GO, e o relatorio diz qual. Um NO-GO bem fundamentado e um resultado valido. A migracao definitiva so e pedida depois de um GO, em carta propria.

Itens do Claude (um commit por entrega, nomeando os arquivos; nao passe o turno antes de todos):

1. Chave de motor: o `BrowserService` le `BROWSER_ENGINE` (`chromium` ou `firefox`). Ausente vale `chromium`. Qualquer outro valor falha na hora com mensagem que lista os valores validos. O caminho firefox importa o `invisible-playwright` so quando escolhido, para o chromium rodar sem ele instalado. Teste rapido da escolha e da falha (porta falsa, sem abrir browser).

2. `requirements-firefox.txt` com os dois pins exatos acima e um comentario de uma linha dizendo o porque (a versao do wrapper exige o core). Sem tocar no `requirements.txt`.

3. Parada estrita, modal que nao abre: hoje cai em ERROR. Deve virar parada estrita com `last_abort_reason` preenchido e nenhuma vaga seguinte tentada. Teste rapido.

4. Parada estrita, desafios: checkpoint, captcha, "trafego incomum" e verificacao de telefone passam a contar como `abort_indicator`, via perfil de seletores ou padroes de URL e nao por codigo solto. O Agy fornece as paginas de teste no sandbox; voce cobre com teste rapido por porta falsa. Nao existe resolucao automatica de desafio: so parar, registrar e avisar.

5. Intencao pre-clique minima: gravar `SUBMITTING` para a vaga ANTES do clique de envio. Depois de um reinicio, uma vaga com `SUBMITTING` e sem resultado nunca e repetida sozinha: vai para revisao manual (status proprio, listado no fim do lote). Teste rapido que simula a queda entre o `SUBMITTING` e o resultado e confirma que a vaga nao e reaberta. Diga na carta onde o estado fica persistido.

6. Reporte a Mutation Score do zero no commit exato (regra 7), por status e por arquivo, com os sobreviventes novos (se houver) e se sao texto de log ou equivalentes. Entrega: carta para o Agy com a lista abaixo, commits nomeando seus arquivos, `Turno: Agy`.

O que vem depois (para voce repassar ao Agy na sua carta, descrevendo o comportamento esperado):

1. ORDEM: antes de ler o codigo do Claude, escreva a partir dos criterios acima (a) a execucao da suite real parametrizada por `BROWSER_ENGINE`, para rodar a mesma suite nos dois motores, e (b) o script do relatorio. So depois leia o codigo do Claude, para revisar. Teste que espelha a implementacao nao vale.

2. Paginas de bloqueio no sandbox: rotas novas no clone, sem link para si mesmas, para captcha, checkpoint, "trafego incomum" e verificacao de telefone. O Nicolas anexa o HTML ou print salvo da tela de "trafego incomum" do Google; use como modelo do texto da pagina, sem copiar marca. Teste real: cada pagina como primeira URL da fila e a URL do clone como segunda. Esperado: zero vagas, `last_abort_reason` preenchido e a segunda URL nunca aberta.

3. Teste real: desafio na pagina da vaga (e nao so na listagem) para o lote.

4. Teste real: modal que nao abre vira parada estrita, e nao ERROR.

5. Rode a suite real em chromium e em firefox e emita `docs/relatorio_go_nogo_firefox.md` com a tabela dos 6 criterios (valor medido, verdadeiro ou falso), as 3 execucoes do firefox e os itens de "sempre registrar". O veredito GO ou NO-GO vai dentro do relatorio.

6. Nao altere o CI (a migracao e condicional); so meca download, tempo e tamanho.

7. Se uma falha for do adaptador em `src/`, devolva ao Claude com carta (`Turno: Claude`) em vez de corrigir. Quando fechar, homologue no commit exato, sem tocar em `src/domain`, `src/application`, `tests/domain` nem `tests/application` (mostrar o `git diff --stat` na carta), e passe `Turno: Nicolas` com a carta pedindo a revisao do relatorio.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Nicolas.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (qualidade; ajustes do Maestro homologados, aguardando deliberacao da diretoria) -> v2.0 (primeiro contato real: Shadow Mode no LinkedIn real com conta descartavel e Lote de Ignicao, na branch `feat/v2.0`) -> PR aprovado com revisao da Argon e do Maestro -> `feat/v2.1` (proxima fase, escopo conforme o backlog). Versoes intermediarias: so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo concluido: 100% dos testes verdes e catraca ativada.
* **Branch Ativa:** `feat/v1.5`. A `feat/v2.0` sera criada pelo Nicolas depois da parada final. A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 178 PASSED (Mutation do zero em 02/11: 95,1%, 562/591, 29 sobreviventes). Suite infra+real = 28 PASSED (14 infra + 14 real Chromium). Total geral = 206 PASSED (0 falhas, 0 xfail).
* **Proxima Acao Esperada:** Nicolas avalia homologacao e emite parecer da diretoria (se aprovado, insere `AUTORIZO: ...` no topo do NOTAS.md e passa `Turno: Claude` para push, PR e posterior tag apos merge).

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
* [2026-11-02] [PRONTO] [Claude] NOTAS.md - Autorizacao recebida: push da feat/v1.5 e PR para a master. Tag v1.5 so depois do merge (Nicolas avisa no chat). Limitacoes conhecidas vao na descricao do PR e no backlog da v2.0.
* [2026-11-02] [RESPOSTA] [Nicolas -> Claude] NOTAS.md - Revisao do ponto estavel '3276d90' aprovada (Nicolas, Argon, Maestro). AUTORIZO: push, PR e tag da feat/v1.5; tag so apos o merge.
* [2026-11-02] [PRONTO] [Agy] tests/real/, .github/workflows/ci.yml, NOTAS.md - Homologa ajustes do Maestro: parada estrita na listagem (zero vagas, 2a URL nao aberta), negativo da tabela restaurado, teste cego com max 10 e empresa vazia, CI endurecido com venv e catraca mutation (95,1%). Total: 206 PASSED (28 Chromium real). Carta no chat. Turno: Nicolas.
* [2026-11-02] [PEDIDO] [Claude] src/application, tests/application - Parada estrita na listagem e por desvio de dominio (`get_current_url` no BrowserPort); mutation do zero 95,1% (562/591), sobreviventes todos equivalentes; fluxo da tag corrigido. Pede 4 testes reais e homologacao ao Agy.
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
