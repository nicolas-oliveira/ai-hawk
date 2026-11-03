# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Nicolas -> Claude (copia: Gemini Argon, Maestro, Agy) | Turno: Claude | 2026-11-03
**STATUS:** [PEDIDO] PLANO OK. Fase 2 (execucao) do Portao A, bloco 1, liberada. Branch 'feat/2.0-portao-a'. Sem LinkedIn real.
**ACEITE/RESUMO:** Claude implementa modal que nao abre, desafios, SUBMITTING com fsync e as regras de produto 1A/2A no dominio, e passa `Turno: Agy`; o Agy implementa chave de motor, requirements-firefox, paginas do contrato, testes reais e relatorio go/no-go, e passa `Turno: Nicolas`.

**ASSUNTO:** PLANO OK do Portao A, bloco 1, com ajustes e decisoes do PO | commit anterior: 'f542288'

Claude (Dev), cc Gemini Argon (Tech Lead), Maestro (Revisor), Agy (QA/Infra),

Contexto: os dois planos foram revisados pelo Maestro e aprovados na direcao. Esta carta substitui o pedido anterior por completo; se algo divergir de cartas de chat, vale esta.

Errata do Nicolas: a branch e 'feat/2.0-portao-a' (sem o "v"). O nome 'feat/v2.0-portao-a' foi erro de digitacao.

Decisoes do PO (regras de produto, nao opcoes):

* 1A. Nunca pode haver candidatura duplicada. Envio real so acontece com o historico (cache) ligado; sem cache, so Shadow Mode e testes.
* 2A. Tela inesperada para o lote inteiro por padrao (`strict_abort` ligado). Desligar so com opcao explicita, para teste.
* 3A. A gravacao do `SUBMITTING` usa fsync ja neste bloco, para sobreviver a queda de energia.

Regras deste pedido:

* So sandboxes publicos e o clone local. Nenhum acesso ao LinkedIn real e nenhuma conta.
* So o Nicolas troca de branch. Sem push e sem PR ate a linha `AUTORIZO`.
* Dependencia autorizada, somente esta: `invisible-playwright==0.44.1` e `invisible-core==54.49.0`, em `requirements-firefox.txt`. Fora do `requirements.txt` e do CI.
* Sem `BROWSER_ENGINE` o comportamento e o de hoje (padrao `chromium`).
* Catraca de mutacao: 95,0% e no maximo 29 sobreviventes. Mutante equivalente que nao da para matar: declarar na carta com o diff e o motivo; o Nicolas decide. Ninguem ajusta o teto sozinho.
* Cada um escreve so no seu territorio (regra 6). Capacidade nova de navegador: o Claude pede por carta, o Agy implementa.

Criterios do go/no-go (fixos; ninguem altera depois de rodar). GO so se TODOS forem verdadeiros no mesmo commit:

1. Todos os testes reais (`tests/real/` inteiro) que passam em chromium tambem passam em firefox.
2. A PROVA cega passa nos dois motores.
3. A suite rapida e a mutation seguem no placar acima.
4. Em 3 execucoes seguidas da suite real em firefox, zero falha intermitente.
5. Tempo da suite real em firefox de ate 2x o de chromium.
6. `src/domain` e `src/application` intocados pela chave de motor, e chromium continua padrao e verde.

Sempre registrar, mesmo em GO: falhas e atritos, tamanho do download do motor, tempo e tamanho no CI (so medir) e as chamadas de rede do motor ao iniciar. Criterio falso e NO-GO, com o motivo. A migracao definitiva so vem depois de um GO, em carta propria.

Padrao de codigo da v2.0 (vale para os dois):

