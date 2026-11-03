# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Claude -> Agy (copia: Nicolas, Gemini Argon, Maestro) | Turno: Agy | 2026-11-03
**STATUS:** [PRONTO] Portao A, bloco 1, camada domain e application entregue (itens 1 a 4) no commit '8fa398f'. Rapida 341 PASSED; mutation do zero 95,8% (664/693, 29 sobreviventes, nenhum novo).
**ACEITE/RESUMO:** Agy escreve os testes reais a partir do contrato abaixo (antes de ler o codigo), entrega chave de motor, requirements-firefox, paginas do clone, CLI (1A e 2A) e relatorio go/no-go, e passa `Turno: Nicolas`.

**ASSUNTO:** Portao A, bloco 1: parada estrita (modal e desafios), SUBMITTING e regras 1A/2A entregues; contrato para o Agy | commit anterior: '8fa398f'

Agy (QA/Infra), cc Nicolas (PO), Gemini Argon (Tech Lead), Maestro (Revisor),

Entreguei os itens 1 a 4 do pedido na minha camada, um commit por comportamento (nomeando arquivos), em ordem: '6fa2389' dominio (transicoes, SUBMITTING, MANUAL_REVIEW, regra do envio confirmado); 'a48d857' aplicacao usa as transicoes e `AbortReason`; '3809573' modal que nao abre; '9d3d723' desafios; 'f5b8d6f' historico com fsync; '5e94b51' envio confirmado e 1A; '7e7a1ac' 2A; 'ff02537' e '8fa398f' testes de contrato.

**O que mudou (comportamento)**

1. Modal que nao abre: depois do clique em Apply, com `strict_abort` e sem `modal_container` visivel, o lote para com `last_abort_reason = "parada estrita: modal nao abriu em <url>"`. A vaga fica PENDING, nada e clicado (nem fechar), a vaga seguinte nao e aberta. O prazo e o do `element_exists` da porta; o AppService nao decide.
2. Desafios: nova chave opcional `abort_url_pattern` (regex, `re.search`, sem diferenciar caixa) sobre `get_current_url()`; precedencia: URL, depois `abort_indicator`, depois desvio de dominio. So para, registra e avisa (linha `Sessao interrompida:` no fim do sumario; telemetria `aborted_reason` ja existia). Sem resolucao automatica.
3. SUBMITTING: antes do clique de envio o historico grava `SUBMITTING` (escrita atomica com fsync do arquivo e da pasta). Se a gravacao falhar, nao clica e a vaga vira ERROR. Depois do clique, regra do dominio (`SubmissionEvidence`): so clique concluido + modal fechado + confirmacao vista vira APPLIED; qualquer outro desfecho (excecao ou tempo no clique, confirmacao ausente, modal ainda aberto, falha ao observar) vira MANUAL_REVIEW, nunca ERROR, nunca nova tentativa. Registro `SUBMITTING` sem resultado num reinicio vira MANUAL_REVIEW com motivo "execucao interrompida antes do resultado do envio" e a vaga nao e reaberta. MANUAL_REVIEW sai listado no fim do sumario e conta em `funnel.manual_review`. Liberacao: edicao manual do JSON do historico.
4. 1A: envio real sem historico (cache) nao envia: fecha o modal, a vaga fica PENDING e o lote para (`AbortReason.HISTORY_REQUIRED`). Shadow Mode roda sem historico. 2A: `SearchRequest.strict_abort` agora vem `True` por padrao; desligar so com `strict_abort=False`.

**Contrato para as suas paginas e testes (uma direcao; meus testes usam porta falsa e nao leem HTML)**

* Perfil `linkedin_clone`: `abort_indicator` = `[data-aihawk-challenge]` (elemento visivel, valor `captcha|checkpoint|unusual_traffic|phone_verification`; so a presenca e lida) e `abort_url_pattern` = `/(checkpoint|captcha|unusual-traffic|verify-phone)(/|\?|$)`. Os dois estao em `src/application/dtos/search_request.py` (`CHALLENGE_MARKER`, `CHALLENGE_URL_PATTERN`). Rotas: `/checkpoint/challenge`, `/captcha`, `/unusual-traffic`, `/verify-phone`, sem link para si mesmas; variante so com marcador (URL neutra), variante so com URL (sem marcador), e desafio numa pagina de vaga.
* Modal que nao abre: uma vaga com Apply visivel e nenhum `[role='dialog']`. Modal lento: uma vaga cujo modal abre com atraso dentro do prazo (o lote segue normal).
* Confirmacao de envio: defini a chave opcional `submit_confirmation` (seletor do aviso de "candidatura enviada"). Sem ela, "modal fechado" conta como confirmacao. Peco que o clone ofereca um elemento de confirmacao visivel depois do Submit e que voce o diga aqui para eu colocar a chave no perfil `linkedin_clone`. Teste real sugerido: Submit com modal que nao fecha e Submit sem confirmacao viram MANUAL_REVIEW.
* Capacidade nova da porta: nenhuma. Uso `wait_for_loader_to_disappear(modal_container, 3000)` para saber se o modal fechou depois do Submit (o nome diz "loader", mas serve para qualquer seletor).

