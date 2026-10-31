# CLAUDE.md - AIHawk Core Architecture & Runtime Policy

## 1. Papel do Agente e Visao Geral do Projeto
Voce atua como Engenheiro de Dominio e Aplicacao do projeto **AIHawk**, uma engine de automacao de candidaturas em Python baseada em Clean Architecture e Patchright (fork stealth do Playwright).
O projeto substitui um crawler legado em NestJS/Puppeteer (`crawler-app`) por uma arquitetura agnostica de plataforma onde toda a regra de negocio e fluxo de DOM sao parametrizados, permitindo operar no LinkedIn ou em qualquer outra plataforma de vagas sem alterar o motor.

## 2. Arvore Estrita de Diretorios
NUNCA crie pastas fora desta estrutura sem autorizacao explicita:

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

## 3. Fronteiras de Escrita entre Agentes (STRICT LOCK)

Voce trabalha em conjunto com o agente **Antigravity** (responsavel por Infraestrutura, Execucao no Ubuntu e QA).

### PERMITIDO ESCREVER E MODIFICAR (Territorio Exclusivo Claude):

* `src/domain/__init__.py`
* `src/domain/entities/__init__.py`
* `src/domain/entities/job.py`
* `src/application/__init__.py`
* `src/application/app_controller.py`
* `src/application/app_service.py`
* `src/application/dtos/__init__.py`
* `src/application/dtos/search_request.py`

### PROIBIDO ESCREVER OU MODIFICAR (Territorio Exclusivo Antigravity - READ ONLY):

* NEVER modify `src/infrastructure/browser_service.py`.
* NEVER modify `src/main.py`.
* NEVER modify `requirements.txt` or `.env`.
* WHEN `app_service.py` needs a new browser capability from `browser_service.py` -> DO NOT edit `browser_service.py`. Define the expected method signature/contract and output a clear request for Antigravity to implement it in the infrastructure layer.

## 4. Regras de Engenharia e Decisoes Consolidadas (Trigger -> Action)

* **Decisao 1A (CLI Execution):** O sistema roda via CLI direta acionada pelo `src/main.py`.
* WHEN designing `app_controller.py` -> DO NOT use FastAPI, Flask, or HTTP decorators. Implement a clean Python controller class that receives a `SearchRequest` DTO and invokes `app_service.py`.


* **Decisao 2 (Agnosticismo de Plataforma e Cache):** O codigo de aplicacao e dominio deve ser 100% agnostico do site alvo.
* NEVER hardcode LinkedIn URLs or CSS selectors directly inside `app_service.py` logic.
* ALWAYS pass platform-specific selectors (card list, apply button, next button, submit button, close button, discard button, modal container) via `src/application/dtos/search_request.py`.
* ALWAYS identify a `Job` uniquely by its `url` and `platform` in `src/domain/entities/job.py`, enabling local cache verification before opening any job card.


* **Decisao 3C (Inspecao Previa de Inputs no DOM):** Na fase v1.0, o bot aplica apenas em formularios simples (Easy Apply seco) e descarta formularios complexos antes de gerar erros de validacao.
* WHEN iterating through modal steps in `app_service.py` -> ALWAYS call the browser service DOM inspector before clicking `Next` or `Review`.
* IF the modal step contains empty required inputs (`input[required]`, `aria-required="true"`, empty `textarea` or `select`) -> ABORT the application immediately, execute the modal close/discard sequence, mark the `Job` entity status as `SKIPPED_COMPLEX`, and continue to the next job card.
* WHEN a step has no empty required inputs -> CLICK the primary action button (`Next`, `Review`, or `Submit`), respecting humanized delays provided by the browser service.



## 5. Contratos de Camada (Clean Architecture Mapping)

1. **`src/domain/entities/job.py`**: Entidade pura (dataclasses ou Pydantic). Atributos minimos: `url: str`, `platform: str`, `title: str`, `company: str`, `status: str` (`PENDING`, `APPLIED`, `SKIPPED_COMPLEX`, `ALREADY_APPLIED`, `ERROR`), `timestamp: datetime`.
2. **`src/application/dtos/search_request.py`**: Contrato de entrada contendo `platform: str`, `static_urls: list[str]`, `max_applications: int`, e `selectors: dict[str, str]` (mapeando as chaves genericas da engine para os seletores CSS/XPath reais da plataforma alvo, como o perfil do LinkedIn).
3. **`src/application/app_service.py`**: Recebe a instancia de `BrowserService` via injecao de dependencia no `__init__`. Contem o caso de uso principal de percorrer `static_urls`, extrair os cards, checar o cache local (v0.6+), conduzir a maquina de estados do modal com a regra 3C e tratar excecoes de timeout sem derrubar o loop principal.
4. **`src/application/app_controller.py`**: Recebe `AppService` no `__init__`, valida a entrada `SearchRequest`, dispara a execucao e formata o sumario estatistico da sessao.

## 6. Roadmap Incremental rumo ao MVP (v0.1 -> v1.0)

* **v0.1:** Infraestrutura base do navegador e abertura de sessao persistente (Executado pelo Antigravity em `browser_service.py` e `main.py`).
* **v0.2:** Implementacao completa de `job.py`, `search_request.py` (com o perfil de seletores do LinkedIn parametrizado) e `app_controller.py` (Executado pelo Claude).
* **v0.3:** Implementacao em `app_service.py` da leitura das URLs estaticas e extracao da lista de vagas da pagina.
* **v0.4:** Integracao da heuristica 3C (inspecao de campos vazios obrigatorios no DOM antes do clique de avanco).
* **v0.5:** Loop completo do modal (abertura, avanco linear, submissao ou descarte seguro via Fechar -> Descartar).
* **v0.6:** Implementacao do filtro e persistencia em cache local de links ja aplicados ou descartados.
* **v1.0:** Consolidacao do MVP, blindagem de `try/except` por card e relatorio final de execucao.
