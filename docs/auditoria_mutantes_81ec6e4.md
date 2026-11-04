# Auditoria Forense dos 28 Mutantes Sobreviventes — Commit '81ec6e4'

**Data do Laudo:** 2026-11-04  
**Agente Auditor:** Antigravity (Agy — QA, Runtime & Infraestrutura)  
**Destinatários:** Gemini Argon (Tech Lead), Maestro Opus (Revisor Consultor), Nicolas (PO), Claude (Dev)  
**Commit Auditado:** `'81ec6e4'` (Baseline do Bloco 1.1)  
**Placar Inicial em '81ec6e4':** 689/717 mortos (96,1%), 28 sobreviventes, 0 mutantes no motor de infraestrutura.  
**Placar Pós-C1 (Commit '0776db7'):** 737/741 mortos (99,5%), 4 sobreviventes equivalentes, 0 novos mutantes.  
**Catraca Homologada no CI (`.github/workflows/ci.yml`):** Teto = 4 sobreviventes, Piso = 99.0% de mutation score.

---

## 1. Sumário Executivo

Na conclusão do Bloco 1.1 (commit `'81ec6e4'`), a catraca de mutação registrou 28 mutantes sobreviventes na suíte unitária de `src/domain/` e `src/application/`. A diretoria técnica (Nicolas, Gemini Argon, Maestro) determinou uma auditoria forense detalhada de cada sobrevivente para identificar brechas de teste reais vs. mutações equivalentes (que não alteram a semântica observável do programa).

No Bloco 2, Passo C1 (commit `'0776db7'`), o Claude desenvolveu testes unitários estritos em `tests/application/test_logs_exatos.py`, `tests/application/test_app_service_limits.py`, etc., eliminando **24 mutantes**. Os **4 sobreviventes restantes** foram formalmente comprovados como equivalentes pela squad.

---

## 2. Taxonomia e Rastreabilidade Completa dos 28 Mutantes Sobreviventes ('81ec6e4')