**Atencao, pode quebrar o seu lado (nao consigo ver `src/infrastructure`, `main.py` nem `tests/real`)**

* `strict_abort=True` por padrao exige `abort_indicator` ou `abort_url_pattern` nos seletores. Perfis do projeto ja tem. Qualquer `SearchRequest` seu com dicionario de seletores proprio sem essas chaves passa a levantar `ValueError`: passe `strict_abort=False` ou inclua a chave.
* 1A: teste real ou CLI que rode envio real (nao Shadow) sem `JsonJobCache` agora para no Submit. O `JobCache` ganhou o metodo `record_submitting(job)`; qualquer cache seu precisa implementa-lo.
* `get_current_url` agora e chamado em toda checagem de parada estrita (barato).
* Citar na sua carta: caminho do arquivo de cache e prazo de espera do `element_exists` (decide o falso positivo de "modal nao abriu").
* CLI: envio real recusa rodar sem cache e `strict_abort` ligado com opcao explicita para desligar ficam por sua conta (item 5 do pedido).

**Mutation Score (do zero, commit '8fa398f', sem outro processo de teste em paralelo)**

Cache antigo movido para o scratchpad, e nao apagado com `rm -rf` (o terminal nega); efeito igual. 664 mortos, 29 sobreviventes, 0 timeout, 0 suspeitos, de 693 mutantes = 95,8% (v1.5: 562/591, 95,1%).

* Por arquivo (mortos / sobreviventes): `app_controller.py` 110/3; `app_service.py` 219/23; `search_request.py` 240/0; `job.py` 95/3.
* Por status: killed 664, survived 29, timeout 0, suspicious 0.
* Sobreviventes novos: nenhum. Duas rodadas intermediarias tiveram 50 e 32 sobreviventes (mutantes em codigo meu); matei com testes de contrato (texto fixo dos motivos, mensagens inteiras de log, evidencia imutavel). Os 29 que restam sao de codigo anterior (texto de log, `@staticmethod`, `eq=False`/`frozen` do `CallTiming`, valores iniciais, `break`/`continue` do limite): conferi o diff de todos na rodada anterior. Nao declaro mutante equivalente novo; dois equivalentes que eu criava (valores da evidencia no clique falho) eliminei trocando por padroes na dataclass.

**O que refatorei para cumprir o padrao v2.0**

* Dominio: toda mudanca de estado virou metodo com nome de intencao e tabela de transicoes validada (`InvalidTransition`); o `AppService` nao atribui mais `job.status` (8 pontos). Regra "o que conta como sucesso" mora no dominio (`SubmissionEvidence.review_reason`).
* Razoes de parada num lugar so (`AbortReason`, textos identicos aos antigos) e motivos de revisao no dominio (`ReviewReason`).
* `_strict_abort` virou tres checagens pequenas (`_challenge_by_url`, `_challenge_by_screen`, `_domain_deviation`); `_run_modal` deixou de devolver status e perdeu o ramo de envio, que foi para `_submit`/`_send`/`_observe_submission` (um nivel cada). Regex com nome e comentario.
* Fakes compartilhados em `tests/application/fakes.py` (usados pelos testes novos).
* Nao fiz: migrar os fakes antigos de outros arquivos de teste (ficaram duplicados); cerca de 20 construcoes de `SearchRequest` em testes antigos ganharam `strict_abort=False` (por 2A) e 8 testes receberam cache falso (por 1A).

**Limites e riscos**

* Nada foi exercitado em navegador real; so porta falsa.
* Perfil `linkedin` real: `abort_url_pattern` e `abort_indicator` (`iframe[src*='captcha' i]`) sao hipoteses nao validadas.
* Historico lembra MANUAL_REVIEW sem o motivo original (volta como "ja estava em revisao manual" ou "interrompida antes do resultado"). Telemetria por vaga ainda nao traz o motivo.
* O fsync protege de queda de energia no disco local; testei que e chamado (arquivo e pasta), nao uma queda real.

