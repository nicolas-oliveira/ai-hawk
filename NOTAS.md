# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Fonte unica de verdade para a coordenacao assincrona entre Agy e Claude.

---

## 📬 COMUNICADO OFICIAL ATIVO NO TOPO (TURNO ATUAL)

**DE/PARA/TURNO:** Nicolas -> Agy (copia: Gemini Argon, Maestro, Claude) | Turno: Agy | 2026-11-04
**STATUS:** [PEDIDO] Fecho do bloco 2 negado: o codigo do Agy fica, a evidencia em `docs/` volta para correcao. Sem PR e sem tag da v1.6. Branch 'feat/2.0-portao-a'. Sem LinkedIn real.
**ACEITE/RESUMO:** Agy entrega R1 a R5 e passa `Turno: Claude`; Claude entrega C4 e passa `Turno: Agy`; Agy grava o teto novo (R6) e passa `Turno: Nicolas`; depois vem o fecho e o PR da v1.6.

**ASSUNTO:** Revisao do bloco 2: a evidencia do Agy volta para correcao | commit anterior: 'e333b11'

Agy (QA/Infra), cc Gemini Argon (Tech Lead), Maestro (Revisor), Claude (Dev),

Primeiro, o reconhecimento, porque ele e real. O seu laudo dos 28 sobreviventes, o que voce mandou no chat antes da entrega do Claude, bateu com a lista dele nos 28: mesma classificacao e mesma causa. Essa conferencia as cegas so funcionou porque voce fez a sua parte a serio. O levantamento de sinais tem veredito por sinal e valor por motor. O achado do WebGL do Chromium chegou ao Nicolas como decisao, que e exatamente o que a decisao 3 do PO pedia. Voce mapeou as chamadas de rede do motor ao iniciar, versionou os hooks com teste e deixou os 47 testes reais verdes nos dois motores. O codigo do seu turno fica.

Por que o fecho volta. Documento em `docs/` e a evidencia permanente do portao: e nele que alguem vai conferir, daqui a meses, por que aceitamos o que aceitamos. Na revisao, o Maestro achou nos documentos dados que nao conferem com a fonte:

* `docs/auditoria_mutantes_81ec6e4.md`: os mutantes 43 e 61 estao descritos de um jeito que nao confere com o seu proprio laudo do chat nem com a lista do Claude. O documento tambem cita um arquivo de teste que nao existe no diff do bloco e um commit de medicao diferente do que o Claude mediu.
* `docs/relatorio_go_nogo_firefox.md`, secao 5: o modo efetivo do Chromium aparece como `headless=True (channel="chrome")`, enquanto `docs/sinais_automacao_xvfb.md` diz `xvfb`. A tabela do bloco 1.1 registrava o user agent de cada rodada, e esta nao registra. A secao tambem cita um motivo de revisao manual que nao existe no codigo.
* Os ajustes b e c do PLANO OK ficaram sem evidencia na carta de entrega.

Decisoes do PO nesta revisao (regras, nao opcoes):

1. Dos 4 equivalentes, 1 sai antes do fim da v1.6: e o C4 do Claude, depois das suas correcoes.
2. O piso de 99% fica, mas precisa ser formalizado e provado (R5).
3. O WebGL entra no Portao B como criterio do A/B entre os dois motores, sem vies para nenhum. Nada a fazer agora.
4. Sem PR e sem tag da v1.6 ate R1 a R6 e o C4 estarem entregues e revisados.

Itens do Agy (um commit por item):

R1. Laudo dos 28: cada linha confere com a fonte (o cache de '81ec6e4', o codigo e a carta do Claude), e cada dado cita de onde veio. Onde o seu laudo e a lista do Claude divergirem, diga explicitamente, com os dois lados.
R2. Linha de base A/B: para cada rodada, o motor pedido, o modo efetivo, o canal, a versao e o user agent observado, nos dois motores e no mesmo modo exigido pela decisao 2A. Se o canal do Chromium mudou desde o bloco 1.1, diga quando, por que e quem decidiu: trocar de navegador e decisao do Nicolas.
R3. Trava sem brecha (ajuste b): explique na carta por que os seus testes provam que nenhum alvo fora do clone local inicia ou continua sem passar pela trava.
R4. Contrato das portas (ajuste c): liste cada modo de uso que o contrato do Claude definiu, com o teste real que prova cada um.
R5. Piso de 99%: formalize o que ele mede, por que 99 e onde o CI o aplica, e prove que o CI reprova abaixo do piso e acima do teto.
R6. Depois do C4 do Claude: grave o teto novo na catraca. O teto so desce.