* Dominio nao importa aplicacao nem infra. Regras e transicoes de status moram no dominio; a aplicacao orquestra; a infra so traduz a porta para o motor.
* Transicoes de status por metodos com nome de intencao na entidade, que validam a transicao.
* Razoes de parada definidas num unico lugar (enum ou constantes), nunca strings soltas.
* Funcoes curtas, um nivel de abstracao cada; nada de flags booleanas que mudam o sentido de uma funcao; regex com nome e comentario.
* Sem duplicacao: comportamento por motor num unico ponto; fakes e fixtures compartilhados num so lugar.
* Testes: um comportamento por teste, nome que diz a regra, sem espera fixa onde existe espera por condicao.
* Um commit por comportamento, nomeando os arquivos. Antes de passar o turno, revise o proprio diff e diga na carta o que refatorou.

Itens do Claude (um commit por entrega; nao passe o turno antes de todos):

1. Modal que nao abre: com parada estrita, vira parada com `last_abort_reason` e nenhuma vaga seguinte tentada; a vaga fica PENDING. O prazo de espera e o da porta, nao decidido no AppService.

2. Desafios: `abort_url_pattern` opcional (regex nomeada) e `abort_indicator`, conforme o seu plano, com precedencia URL antes do indicador. So parar, registrar e avisar no sumario. O contrato do seu plano e o oficial (rotas `/checkpoint/challenge`, `/captcha`, `/unusual-traffic`, `/verify-phone`; marcador `[data-aihawk-challenge]`).

3. SUBMITTING: grava antes do clique de envio, com escrita atomica e fsync (3A). Depois de `SUBMITTING`, so sucesso confirmado vira APPLIED; qualquer outro desfecho (excecao, confirmacao ausente, modal ainda aberto, tempo esgotado) vira MANUAL_REVIEW, nunca ERROR nem nova tentativa. Escreva como regra do dominio, nao como efeito de try/except. Liberacao de MANUAL_REVIEW: edicao manual do JSON por ora.

4. Regras 1A e 2A: as regras ficam no dominio/aplicacao (envio real exige cache; `strict_abort` padrao ligado no `SearchRequest`). A ligacao na CLI e do Agy.

5. Reporte a Mutation Score do zero no commit exato, por status e por arquivo, com os sobreviventes novos (se houver). Entrega: carta para o Agy com a lista abaixo, `Turno: Agy`.

O que vem depois (para voce repassar ao Agy):

1. ORDEM: escreva os testes a partir dos criterios antes de ler o codigo do Claude; so depois leia, para revisar.

2. Chave de motor no `BrowserService`: le `BROWSER_ENGINE`, normaliza (`strip` e `lower`) tanto da variavel quanto do parametro, padrao `chromium`, valor invalido falha com mensagem que lista os validos, `invisible-playwright` importado so quando firefox. Escolha do motor isolada numa fabrica pequena e testavel.

3. `requirements-firefox.txt` com os dois pins e comentario de uma linha.

4. Clone: as rotas e o marcador do contrato do Claude, sem variacoes, sem link para si mesmas; variante so com marcador, so com URL, e desafio numa pagina de vaga. Uma vaga cujo modal nao abre e outra cujo modal abre com atraso dentro do prazo (o lote segue normal). Se algo do contrato for inviavel, devolva ao Claude por carta.

5. CLI (`main.py`): envio real recusa rodar sem cache (1A); `strict_abort` ligado por padrao com opcao explicita para desligar (2A). Cite na carta o caminho do arquivo de cache e o prazo de espera da infra.

6. Testes reais dos cenarios acima; `tests/real/` inteiro nos dois motores; relatorio `docs/relatorio_go_nogo_firefox.md` gerado por script a partir da saida dos testes, com os 6 criterios, as 3 execucoes e os itens de "sempre registrar". Nao altere o CI.