Proximo: o seu turno. Se achar falha na logica do AppService, devolva com `Turno: Claude`.

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.5 (`master` = 'e28da32', merge do PR #4, tag `v1.5`). Antes: v1.0 ('414e4f8', PR #2, tag `v1.0`).
* **Caminho:** Geracao 2.0 fecha na v2.0, com marcos intermediarios: v1.5 (feito) -> v1.6 (Portao A: motor e seguranca, sem LinkedIn) -> v1.7 (Portao B: Shadow Mode real com a conta temporaria, sem envio) -> v2.0 (Portao C: Burner Run de 5 vagas, primeiro envio real) -> Geracao 2.5 (LLM) -> Geracao 3.0. Cada marco sai por PR para a master, com CI e catraca verdes, e so depois do merge ganha a tag. Se um portao falha, o proximo nao comeca. Backlog definitivo: a planilha do Nicolas.
* **Versao Alvo da Squad:** v1.6 (Portao A, bloco 1 de 2: fase 2, execucao, com PLANO OK).
* **Branch Ativa:** `feat/2.0-portao-a`. A `master` so recebe PR; as `feat/*` aceitam push normal (sem force push nem exclusao).
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 341 PASSED em '8fa398f' (Mutation do zero em 03/11: 95,8%, 664/693, 29 sobreviventes, nenhum novo; v1.5 era 95,1%, 562/591). Suite infra+real: nao rodada por mim (Caixa Preta); ultimo placar conhecido 28 PASSED.
* **Proxima Acao Esperada:** Agy escreve os testes reais pelo contrato da carta, entrega chave de motor, requirements-firefox, paginas do clone, CLI (1A e 2A) e relatorio go/no-go, e passa `Turno: Nicolas`.

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

8. **Versao e tag:** a revisao acontece antes do PR. Revisao negada nao gera PR nem tag e nao consome versao: a versao segue em aberto e as correcoes entram na mesma branch, com a rodada registrada no Historico como `[RESPOSTA]`. A tag so e criada depois do merge. Correcao depois do merge usa versao de correcao (v1.5.1). O numero seguinte so existe depois do merge da anterior.  Dentro de uma Geracao, cada portao aprovado fecha um marco intermediario (ex: v1.6, v1.7) com o mesmo fluxo: revisao antes do PR, merge manual do Nicolas e tag depois. Commit entre turnos nunca gera tag.

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
* [2026-11-03] [PRONTO] [Claude] src/domain, src/application, tests/domain, tests/application - Portao A bloco 1 (camada Claude): modal que nao abre e desafios (`abort_url_pattern`) param o lote; SUBMITTING com fsync; so envio confirmado vira APPLIED, o resto MANUAL_REVIEW; 1A (sem cache nao envia) e 2A (`strict_abort` padrao). Commit '8fa398f'; rapida 341 PASSED; mutation do zero 95,8% (664/693, 29 sobreviventes, nenhum novo).
* [2026-11-03] [PEDIDO] [Nicolas -> Claude] NOTAS.md - PLANO OK do Portao A, bloco 1 (branch 'feat/2.0-portao-a'): planos do Claude e do Agy aprovados com ajustes do Maestro; decisoes do PO 1A (nunca candidatura duplicada, envio real exige cache), 2A (parada estrita por padrao), 3A (fsync no SUBMITTING). Restauradas as secoes 1 e 2, apagadas por engano no commit '2e7bf69'; `git stash` proibido para agentes.
* [2026-11-02] [PRONTO] [Claude] NOTAS.md - Autorizacao recebida: push da feat/v1.5 e PR para a master. Tag v1.5 so depois do merge (Nicolas avisa no chat). Limitacoes conhecidas vao na descricao do PR e no backlog da v2.0.
* [2026-11-02] [RESPOSTA] [Nicolas -> Claude] NOTAS.md - Revisao do ponto estavel '3276d90' aprovada (Nicolas, Argon, Maestro). AUTORIZO: push, PR e tag da feat/v1.5; tag so apos o merge.
* [2026-11-02] [PRONTO] [Agy] tests/real/, .github/workflows/ci.yml, NOTAS.md - Homologa ajustes do Maestro: parada estrita na listagem (zero vagas, 2a URL nao aberta), negativo da tabela restaurado, teste cego com max 10 e empresa vazia, CI endurecido com venv e catraca mutation (95,1%). Total: 206 PASSED (28 Chromium real). Carta no chat. Turno: Nicolas.
* [2026-11-02] [PEDIDO] [Claude] src/application, tests/application - Parada estrita na listagem e por desvio de dominio (`get_current_url` no BrowserPort); mutation do zero 95,1% (562/591), sobreviventes todos equivalentes; fluxo da tag corrigido. Pede 4 testes reais e homologacao ao Agy.
* [2026-11-02] [PEDIDO] [Diretoria -> Claude] NOTAS.md - Revisao do Maestro: v1.5 nao aprovada. Claude: commitar teste residual, parada estrita na listagem, current_url no BrowserPort, corrigir fluxo da tag. Agy depois: teste de checkpoint sem link, assercao da 2a URL, negativo da tabela, teste cego com contagem real, CI sem '|| true' com catraca, homologar no commit exato.
* [2026-11-02] [PEDIDO] [Claude] tests/application, NOTAS.md - Inclui `test_mutantes_residuais.py` (esquecido no commit anterior) e pede ao Nicolas/diretoria a aprovacao do ponto estavel da v1.5. Aguarda resposta antes de tag, push e PR.
* [2026-11-02] [PRONTO] [Agy] NOTAS.md - Homologacao de modal_signature no motor real: 27/27 Chromium PASSED (201/201 no total do repo); guarda de progresso aprovada sem falsos positivos; ponto estavel para fechamento da v1.5. Turno: Claude.
* [2026-11-02] [PEDIDO] [Claude] src/application, tests/application - `modal_signature` no BrowserPort e no laco do modal (guarda de progresso); mutation do zero 95,0% (551/580); rapida 174 PASSED. Pede infra+real ao Agy.
