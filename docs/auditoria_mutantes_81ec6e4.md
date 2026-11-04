# Auditoria Forense dos 28 Mutantes Sobreviventes — Baseline '81ec6e4'

**Data do Laudo:** 2026-11-04  
**Agente Auditor:** Antigravity (Agy — QA, Runtime & Infraestrutura)  
**Destinatários:** Gemini Argon (Tech Lead), Maestro Opus (Revisor Consultor), Nicolas (PO), Claude (Dev)  
**Commit Auditado (Origem):** `'81ec6e4'` (Fecho do Bloco 1.1)  
**Fonte Primária de Dados:** Arquivo de cache arquivado `.mutmut-cache.81ec6e4` e código-fonte em `'81ec6e4'`  
**Commit de Eliminação (C1):** `'0776db7'` (24 mutantes mortos por testes estritos em `tests/application/test_logs_exatos.py` e `tests/domain/test_job_transitions.py`)  
**Commit da Medição do Zero (C2):** `'79cb102'` (Medição com cache limpo: 737/741 mortos, 99,5%, 4 equivalentes sobreviventes, 0 novos)  
**Commit de Eliminação de Equivalente (C4):** `'e54568b'` (Mutante 43 eliminado, 737/740 mortos, 99,6%, 3 equivalentes sobreviventes, 0 novos)  
**Catraca no CI (`.github/workflows/ci.yml`):** Teto = 3 sobreviventes (R6), Piso = 99.0% de mutation score.

---

## 1. Sumário Executivo e Fontes dos Dados

Na conclusão do Bloco 1.1 (commit `'81ec6e4'`), a catraca de mutação registrou **28 mutantes sobreviventes** em `src/domain/` e `src/application/`.

Antes da abertura do Bloco 2, a diretoria técnica solicitou que Agy e Claude realizassem levantamentos independentes às cegas sobre a natureza desses 28 mutantes. A conferência cega confirmou paridade absoluta entre o laudo preliminar do Agy e a entrega do Claude no commit `'0776db7'` (C1):
* **24 mutantes matáveis** (20 relacionados a asserções parciais de log com `"msg" in caplog.text`, 1 dataclass mutável, 1 quebra de laço de limite e 2 inicializações de variáveis de estado/assinatura).
* **4 mutantes equivalentes** (sem qualquer alteração na semântica ou no comportamento observável da aplicação).

Todos os 24 mutantes matáveis foram mortos pelo Claude no commit `'0776db7'` através da suíte `tests/application/test_logs_exatos.py` (23 testes) e `tests/domain/test_job_transitions.py` (1 teste). A medição oficial do zero com árvore limpa foi executada pelo Claude no commit `'79cb102'`, atingindo **99,5% (737/741 mortos, 4 sobreviventes)**.

---

## 2. Taxonomia e Rastreabilidade Completa dos 28 Mutantes Sobreviventes ('81ec6e4')

A tabela abaixo foi conferida byte a byte contra `.mutmut-cache.81ec6e4`, o código-fonte em `'81ec6e4'` e a entrega do Claude em `'0776db7'` / `'79cb102'`:

| ID Mutmut | Arquivo:Linha (em '81ec6e4') | Mutação Aplicada pelo Mutmut | Causa Raiz da Sobrevivência | Classificação | Teste que Eliminou (em '0776db7') |
|---|---|---|---|---|---|
| **43** | `src/domain/entities/job.py:97` | `@dataclass(eq=False)` -> `@dataclass(eq=True)` (Job) | `Job` implementa `__eq__` e `__hash__` explícitos que sobrepõem o dataclass | **EQUIVALENTE** | Nenhum (comportamento de classe idêntico) |
| **50** | `src/domain/entities/job.py:117` | Remove `@staticmethod` de `canonicalize_url` | Chamada via classe funciona sem decorador em Python | Matável | `test_canonicalize_url_e_estatico_tambem_pela_instancia` (em `test_job_transitions.py`) |
| **61** | `src/domain/entities/job.py:136` | `query = ""` -> `query = None` em `canonicalize_url` | `urllib.parse.urlunsplit` trata `""` e `None` de forma idêntica | **EQUIVALENTE** | Nenhum (saída de URL normalizada idêntica) |
| **199** | `src/application/app_controller.py:176` | `"Falha ao exportar a telemetria em %s"` -> `"XX...%sXX"` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_falha_ao_exportar_telemetria` |
| **212** | `src/application/app_controller.py:195` | `"Telemetria existente ilegivel; preservada em %s"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_telemetria_corrompida_e_preservada` |
| **244** | `src/application/app_service.py:124` | `@dataclass(frozen=True)` -> `frozen=False` (CallTiming) | Nenhum teste tentava mutar campos pós-instanciação | Matável | `test_calltiming_e_imutavel` |
| **261** | `src/application/app_service.py:171` | Log DEBUG `"%s(%s) -> %s em %.2f s"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_chamada_rapida_so_loga_debug` |
| **263** | `src/application/app_service.py:174` | Log INFO `"Chamada lenta: ..."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_chamada_lenta_loga_debug_e_info` |
| **283** | `src/application/app_service.py:229` | `"Cache ilegivel; preservado em %s"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_cache_ilegivel_e_preservado` |
| **284** | `src/application/app_service.py:231` | `"Cache ilegivel e nao foi possivel preserva-lo: %s"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_cache_ilegivel_que_nao_da_para_preservar` |
| **301** | `src/application/app_service.py:277` | `"Falha ao gravar o cache em %s (seguindo so em memoria)."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_falha_ao_gravar_o_cache_segue_em_memoria` |
| **329** | `src/application/app_service.py:334` | `"Limite de %d candidaturas atingido."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_limite_de_candidaturas_loga_uma_vez_e_para` |
| **330** | `src/application/app_service.py:335` | `break` -> `continue` (limite de candidaturas) | Laço prosseguia repetindo log sem asserção de cardinalidade | Matável | `test_limite_de_candidaturas_loga_uma_vez_e_para` |
| **343** | `src/application/app_service.py:351` | `"Sessao interrompida: %s."` (freio de erros) -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_freio_de_erros_consecutivos_loga_o_motivo` |
| **360** | `src/application/app_service.py:381` | `"Tempo por chamada ao navegador (total %.2f s):"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_resumo_de_tempo_no_log` |
| **361** | `src/application/app_service.py:383` | `"  %s"` -> `"XX  %sXX"` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_resumo_de_tempo_no_log` |
| **380** | `src/application/app_service.py:434` | `"Falha ao listar vagas em %s; seguindo para a proxima URL."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_falha_ao_listar_uma_url` |
| **400** | `src/application/app_service.py:469` | `"Sem botao de candidatura visivel (%s): %s"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_sem_botao_de_candidatura` |
| **405** | `src/application/app_service.py:479` | `"Erro ao processar %s"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_erro_ao_processar_a_vaga` |
| **410** | `src/application/app_service.py:494` | `urlsplit(url or "")` -> `urlsplit(url or "XXXX")` | `urlsplit("XXXX").netloc` devolve `""`, idêntico a `urlsplit("").netloc` | **EQUIVALENTE** | Nenhum (saída de host idêntica) |
| **432** | `src/application/app_service.py:537` | `last_signature = ""` -> `"XXXX"` | Nenhum teste validava assinatura inicial do 1º passo | Matável | `test_assinatura_do_primeiro_passo_nao_e_comparada_com_texto_inicial` |
| **433** | `src/application/app_service.py:537` | `last_signature = ""` -> `None` | Guarda `signature and signature == last_signature` nunca bate | **EQUIVALENTE** | Nenhum (assinatura de modal nunca é vazia/None) |
| **437** | `src/application/app_service.py:546` | `"Modal sem progresso entre dois passos; descartando."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_modal_sem_progresso` |
| **439** | `src/application/app_service.py:552` | `"Regra 3C: campo obrigatorio vazio no passo; descartando (%s)."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_modal_com_campo_obrigatorio` |
| **441** | `src/application/app_service.py:559` | `"Shadow Mode: Submit NAO clicado em %s."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_modal_shadow` |
| **448** | `src/application/app_service.py:576` | `"Passo do modal sem botao de avanco reconhecido; descartando."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_modal_sem_botao_de_avanco` |
| **449** | `src/application/app_service.py:583` | `"Limite de %d passos do modal excedido; descartando."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_modal_estoura_o_limite_de_passos` |
| **475** | `src/application/app_service.py:657` | `"Falha ao descartar o modal apos erro."` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_falha_ao_descartar_apos_erro` |

