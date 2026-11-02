# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Claude -> Agy (copia: Gemini Argon, Maestro, Nicolas) | Turno: Agy | 2026-11-02
**STATUS:** [PEDIDO] Ajustes da revisao do Maestro feitos (itens 1 a 5 do Claude). Agy: 4 testes reais e homologacao no commit exato; depois `Turno: Nicolas`.
**ACEITE/RESUMO:** Rapida 177+ PASSED; mutation do zero 95,1% (562 mortos / 29 sobreviventes de 591). Parada estrita agora cobre listagem e desvio de dominio.

**ASSUNTO:** Parada estrita na listagem, desvio de dominio e mutation do zero | commit anterior: 'c7f0d77'

Agy (QA/Infra), cc Gemini Argon (Tech Lead), Maestro (Revisor), Nicolas (PO),

### 1. Feito (um commit por entrega)
1. `test_mutantes_residuais.py`: ja entrou no 'c7f0d77' (o commit da diretoria varreu o staged). Esta no git; a reproducao vale a partir dele.
2. Parada estrita na LISTAGEM ('be8a69f'): o `abort_indicator` e checado logo apos navegar para cada URL de listagem, mesmo com zero cards. Ao disparar, o lote para: `run` devolve so o que ja foi lido (PENDING, nada processado) e as URLs seguintes NAO sao abertas.
3. Desvio de dominio ('be8a69f'): `BrowserPort.get_current_url() -> str` (a sua). Com `strict_abort`, se o host da URL atual (sem `www.`, caixa ignorada) for diferente do host da pagina que o motor tentou abrir, o lote para com `last_abort_reason = "parada estrita: desvio de dominio (<esperado> -> <atual>) em <url>"`. URL atual vazia nao conta como desvio.
4. Fluxo da tag corrigido (memoria): Agy homologa, Nicolas escreve `AUTORIZO`, eu faco push da branch e abro o PR, Nicolas faz o merge, so entao eu crio a tag.
5. Mutation do zero em 'ee3e3d9' (cache apagado): 591 mutantes, 562 mortos, 29 sobreviventes = 95,1%.
   * app_service 24: todos texto de mensagem de log (equivalentes na pratica; nenhum muda decisao).
   * app_controller 2: texto de log.
   * job 3: 2 decoradores sem efeito observavel e `query = ""` -> `None` (`urlunsplit` trata igual): equivalentes.
   * search_request 0. Nenhum sobrevivente muda comportamento.

### 2. O que o Agy deve fazer (comportamento esperado)
1. Rota nova no clone: pagina de checkpoint SEM link para si mesma (com `data-testid='security-checkpoint'`), como PRIMEIRA URL da fila e a URL do clone como segunda. Esperado: zero vagas, `last_abort_reason` preenchido e a segunda URL nunca aberta.
2. No teste atual de parada estrita, afirmar que nao existe vaga da segunda URL (`len(jobs) == 1`).
3. Restaurar `test_prova_tabela_paginada_nao_vira_link_falso` (seletor inexistente devolve lista vazia) e manter o de paginacao como adicional.
4. Teste cego do `AppService` com `max_applications` maior que a contagem da pagina (ex.: 10): `len(jobs)` igual a contagem real e `company == ""`.
5. CI que nao fique verde sem testar nada: confirme que o job roda a rapida e a mutation de verdade (falha se faltar o cache/teste).
6. Homologar infra+real no commit exato do meu ultimo commit e passar `Turno: Nicolas` para o `AUTORIZO`.

Claude

---

## 1. Estado Atual da Squad

* **Turno Atual:** Agy.
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.0 (`master` = `414e4f8`, merge do PR #2, tag `v1.0`). Fase 1 do roadmap concluida.
* **Caminho:** v1.0 (feito) -> v1.5 (qualidade; a parada de revisao de 02/11 foi feita e restam os itens 10 a 19 do backlog) -> v2.0 (primeiro contato real: Shadow Mode no LinkedIn real com conta descartavel e Lote de Ignicao, na branch `feat/v2.0`) -> PR aprovado com revisao da Argon e do Maestro -> `feat/v2.1` (proxima fase, escopo conforme o backlog). Versoes intermediarias: so commit local, sem tag, sem push, sem PR.
* **Versao Alvo da Squad:** `v1.5`. Escopo restante: homologacao final da v1.5 pela diretoria apos o fechamento pelo Claude. Sem LinkedIn real.
* **Branch Ativa:** `feat/v1.5`. A `feat/v2.0` sera criada pelo Nicolas depois da parada final. A `feat/v0.1-stealth-engine` e so backup local; ninguem a usa.
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 177 PASSED (Mutation do zero em 02/11: 95,1%, 562/591). Suite infra+real = 27 PASSED (14 infra + 13 real Chromium). Total geral = 201 PASSED (0 falhas, 0 xfail).
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
