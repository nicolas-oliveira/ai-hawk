# NOTAS.md - Log de Handoff entre Agentes (AIHawk)

Formato: `[AAAA-MM-DD] [autor] [arquivo] - evento`. Uma linha por evento, mais recente no topo de cada secao.

## Papeis

| Papel | Agente | Territorio de escrita |
|---|---|---|
| Decisor / merge / tag | Nicolas | `master` (PR manual) |
| DEV (arquitetura e contratos) | Claude | `src/domain/`, `src/application/` |
| QA e infraestrutura | Antigravity (Agy) | `src/infrastructure/`, `src/main.py`, `requirements.txt`, `.env` |
| Revisao | Argon | somente leitura |

## Ambiente

* Ubuntu 24.04.5 LTS (noble)
* Python 3.14.4 (informado pelo Agy) - suporte do Patchright a esta versao: PENDENTE DE VERIFICACAO

## Estado atual

* Versao em andamento: v0.1 (Fundacao e Engine Stealth) - responsavel: Agy.
* Repositorio: ainda NAO e git (`git init` pendente, decisao do Nicolas).

## Pedidos pendentes

* (nenhum)

## Historico

* [2026-10-31] [Claude] src/ - a pedido do Nicolas, `application/`, `domain/`, `infrastructure/` e `main.py` foram movidos da raiz para `src/` (so os caminhos mudaram, conteudo intacto). Agy: executar a partir da raiz com `python -m src.main` e conferir se os imports funcionam sem `src/__init__.py`.
* [2026-10-31] [Claude] AGENTS.md - secao 6 ajustada (tag pos-merge), secoes 7 e 8 adicionadas, com aprovacao do Agy.
* [2026-10-31] [Agy] - alinhamento de papeis, comunicacao via NOTAS.md e fluxo de merge aprovados.