---

## 3. Análise Forense Detalhada dos 4 Mutantes Equivalentes Homologados

1. **Mutante 43 (`Job` dataclass equality):**
   - *Arquivo e Linha:* `src/domain/entities/job.py:97`
   - *Código Original em '81ec6e4':* `@dataclass(eq=False)` acima de `class Job:`
   - *Mutação:* `@dataclass(eq=True)`
   - *Prova de Equivalência:* A classe `Job` define explicitamente seus métodos mágicos `__eq__` (linhas 105-108) e `__hash__` (linhas 110-112). Pela especificação da PEP 557 (Python `dataclasses`), quando uma classe define explicitamente `__eq__`, o decorator `@dataclass` **não sobrescreve** a implementação explícita existente, seja `eq=False` ou `eq=True`. O comportamento em runtime é rigorosamente idêntico.

2. **Mutante 61 (`canonicalize_url` query fallback):**
   - *Arquivo e Linha:* `src/domain/entities/job.py:136`
   - *Código Original em '81ec6e4':* `query = ""`
   - *Mutação:* `query = None`
   - *Prova de Equivalência:* A montagem da URL canônica ao final do método é feita via `urlunsplit((parts.scheme, parts.netloc, path, query, ""))`. A função `urllib.parse.urlunsplit` trata `query=""` e `query=None` de forma indistinguível (não anexa `?` quando o componente é falso/vazio). A string de URL retornada é exatamente a mesma para qualquer entrada.

3. **Mutante 410 (`_host` urlsplit fallback):**
   - *Arquivo e Linha:* `src/application/app_service.py:494`
   - *Código Original em '81ec6e4':* `return urlsplit(url or "").netloc.lower().removeprefix("www.")`
   - *Mutação:* `return urlsplit(url or "XXXX").netloc.lower().removeprefix("www.")`
   - *Prova de Equivalência:* Para qualquer URL válida (`http://...` ou `https://...`), a expressão de curto-circuito `url or ...` avalia apenas o operando esquerdo. Para entradas falsas (`url=""` ou `url=None`), `urlsplit("XXXX").netloc` avalia como string vazia `""`, pois `"XXXX"` não contém autoridade (sem `//`). Portanto, `urlsplit("").netloc` e `urlsplit("XXXX").netloc` devolvem exatamente `""`.

4. **Mutante 433 (`last_signature` guard initialization):**
   - *Arquivo e Linha:* `src/application/app_service.py:537`
   - *Código Original em '81ec6e4':* `last_signature = ""`
   - *Mutação:* `last_signature = None`
   - *Prova de Equivalência:* O loop de inspeção do modal avalia o progresso através de `if signature and signature == last_signature:`. No primeiro passo do modal, uma assinatura gerada pelo navegador é sempre uma string não vazia (composta pelo HTML/texto dos botões de avanço). Uma string não vazia nunca é igual a `""` e nunca é igual a `None`. Portanto, inicializar com string vazia ou com `None` resulta exatamente no mesmo fluxo lógico (o bloco condicional não é executado no primeiro passo).

---

## 4. Comparativo de Divergências entre Agentes

Não houve divergência de julgamento entre Agy e Claude:
* Ambos identificaram os **mesmos 28 mutantes** a partir do cache `.mutmut-cache.81ec6e4`.
* Ambos classificaram **24 como matáveis** e **4 como equivalentes**.
* A decisão do PO determinou que, dos 4 equivalentes, **1 foi eliminado pelo Claude no passo C4 (commit 'e54568b')**: o mutante 43 deixou de ser gerado pela remoção de `eq=False` em `Job`.
* O Agy atualizou a catraca no CI no passo R6 (`.github/workflows/ci.yml`) para o novo teto de **3 sobreviventes** (`survived <= 3`), com piso mantido em **99.0%** (score real medido: **99,6%** em 737/740 mortos).
* Os 3 equivalentes remanescentes (61, 410, 433) seguem para decisão e homologação final do Nicolas.
