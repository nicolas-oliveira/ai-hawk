# AIHawk Engine - Constituicao Arquitetural (Antigravity Role: Infra, Runtime & QA)

## 1. Contexto e Mudanca de Paradigma
O AIHawk e uma engine automatizada de candidaturas com arquitetura agnostica de plataforma. O projeto substitui uma base legada em NestJS v9 + TypeScript + Puppeteer v19.8.5 (que operava de forma stateless abrindo instancias headless do Chrome e lendo o DOM passivamente via `page.evaluate`) por uma arquitetura limpa em Python utilizando Patchright (fork anti-deteccao do Playwright com patches em C++ no motor do Chromium).

O sistema opera como um agente interativo de sessao persistente capaz de contornar sistemas anti-bot modernos (Cloudflare, DataDome) e interagir com estados dinamicos de formularios sem acoplamento direto ao DOM de um unico site no core da aplicacao.

## 2. Arvore Estrita do Projeto
A estrutura de diretorios abaixo e imutavel:

```text
├── .env
├── requirements.txt
└── src/
    ├── application/
    │   ├── __init__.py
    │   ├── app_controller.py
    │   ├── app_service.py
    │   └── dtos/
    │       ├── __init__.py
    │       └── search_request.py
    ├── domain/
    │   ├── __init__.py
    │   └── entities/
    │       ├── __init__.py
    │       └── job.py
    ├── infrastructure/
    │   ├── __init__.py
    │   └── browser_service.py
    └── main.py

```

## 3. Controle de Concorrencia e Fronteiras de Escrita (STRICT BOUNDARIES)

Este projeto e desenvolvido simultaneamente por dois agentes (Antigravity e Claude). Respeite rigorosamente as permissoes de escrita:

### PERMITIDO CRIAR E MODIFICAR (Territorio Antigravity):

* `@requirements.txt` e `@.env`
* `@src/infrastructure/__init__.py` e `@src/infrastructure/browser_service.py`
* `@src/main.py`
* Diretorios temporarios de sessao local (ex: `./sessions/`) e cache local.

### PROIBIDO MODIFICAR (Territorio Exclusivo do Claude - READ ONLY para Antigravity):

* NUNCA edite, sobrescreva ou refatore arquivos dentro de `src/domain/` (`@src/domain/entities/job.py`).
* NUNCA edite, sobrescreva ou refatore arquivos dentro de `src/application/` (`@src/application/app_controller.py`, `@src/application/app_service.py`, `@src/application/dtos/search_request.py`).
* QUANDO um teste de execucao falhar por erro de logica ou seletor dentro de `src/application/` ou `src/domain/` -> NAO altere o arquivo diretamente. Gere o traceback exato do erro e solicite a correcao de contrato para o Claude.

## 4. Decisoes Arquiteturais Consolidadas

1. **Gatilho de Execucao (Decisao 1A - CLI Direta):** `@src/main.py` executa como script direto de terminal. Sem servidor HTTP ou overhead de API na v1.0. Ele instancia `@src/infrastructure/browser_service.py`, injeta em `@src/application/app_service.py`, aciona `@src/application/app_controller.py` passando o DTO de `@src/application/dtos/search_request.py` e exibe o relatorio final no console.
2. **Design Agnostico e Cache de Links (Decisao 2):** A infraestrutura em `@src/infrastructure/browser_service.py` nao contem strings ou regras chumbadas do LinkedIn. Ela gerencia sessoes persistentes parametrizadas (`channel="chrome"`, `headless=False`, pasta `./sessions/{platform}`) e fornece metodos genericos de manipulacao e inspecao de DOM. O cache de URLs aplicadas/ignoradas evita retrabalho entre sessoes em qualquer plataforma.
3. **Inspecao Previa de Inputs no DOM (Decisao 3C):** Antes de avancar em qualquer modal de candidatura, a engine inspeciona o container do modal em busca de campos obrigatorios vazios (`input[required]`, `aria-required="true"`, `select` vazio, `textarea` vazio). Se detectar complexidade, aborta e descarta o modal sem disparar erros de submissao no front-end alvo.