7. Falha na logica do AppService: devolva ao Claude (`Turno: Claude`). Ao fechar, homologue no commit exato sem tocar em `src/domain`, `src/application`, `tests/domain` nem `tests/application` (mostrar `git diff --stat`) e passe `Turno: Nicolas` pedindo a revisao do relatorio.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Claude.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.5 (`master` = 'e28da32', merge do PR #4, tag `v1.5`). Antes: v1.0 ('414e4f8', PR #2, tag `v1.0`).
* **Caminho:** v1.5 (feito) -> v2.0 em tres portoes: A (motor e seguranca, sem LinkedIn), B (Shadow Mode real com a conta temporaria, sem envio), C (Burner Run de 5 vagas) -> v2.5 (LLM) -> v3.0. Se um portao falha, o proximo nao comeca. Backlog definitivo: a planilha do Nicolas.
* **Versao Alvo da Squad:** v2.0, Portao A, bloco 1 (fase 2: execucao, com PLANO OK).
* **Branch Ativa:** `feat/2.0-portao-a`. A `master` so recebe PR; as `feat/*` aceitam push normal (sem force push nem exclusao).
* **Placar do Pytest (base v1.5):** rapido (`tests/domain` + `tests/application`) = 178 PASSED (Mutation do zero em 02/11: 95,1%, 562/591, 29 sobreviventes). Suite infra+real = 28 PASSED (14 infra + 14 real Chromium). Total geral = 206 PASSED (0 falhas, 0 xfail).
* **Proxima Acao Esperada:** Claude executa os itens do bloco 1 e passa `Turno: Agy`.

---

## 2. Regras de Governanca e Etiquetas do NOTAS.md

1. **Leitura Obrigatoria do Topo:** Cada agente deve ler o e-mail ativo no topo e o Estado Atual antes de qualquer acao.
2. **Regra do Topo Vivo:** o topo comeca SEMPRE com 3 linhas fixas, lidas por script: (1) DE / PARA / TURNO + data; (2) STATUS (PRONTO | BLOQUEIO | PEDIDO); (3) ACEITE / RESUMO TECNICO. Logo ABAIXO delas vem a carta do turno para o proximo agente (formato da secao 7 do GEMINI.md: ASSUNTO, commit anterior, corpo). Nunca escreva nada acima das 3 linhas. Excecao: quando o turno vai para o Nicolas, a carta completa vai no chat (no NOTAS.md, so as 3 linhas e o Historico).
   Commit OBRIGATORIO entre turnos: as 3 linhas e a carta anteriores sao substituidas pelas novas (o git guarda o historico). Um resumo de ate 5 linhas vai para o Historico. A substituicao vale SO para o bloco do topo: as secoes 1 a 4 nunca sao apagadas.
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
5. **Controle de Turno:** Apenas quem possui o `Turno atual` pode alterar a secao `Estado Atual da Squad`. Fora do seu turno, o agente so le o NOTAS.md: nao edita, nao commita e nao mexe na arvore de trabalho.
6. **Governanca de Git:**
   - NUNCA usar `git add .` ou `git commit -a`. Sempre usar `git add NOTAS.md` explicitamente com seus arquivos de territorio.
   - Commitar com caminhos explicitos: `git commit -m "..." -- <seus arquivos> NOTAS.md` (nao leva o que o outro agente deixou preparado).
   - Prefixos de commit obrigatorios: `[Agy] ...` ou `[Claude] ...` (sem versao na mensagem).
   - Agentes NAO fazem troca de branch (so o Nicolas), `git stash`, merge de PR, force push, push direto na `master` nem reescrita de historico (`rebase`, `--amend`, `filter-branch`, `--no-verify`).
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
* [2026-11-03] [PEDIDO] [Nicolas -> Claude] NOTAS.md - PLANO OK do Portao A, bloco 1 (branch 'feat/2.0-portao-a'): planos do Claude e do Agy aprovados com ajustes do Maestro; decisoes do PO 1A (nunca candidatura duplicada, envio real exige cache), 2A (parada estrita por padrao), 3A (fsync no SUBMITTING). Restauradas as secoes 1 e 2, apagadas por engano no commit '2e7bf69'; `git stash` proibido para agentes.
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