Regra para todos os itens: todo nome, numero e commit escrito em `docs/` ou na carta confere com a fonte. Dado sem fonte nao entra.

Item do Claude (proximo turno, depois do Agy):

C4. Elimine 1 dos 4 equivalentes sem mudar o comportamento do bot. Prove com a suite rapida e com a mutacao do zero (por status, por arquivo e hash exato), e reporte o novo numero de sobreviventes.

Combinado: o `ROADMAP.md` foi atualizado pelo Maestro com o andamento do bloco 2 e os proximos passos. Leiam e nao editem. Ordem de turnos: Agy (R1 a R5), depois Claude (C4), depois Agy (R6), depois Nicolas.

Turno: Agy

Maestro Opus e Nicolas

## 1. Estado Atual da Squad

* **Turno Atual:** Agy (revisao do bloco 2 negada em 2026-11-04: a evidencia em `docs/` volta para correcao, R1 a R5; depois Claude C4, Agy R6 e Nicolas).
* **Regra de turno (lida por script):** o campo `Turno:` do topo so aceita `Claude`, `Agy` ou `Nicolas`. Mudar o `Turno` no mesmo commit do seu trabalho e o sinal de passagem. Commit fora do seu turno e recusado por hook.
* **Versao Consolidada da Aplicacao:** v1.5 (`master` = 'e28da32', merge do PR #4, tag `v1.5`). Antes: v1.0 ('414e4f8', PR #2, tag `v1.0`).
* **Caminho:** Geracao 2.0 fecha na v2.0, com marcos intermediarios: v1.5 (feito) -> v1.6 (Portao A: motor e seguranca, sem LinkedIn) -> v1.7 (Portao B: Shadow Mode real com a conta temporaria, sem envio) -> v2.0 (Portao C: Burner Run de 5 vagas, primeiro envio real) -> Geracao 2.5 (LLM) -> Geracao 3.0. Cada marco sai por PR para a master, com CI e catraca verdes, e so depois do merge ganha a tag. Se um portao falha, o proximo nao comeca. Backlog definitivo: a planilha do Nicolas.
* **Versao Alvo da Squad:** v1.6 (Portao A). Bloco 1: homologado com GO com condicoes ('e251373'). Bloco 1.1 (correcoes C1..C5 + A1..A7): entregue e homologado com GO pleno em Xvfb. Bloco 2: C1 a C3 entregues pelo Claude ('0776db7', '74ee9b6', '79cb102'); A1 a A5 entregues pelo Agy ('a8d275a' a 'e333b11'); revisao negada pela evidencia em `docs/`, correcoes em curso. O Portao A so fecha a v1.6 quando os blocos 1, 1.1 e 2 terminarem.
* **Branch Ativa:** `feat/2.0-portao-a`. A `master` so recebe PR; as `feat/*` aceitam push normal (sem force push nem exclusao).
* **Placar do Pytest:** rapido (`tests/domain` + `tests/application`) = 414 PASSED em '79cb102' (Mutation do zero em 04/11: 99,5%, 737/741, 4 sobreviventes equivalentes, catraca atualizada no CI para teto 4 e piso 99.0%). Suite infra: 32 PASSED. Suite real (`tests/real/`): 47 PASSED em Chromium (1059.48s) e 47 PASSED em Firefox sob `xvfb` (938.86s).
* **Proxima Acao Esperada:** Agy corrige a evidencia (R1 a R5); Claude elimina 1 equivalente (C4); Agy grava o teto (R6); so entao fecho, PR e tag v1.6.

* **Roadmap tecnico:** fica no `ROADMAP.md` da raiz (guardiao: Maestro). Leia-o junto com o topo antes de planejar. Os agentes leem; nao editam (permissao negada). O andamento vai na carta de entrega e o Maestro marca `●` no fecho.

Plano de subtasks do Claude e do Agy (Mermaid do proprio algoritmo, se houver): fica AQUI, sob um titulo com o nome de quem escreveu.

### Plano do Agy (bloco 2, A1 a A5: entregue)

* A1 ('a8d275a'): Trava de identidade em `BrowserService` e CLI (`--headless` bloqueado para alvos externos sem display real) + levantamento de sinais medidos sob Xvfb vs clone em `docs/sinais_automacao_xvfb.md`.
* A3 ('c7c3b7a'): Implementa portas `wait_until_hidden` e `job_shows_applied` em `BrowserService` + novos cenarios hostis no clone Next.js + bateria em `tests/real/external/test_already_applied_and_post_send_state.py`.
* A2 ('9970deb'): Homologacao da bateria real completa nos dois motores (Chromium 47/47 PASSED em 1059.48s, Firefox 47/47 PASSED em 938.86s sob Xvfb) registrada em `docs/relatorio_go_nogo_firefox.md` como linha de base A/B para Portao B.
* A4 ('f957bfb'): Atualiza teto da catraca no CI (`.github/workflows/ci.yml`: teto 4, piso 99.0%) + laudo forense dos 28 mutantes de '81ec6e4' em `docs/auditoria_mutantes_81ec6e4.md`.
* A5 (este commit): Hooks de governanca versionados em `scripts/hooks/` (`commit-msg`, `ler_topo.py`, `pre-commit`, `pre-push`) + instalador `scripts/install_hooks.sh` + regras consolidadas em `AGENTS.md` + testes em `tests/infrastructure/test_git_hooks.py`.

### Plano do Claude (bloco 2, C1 a C3: entregue)

* C1 ('0776db7'): lista dos 28 (`mutmut show`) -> `tests/application/test_logs_exatos.py` (mensagens inteiras com `caplog.records`) + imutabilidade, bordas e `staticmethod` -> cada mutante aplicado e confirmado morto; 4 equivalentes com diff e motivo na carta.
* C3 ('74ee9b6'): renomear nos testes (vermelho) -> renomear `BrowserPort.wait_until_hidden` e as 2 chamadas (verde).
* C2 ('79cb102'): tabela-verdade de 16 linhas (clique, confirmacao, estado, dialogo) -> `Job.mark_already_applied`, `SubmissionEvidence.applied_state_seen`, motivos `STATE_NOT_CONFIRMED`/`STATE_WITHOUT_CONFIRMATION` -> porta `job_shows_applied` -> leitura antes de abrir e depois do envio -> recusa `JOB_STATE_REQUIRED` -> chave `applied_state` so no clone -> fakes e testes antigos.

```mermaid
flowchart TD
  OPEN["_process_job: abre a vaga e prepara a pagina"] --> SA{"_strict_abort?"}
  SA -->|sim| F0["para (vaga PENDING)"]
  SA -->|nao| S0{"job_shows_applied(timeout=0)?"}
  S0 -->|sim| AA["ALREADY_APPLIED, sem dialogo, sem clique"]
  S0 -->|nao| BTN{"apply_button visivel?"}
  BTN -->|nao| S1{"job_shows_applied(SHORT_TIMEOUT)?"}
  S1 -->|sim| AA
  S1 -->|nao| SK["SKIPPED_COMPLEX"]
  BTN -->|sim| MODAL["modal: 3C, historico, SUBMITTING"] --> ENV["clique de envio e observacao"]
  ENV --> COMB{"confirmacao x estado"}
  COMB -->|"vista e candidatada"| OK["APPLIED"]
  COMB -->|"vista, estado nao mudou"| M1["MANUAL_REVIEW: STATE_NOT_CONFIRMED"]
  COMB -->|"ausente, candidatada"| M2["MANUAL_REVIEW: STATE_WITHOUT_CONFIRMATION"]
  COMB -->|"ausente, nao mudou"| M3["MANUAL_REVIEW: MODAL_STILL_OPEN ou CONFIRMATION_MISSING"]
  M1 --> P{"strict_abort?"}
  M2 --> P
  M3 --> P
  P -->|sim| PARA["lote para: MANUAL_REVIEW_STOP"]
```

### Plano do Claude (bloco 1.1, C1 a C5: entregue)

* C1 ('ba40e36'): tabela-verdade da `SubmissionEvidence` (8 linhas) -> testes de aplicacao (sucesso com dialogo aberto fecha; falha ao fechar nao rebaixa) -> `review_reason` e `_close_after_send`.
* C2 ('5418dea'): testes de recusa sem a chave e de Shadow sem a chave -> fakes com a confirmacao -> checagem no inicio do `run()`, fim do palpite em `_observe_submission`, chave no perfil do clone.
* C3 ('b4c0e02'): testes de PENDING sem clique, lote parado, descarte que falha, sumario e memoria do `JsonJobCache` -> `try` em `record_submitting` no `_submit` e desfazer em memoria no cache.
* C4 ('49b0231'): testes de parada, historico antes da parada e sumario -> `put` + `_stop(MANUAL_REVIEW_STOP)` no `_submit`.
* C5 ('81ec6e4'): lista de revisao manual chamada pela instancia em `execute`; sumario conferido byte a byte; mutation do zero.

```mermaid
flowchart TD
  INI["run()"] --> CONF{"Envio real e perfil sem submit_confirmation?"}
  CONF -->|sim| R2["_stop(SUBMIT_CONFIRMATION_REQUIRED), devolve []"]
  CONF -->|não| LISTA["_collect_jobs e laço das vagas"] --> SUB["_run_modal chega ao Submit (não shadow)"]
  SUB --> HIST{"cache ligado?"}
  HIST -->|não| R1["_discard e _stop(HISTORY_REQUIRED)"]
  HIST -->|sim| GRAVA["cache.record_submitting (fsync)"]
  GRAVA --> GOK{"gravou?"}
  GOK -->|não| R3["cache desfaz em memória; _discard_quietly; _stop(HISTORY_WRITE_FAILED); vaga PENDING"]
  GOK -->|sim| CLIQUE["mark_submitting; _send clica em Submit"]
  CLIQUE --> EV["SubmissionEvidence: clique, confirmação, diálogo"]
  EV --> SET["job.settle_submission (regra no domínio)"]
  SET -->|APPLIED| OK{"diálogo aberto?"}
  OK -->|sim| FECHA["_close_after_send: falha só no log"]
  OK -->|não| PROX["próxima vaga"]
  FECHA --> PROX
  SET -->|MANUAL_REVIEW| ST{"strict_abort?"}
  ST -->|sim| PARA["cache.put(job); _stop(MANUAL_REVIEW_STOP)"]
  ST -->|não| PROX2["run() faz o put e segue"]
```

### Plano do Agy (bloco 1.1, A1 a A7: entregue)

* A1 ('a41bb13'): `DEFAULT_VISIBILITY_TIMEOUT_MS = 3000` restaurado em `src/infrastructure/browser_service.py`; parametro `visibility_timeout_ms` no construtor do `BrowserService` (sem variavel de ambiente); teste de regressao em `tests/infrastructure/test_browser_service.py` e cenario de estouro (`very-slow-modal` 2500 ms com `visibility_timeout_ms=1000`).
* A2 ('376a286'): `get_project_root()` em `src/infrastructure/paths.py` ancorando `DEFAULT_CACHE_PATH` (`<raiz>/.cache/jobs_history.json`) e `SESSION_ROOT_DIR` padrao (`<raiz>/sessions`), mantendo caminhos relativos explicitos relativos ao `cwd`; log de caminhos absolutos no startup; `app_controller.execute(request)` em `src/main.py`; `.cache/` e `sessions/` validados via `git check-ignore -v`.
* A3 ('656679c'): perfil separado por motor em pastas irmas (`<root>/<platform>` para `chromium`, `<root>/<platform>-firefox` para `firefox`).
* A4 ('4f6b4c9'): modo do Firefox explicito (`firefox_headless_mode="xvfb"` padrao exige `/usr/bin/Xvfb` ou falha com `RuntimeError`; `"true_headless"` explicito emite `WARNING` e restaura `os.environ` no `close()`); `get_runtime_metadata()` para ambos os motores (`effective_mode`, `xvfb_path`, `browser_version`, `user_agent`).
* A5 ('2e30d1b'): fluxo base da v1.5 restaurado no clone (`1000 ms`, modal permanece aberto com confirmacao interna); cenarios explicitos `?scenario=close-on-submit`, `no-confirm`, `stuck-submit`, `slow-modal` e `very-slow-modal`; testes reais para C1, C2, C3 (diretorio-pai arquivo comum -> `OSError`) e C4.
* A6 ('87e700d'): prova de `BrowserService().channel == "chromium"` por padrao; remocao de `channel="chromium"` chumbado nas fixtures reais (`tests/real/conftest.py` e `tests/real/external/conftest.py`) e adicao de guarda de identidade do motor via `navigator.userAgent` (`"Firefox"` vs `"Chrome"`).
* A7 (este commit): alinhamento das paginas do santuario e mar aberto com C2; 1 rodada completa de `tests/real/` em Chromium (`39/39 PASSED`) e 3 rodadas seguidas em Firefox modo `xvfb` (`39/39 PASSED` nas 3, tempo `1,03x` medio / `1,04x` max); relatorio atualizado em `docs/relatorio_go_nogo_firefox.md` com veredito `GO`.

```mermaid
flowchart TD
  START["BrowserService.start_session()"] --> ENG{"engine?"}
  ENG -->|chromium| CR_MODE{"headless?"}
  CR_MODE -->|True| CR_HL["effective_mode = 'headless'"]
  CR_MODE -->|False| CR_HD["effective_mode = 'headed'"]
  ENG -->|firefox| FF_HL{"headless?"}
  FF_HL -->|False| FF_HD["effective_mode = 'headed'"]
  FF_HL -->|True| FF_OPT{"firefox_headless_mode == 'true_headless'?"}
  FF_OPT -->|Sim| WARN["Log WARNING + INVPW_TRUE_HEADLESS=1 temporario + effective_mode = 'headless-real'"]
  FF_OPT -->|Nao| XVFB{"shutil.which('Xvfb') existe?"}
  XVFB -->|Nao| ERR["Raise RuntimeError(XVFB_MISSING_ERROR_MSG)"]
  XVFB -->|Sim| OK_XVFB["effective_mode = 'xvfb' + xvfb_path = '/usr/bin/Xvfb'"]
  WARN --> CLOSE["close() restaura os.environ"]
```

```mermaid
flowchart LR
  ROOT["get_project_root() em src/infrastructure/paths.py"] --> CACHE_DEF["Sem --cache-path / JOB_CACHE_PATH: <raiz>/.cache/jobs_history.json"]
  CWD["os.getcwd()"] --> CACHE_EXP["Com --cache-path / JOB_CACHE_PATH relativo: abspath(cwd / caminho)"]
  ROOT --> SESS_DEF["Sem session_root_dir / SESSION_ROOT_DIR: <raiz>/sessions"]
  CWD --> SESS_EXP["Com session_root_dir / SESSION_ROOT_DIR relativo: abspath(cwd / caminho)"]
  SESS_DEF --> ENG_SEP{"engine?"}
  SESS_EXP --> ENG_SEP
  ENG_SEP -->|chromium| P_CR["<root_dir>/<platform>"]
  ENG_SEP -->|firefox| P_FF["<root_dir>/<platform>-firefox"]
```

---

## 2. Regras de Governanca e Etiquetas do NOTAS.md

1. **Leitura Obrigatoria do Topo:** Cada agente deve ler o e-mail ativo no topo, o Estado Atual e o `ROADMAP.md` antes de qualquer acao.
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
7. **Mutation Score:** todo score registrado traz a contagem por status e por arquivo, e foi medido do zero (`.mutmut-cache` movido para fora com `mv`, nunca `rm -rf`) e sem outro processo de teste rodando em paralelo. O Maestro pode reproduzi-lo; diferenca entre medicoes e investigada antes de entrar no historico.

8. **Versao e tag:** a revisao acontece antes do PR. Revisao negada nao gera PR nem tag e nao consome versao: a versao segue em aberto e as correcoes entram na mesma branch, com a rodada registrada no Historico como `[RESPOSTA]`. A tag so e criada depois do merge. Correcao depois do merge usa versao de correcao (v1.5.1). O numero seguinte so existe depois do merge da anterior.  Dentro de uma Geracao, cada portao aprovado fecha um marco intermediario (ex: v1.6, v1.7) com o mesmo fluxo: revisao antes do PR, merge manual do Nicolas e tag depois. Commit entre turnos nunca gera tag.

9. **Dois roadmaps:** o roadmap de produto (planilha, mantido pela Gemini Argon e pelo Nicolas) nao e alterado por agente nem pelo Maestro: ele diz O QUE o sistema entrega. O roadmap tecnico fica no `ROADMAP.md` da raiz e o Maestro e o guardiao: ele diz COMO. Roadmap e sempre em grafo unicode (estilo `git log --graph`); algoritmo e logica de codigo sao sempre em Mermaid. Cada item do produto entra com o nome sem alteracao, como titulo, e os passos tecnicos ficam embaixo dele. A cadeia e negocio (planilha: O QUE) -> tecnico (`ROADMAP.md`: COMO, do Maestro) -> subtasks (do Claude e do Agy, na secao 1 do NOTAS.md). Claude e Agy leem o `ROADMAP.md` e nao o editam (permissao negada): o andamento vai na carta de entrega e o Maestro marca `●` no fecho, depois da revisao; o Nicolas commita. Incluir, remover ou reordenar passos so por carta do Maestro; se um agente achar que falta ou sobra passo, faz `[PEDIDO]` ao Maestro e nao corrige sozinho. Detalhe tecnico nunca sobe para a planilha.

---

## 3. Papeis e Territorios de Escrita

| Papel | Agente | Territorio Permitido de Escrita |
|---|---|---|
| Decisor / Autorizacao / Merge do PR | Nicolas | `master` (PR manual via GitHub), `.claude/`, `.gemini/`, `scripts/maestro/`, `ROADMAP.md` (conteudo do Maestro) |
| DEV (Arquitetura e Contratos) | Claude | `src/domain/`, `src/application/`, `tests/domain/`, `tests/application/`, `NOTAS.md`; entrega Git (push, PR, tag) so com autorizacao |
| QA, Runtime e Infraestrutura | Antigravity (Agy) | `src/infrastructure/`, `src/main.py`, `tests/infrastructure/`, `tests/real/`, `tests/conftest.py`, `Makefile`, `requirements*.txt`, `docs/`, `.github/`, configs de ferramentas na raiz, `.env*`, `.gitignore`, `NOTAS.md` |
| Auditoria e Revisao | Argon | Somente leitura |

---

## 4. Historico de Handoffs
* [2026-11-04] [RESPOSTA] [Maestro e Nicolas -> Agy] NOTAS.md, ROADMAP.md - Revisao do bloco 2 negada: codigo fica; laudo em docs/ nao confere com a fonte (mutantes 43 e 61, arquivo e commit), base A/B sem modo e user agent por rodada, ajustes b e c sem evidencia. PO: piso 99% fica com prova; 1 dos 4 equivalentes sai (C4); WebGL vai ao A/B do Portao B. Turno: Agy.
* [2026-11-04] [PRONTO] [Agy] src/infrastructure/, tests/real/, docs/, scripts/, .github/, AGENTS.md, NOTAS.md - Portao A Bloco 2 homologado (A1 a A5): trava de identidade em BrowserService/CLI ('a8d275a'); portas job_shows_applied/wait_until_hidden e testes ('c7c3b7a'); linha de base A/B nos dois motores (Chromium 47/47 PASSED em 1059.48s, Firefox 47/47 PASSED em 938.86s sob Xvfb, '9970deb'); teto da catraca no CI atualizado (teto 4, piso 99.0%) e laudo forense ('f957bfb'); hooks de governanca versionados em scripts/hooks/ e testados (este commit). Turno: Nicolas.
* [2026-11-04] [PRONTO] [Claude] src/domain, src/application, tests/domain, tests/application - Bloco 2 C1 a C3: 24 dos 28 sobreviventes mortos (4 equivalentes, decisao do Nicolas); porta `wait_for_loader_to_disappear` renomeada para `wait_until_hidden`; vaga ja candidatada pela pagina (`job_shows_applied`, `applied_state`, `JOB_STATE_REQUIRED`, regra de combinacao confirmacao x estado). Commits '0776db7', '74ee9b6', '79cb102'; rapida 414 PASSED; mutation do zero 99,5% (737/741, 4 sobreviventes, nenhum novo). Turno: Agy.
* [2026-11-04] [PEDIDO] [Nicolas -> Claude] NOTAS.md - Bloco 2 aberto (fecha o Portao A): sobreviventes da mutacao um a um, vaga ja candidatada pela pagina, trava de identidade. Decisoes do PO: 1A (teto 28, so desce) e 2A (Chromium headless proibido no LinkedIn real; os dois motores em Xvfb fora do clone). Roadmap tecnico sai do NOTAS.md para o `ROADMAP.md` (leitura incentivada, edicao negada aos agentes; Maestro marca `●` no fecho). Turno: Claude.
* [2026-11-03] [PRONTO] [Agy] src/infrastructure/, src/main.py, tests/infrastructure/, tests/real/, docs/, NOTAS.md - Bloco 1.1 A1 a A7 entregues ('a41bb13' a este commit): prazo 3000 ms restaurado; `get_project_root()` em `paths.py`; perfil separado por motor; Firefox exige Xvfb salvo `true_headless` explicito; clone base v1.5 restaurado + cenarios C1..C4; guarda de `userAgent` nas fixtures reais; 39/39 PASSED em Chromium e 3x Firefox Xvfb (tempo 1,03x). Veredito GO. Turno: Nicolas.
* [2026-11-03] [PRONTO] [Claude] src/domain, src/application, tests/domain, tests/application - Bloco 1.1 C1 a C5: confirmacao vence dialogo aberto; envio real exige `submit_confirmation` (clone ganhou a chave); falha ao gravar SUBMITTING deixa PENDING e para; lote para apos MANUAL_REVIEW (5A); mutante 140 morto. Commits 'ba40e36' a '81ec6e4'; rapida 355 PASSED; mutation do zero 96,1% (689/717, 28 sobreviventes, nenhum novo). Turno: Agy.
* [2026-11-03] [RESPOSTA] [Maestro -> Claude, Agy] NOTAS.md - PLANO OK do bloco 1.1 com ajustes: historico fica no Submit (Mermaid corrigido); descarte do dialogo na falha de gravacao permitido; chave de confirmacao do clone com o dono do arquivo; sem variavel de ambiente para o prazo de visibilidade; guarda de identidade do motor nas fixtures reais. Turno: Claude.
* [2026-11-03] [PEDIDO] [Nicolas -> Claude] NOTAS.md - Bloco 1.1 (correcoes do GO com condicoes) aberto; decisoes do PO 4B (Chromium segue padrao ate o Portao B) e 5A (lote para apos MANUAL_REVIEW). Governanca: dois roadmaps (regra 9); roadmap de produto fica fechado, o tecnico fica na secao 1 com o Maestro. Territorio do Agy explicita `requirements*.txt`, `docs/` e `.github/`. Turno: Claude.
* [2026-11-03] [PRONTO] [Agy] src/infrastructure/, src/main.py, tests/real/, docs/ - Portao A bloco 1 homologado nos dois motores (Chromium + Firefox): BROWSER_ENGINE=chromium|firefox; requirements-firefox.txt isolado; regras 1A e 2A na CLI com cache obrigatorio; rotas de desafio, modal lento e broken modal no clone Next.js; suite real (32 PASSED) nos dois motores; Go/No-Go gerado em docs/relatorio_go_nogo_firefox.md com veredito GO (6 criterios verdadeiros, tempo 1,05x). Turno: Nicolas.
* [2026-11-03] [PRONTO] [Claude] src/domain, src/application, tests/domain, tests/application - Portao A bloco 1 (camada Claude): modal que nao abre e desafios (`abort_url_pattern`) param o lote; SUBMITTING com fsync; so envio confirmado vira APPLIED, o resto MANUAL_REVIEW; 1A (sem cache nao envia) e 2A (`strict_abort` padrao). Commit '8fa398f'; rapida 341 PASSED; mutation do zero 95,8% (664/693, 29 sobreviventes, nenhum novo).
* [2026-11-03] [PEDIDO] [Nicolas -> Claude] NOTAS.md - PLANO OK do Portao A, bloco 1 (branch 'feat/2.0-portao-a'): planos do Claude e do Agy aprovados com ajustes do Maestro; decisoes do PO 1A (nunca candidatura duplicada, envio real exige cache), 2A (parada estrita por padrao), 3A (fsync no SUBMITTING). Restauradas as secoes 1 e 2, apagadas por engano no commit '2e7bf69'; `git stash` proibido para agentes.
* [2026-11-02] [PRONTO] [Claude] NOTAS.md - Autorizacao recebida: push da feat/v1.5 e PR para a master. Tag v1.5 so depois do merge (Nicolas avisa no chat). Limitacoes conhecidas vao na descricao do PR e no backlog da v2.0.
* [2026-11-02] [RESPOSTA] [Nicolas -> Claude] NOTAS.md - Revisao do ponto estavel '3276d90' aprovada (Nicolas, Argon, Maestro). AUTORIZO: push, PR e tag da feat/v1.5; tag so apos o merge.