## 5. De-Para Arquitetural (Legado TS -> Python Clean Architecture)

* `main.ts` + `app.module.ts` -> `@src/main.py` (Injecao manual de dependencias e execucao via CLI).
* `crawler.service.ts` -> `@src/infrastructure/browser_service.py` (Substitui `puppeteer.launch` stateless por Patchright com `launch_persistent_context` e `channel="chrome"` no Ubuntu).
* `app.controller.ts` -> `@src/application/app_controller.py` (Recebe DTO via CLI e aciona servico).
* `searchdaterequest.dto.ts` -> `@src/application/dtos/search_request.py` (Carrega URLs estaticas pre-filtradas, nome da plataforma e mapa de seletores CSS/XPath).
* `room.dto.ts` -> `@src/domain/entities/job.py` (Entidade de dominio: `url`, `platform`, `title`, `company`, `status`, `timestamp`).
* `app.service.ts` -> `@src/application/app_service.py` (Orquestra navegacao, listagem e loop de candidatura).

## 6. Roadmap de Versionamento e Criterios de Release (Git Tag)

O Antigravity e o responsavel por validar a execucao no Ubuntu (QA). A tag Git de cada versao e criada pelo Nicolas na `master`, SOMENTE apos o merge do PR manual (`git tag -a v0.x -m "Release v0.x"`). Fluxo: Antigravity testa na branch de feature e avisa em `NOTAS.md` -> Nicolas faz o PR/merge na `master` -> Nicolas cria a tag. Ninguem altera a `master` diretamente. A validacao exige 100% dos requisitos da respectiva versao passando nos testes:

* **v0.1 (Fundacao e Engine Stealth):** Configurar ambiente virtual, instalar `patchright` e `python-dotenv`, implementar `@src/infrastructure/browser_service.py` abrindo o Google Chrome nativo do Ubuntu com sessao persistente e validar navegacao basica via `@src/main.py`.
* **v0.2 (Contratos, Dominio e CLI):** Integrar `@src/main.py` com `@src/application/app_controller.py`, `@src/application/dtos/search_request.py` e `@src/domain/entities/job.py` (desenvolvidos pelo Claude).
* **v0.3 (Navegacao e Extracao de Listagem):** Testar e validar a abertura de URLs estaticas filtradas, rolagem de pagina (lazy loading) e extracao de URLs unicas de vagas.
* **v0.4 (Inspetor DOM 3C):** Implementar em `@src/infrastructure/browser_service.py` o metodo generico `has_empty_required_inputs(container_selector)` e validar em conjunto com o `app_service.py`.
* **v0.5 (Loop Easy Apply Seco):** Executar o fluxo completo de clique no botao de candidatura, avanco linear validado pelo Inspetor v0.4, submissao ou descarte seguro (Fechar -> Descartar).
* **v0.6 (Cache Agnostico):** Persistir e consultar URLs processadas (`APPLIED`, `SKIPPED_COMPLEX`) para impedir reabertura de vagas em execucoes futuras.
* **v1.0 (MVP Operacional):** Bateria de execucao estavel em lote com multiplas URLs estaticas, tratamento robusto de `TimeoutError` e relatorio final no terminal.

## 7. Protocolo de Comunicacao e Git

* Toda comunicacao entre agentes passa por `NOTAS.md` (pedidos de contrato, handoffs, tracebacks). Uma entrada por evento, com data, autor e arquivo afetado.
* Pedido de capacidade nova no navegador: o Claude define a assinatura do metodo e registra o pedido; o Antigravity implementa em `browser_service.py`.
* Falha de teste em `src/application/` ou `src/domain/`: o Antigravity registra o traceback exato; o Claude corrige.
* Branches por agente e feature (`claude/<feature>`, `agy/<feature>`). Commits atomicos, com o agente identificado na mensagem.
* A `master` so recebe merge via PR manual do Nicolas.

## 8. Ambiente

* Ubuntu 24.04.5 LTS (noble), Python 3.14.4 (informado pelo Antigravity). Priorizar libs puras ou com wheels estaveis; o Antigravity garante o venv.