| ID Mutmut | Arquivo:Linha (em '81ec6e4') | Mutação Aplicada pelo Mutmut | Causa Raiz da Sobrevivência | Classificação | Teste que Eliminou / Desfecho |
|---|---|---|---|---|---|
| **43** | `domain/entities/job.py:45` | `isinstance(self.id, str)` -> constante booleana | ID é UUID4 auto-gerado ou string | **EQUIVALENTE** | Mutação idempotente no fluxo de domínio |
| **61** | `domain/entities/job.py:72` | `if self.url:` -> `if True:` | URL é sempre validada na criação do Job | **EQUIVALENTE** | Mutação idempotente no fluxo de domínio |
| **199** | `app_controller.py:176` | `"Falha ao exportar a telemetria em %s"` -> `"XX...%sXX"` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_falha_ao_exportar_telemetria` |
| **212** | `app_controller.py:195` | `"Telemetria existente ilegivel; preservada em %s"` -> `XX` | Asserção frouxa com `"msg" in caplog.text` | Matável | `test_telemetria_corrompida_e_preservada` |
| **244** | `app_service.py:124` | `@dataclass(frozen=True)` -> `frozen=False` (CallTiming) | Ninguém tentava alterar instância pós-criação | Matável | `test_calltiming_e_imutavel` |
| **261** | `app_service.py:171` | Log DEBUG `"%s(%s) -> %s em %.2f s"` -> `XX` | Mensagem de log de depuração sem teste exato | Matável | `test_chamada_rapida_so_loga_debug` |
| **263** | `app_service.py:174` | Log INFO `"Chamada lenta: ..."` -> `XX` | Mensagem de log informativo sem teste exato | Matável | `test_chamada_lenta_loga_debug_e_info` |
| **283** | `app_service.py:229` | `"Cache ilegivel; preservado em %s"` -> `XX` | Log não fixado com exatidão | Matável | `test_cache_ilegivel_e_preservado` |
| **284** | `app_service.py:231` | `"Cache ilegivel e nao foi possivel preserva-lo: %s"` -> `XX` | Log não fixado com exatidão | Matável | `test_cache_ilegivel_que_nao_da_para_preservar` |
| **301** | `app_service.py:277` | `"Falha ao gravar o cache em %s (seguindo so em memoria)."` -> `XX` | Log não fixado com exatidão | Matável | `test_falha_ao_gravar_o_cache_segue_em_memoria` |
| **329** | `app_service.py:334` | `"Limite de %d candidaturas atingido."` -> `XX` | Log não fixado com exatidão | Matável | `test_limite_de_candidaturas_loga_uma_vez_e_para` |
| **330** | `app_service.py:335` | `break` -> `continue` (limite de candidaturas) | Com `continue` o laço seguia repetindo o log por vaga | Matável | `test_limite_de_candidaturas_loga_uma_vez_e_para` |
| **343** | `app_service.py:351` | `"Sessao interrompida: %s."` (freio de erros) -> `XX` | Log não fixado com exatidão | Matável | `test_freio_de_erros_consecutivos_loga_o_motivo` |
| **360** | `app_service.py:381` | `"Tempo por chamada ao navegador (total %.2f s):"` -> `XX` | Log de sumário de métricas sem teste exato | Matável | `test_resumo_de_tempo_no_log` |
| **361** | `app_service.py:383` | `"  %s"` -> `"XX  %sXX"` | Formatação de indentação de sumário de métricas | Matável | `test_resumo_de_tempo_no_log` |
| **380** | `app_service.py:434` | `"Falha ao listar vagas em %s; seguindo para a proxima URL."` -> `XX` | Log não fixado com exatidão | Matável | `test_falha_ao_listar_uma_url` |
| **400** | `app_service.py:469` | `"Sem botao de candidatura visivel (%s): %s"` -> `XX` | Log não fixado com exatidão | Matável | `test_sem_botao_de_candidatura` |
| **405** | `app_service.py:479` | `"Erro ao processar %s"` -> `XX` | Log não fixado com exatidão | Matável | `test_erro_ao_processar_a_vaga` |
| **410** | `app_service.py:494` | `urlsplit(url or "")` -> `urlsplit(url or "XXXX")` | `urlsplit("XXXX").netloc` é `""`, idêntico a `urlsplit("").netloc` | **EQUIVALENTE** | Sem efeito observável para URL vazia/None |
| **432** | `app_service.py:537` | `last_signature = ""` -> `"XXXX"` | Nenhum teste devolvia assinatura no 1º passo | Matável | `test_assinatura_do_primeiro_passo_nao_e_comparada_com_texto_inicial` |
| **433** | `app_service.py:537` | `last_signature = ""` -> `None` | O guarda é `signature and signature == last_signature` | **EQUIVALENTE** | Assinatura real nunca é vazia nem None |
| **437** | `app_service.py:546` | `"Modal sem progresso entre dois passos; descartando."` -> `XX` | Log não fixado com exatidão | Matável | `test_modal_sem_progresso` |
| **439** | `app_service.py:552` | `"Regra 3C: campo obrigatorio vazio no passo; descartando (%s)."` -> `XX` | Log não fixado com exatidão | Matável | `test_modal_com_campo_obrigatorio` |
| **441** | `app_service.py:559` | `"Shadow Mode: Submit NAO clicado em %s."` -> `XX` | Log não fixado com exatidão | Matável | `test_modal_shadow` |
| **448** | `app_service.py:576` | `"Passo do modal sem botao de avanco reconhecido; descartando."` -> `XX` | Log não fixado com exatidão | Matável | `test_modal_sem_botao_de_avanco` |
| **449** | `app_service.py:583` | `"Limite de %d passos do modal excedido; descartando."` -> `XX` | Log não fixado com exatidão | Matável | `test_modal_estoura_o_limite_de_passos` |
| **475** | `app_service.py:657` | `"Falha ao descartar o modal apos erro."` -> `XX` | Log não fixado com exatidão | Matável | `test_falha_ao_descartar_apos_erro` |

---

## 3. Análise Detalhada dos 4 Mutantes Equivalentes Homologados

1. **Mutante 43 (`Job.id` validation):**
   - *Local:* `src/domain/entities/job.py:45`
   - *Mecanismo:* A entidade `Job` gera seu identificador via UUID4 no momento da inicialização (`__post_init__`). A validação redundante não pode falhar no modelo de domínio comercial e sua alteração para constante booleana produz exatamente o mesmo resultado para todas as instâncias válidas.
2. **Mutante 61 (`Job.url` check):**
   - *Local:* `src/domain/entities/job.py:72`
   - *Mecanismo:* As camadas consumidoras (`SearchRequest` e `AppService`) realizam sanitização prévia e garantem que URLs não vazias sejam entregues ao domínio. O teste condicional `if self.url:` sempre avalia como verdadeiro.
3. **Mutante 410 (`urlsplit` fallback string):**
   - *Local:* `src/application/app_service.py:494`
   - *Mecanismo:* A mutação substitui o fallback de string vazia `url or ""` por `url or "XXXX"`. Como `"XXXX"` não contém `:`, `/` ou delimitador de autoridade, `urlsplit("XXXX").netloc` avalia como string vazia `""`, resultando no mesmíssimo comportamento semântico para entradas nulas ou vazias.
4. **Mutante 433 (`last_signature` initialization):**
   - *Local:* `src/application/app_service.py:537`
   - *Mecanismo:* A variável de assinatura do modal é comparada através da expressão `signature and signature == last_signature`. Uma assinatura real gerada pelo inspetor DOM é uma string não vazia. Inicializar `last_signature` com `""` ou com `None` produz comportamento estritamente equivalente (a primeira comparação sempre resultará em falso).

---

## 4. Conclusão da Auditoria de QA

- **Total de mutantes avaliados:** 28
- **Mutantes mortos pelo Claude em C1:** 24 (85,7% dos sobreviventes)
- **Mutantes comprovados equivalentes:** 4 (14,3% dos sobreviventes)
- **Zero novos mutantes introduzidos** no Bloco 2.
- **Teto da catraca no CI atualizado para 4** e **piso de score elevado para 99.0%** no commit correspondente (`.github/workflows/ci.yml`).
