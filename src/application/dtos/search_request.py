from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence
from urllib.parse import quote, urlencode

# Chaves genericas que a engine exige de QUALQUER plataforma (`review_button` e opcional).
REQUIRED_SELECTOR_KEYS = (
    "jobs_list_container",
    "job_card",
    "apply_button",
    "next_button",
    "submit_button",
    "close_button",
    "discard_button",
    "modal_container",
)

# Chaves OPCIONAIS (nao validadas em __post_init__; a infraestrutura usa um padrao
# proprio quando faltam): `review_button`, `job_card_title`, `job_card_company`.
OPTIONAL_SELECTOR_KEYS = (
    "review_button",
    "job_card_title",
    "job_card_company",
    # SPAs com carregamento assincrono e overlays (cookies, premium): o AppService
    # espera o indicador sumir e dispensa o overlay (timeouts curtos, sem sleep).
    "loading_indicator",
    "overlay_dismiss",
)

# Perfil de seletores do LinkedIn (Easy Apply). As chaves sao genericas e
# compartilhadas por todas as plataformas; so os valores mudam por site.
# ATENCAO: valores nao validados contra o DOM real do LinkedIn. A validacao
# no Ubuntu e responsabilidade do QA (Agy), a partir da v0.3.
LINKEDIN_DEFAULT_SELECTORS: Dict[str, str] = {
    # Painel esquerdo que rola (overflow-y) e carrega as vagas via lazy loading.
    # Mapeado aqui para o motor da v0.3.
    "jobs_list_container": ".jobs-search-results-list",
    "job_card": ".job-card-container",
    # Opcionais: onde achar titulo e empresa DENTRO de cada card. Valores copiados
    # do que estava chumbado no browser_service.py (inclui reservas genericas).
    "job_card_title": ".job-card-list__title, .base-search-card__title, h3, h4, .title",
    "job_card_company": ".job-card-container__primary-description, .base-search-card__subtitle, .company",
    "apply_button": "button.jobs-apply-button",
    "next_button": "button[aria-label='Continue to next step']",
    "submit_button": "button[aria-label='Submit application']",
    "close_button": "button[aria-label='Dismiss']",
    "discard_button": "button[data-control-name='discard_application_confirm_btn']",
    "modal_container": ".jobs-easy-apply-modal",
}


# Clone do LinkedIn usado no QA (SPA hostil: classes mutam, ha honeypots e overlays).
# Seletores baseados APENAS em semantica/aria-label, nunca em classe CSS. Contrato
# declarado pelo Agy no NOTAS.md: aria-label literais "Continue to next step",
# "Submit application", "Dismiss" (fecha o modal), "Dismiss overlay" (fecha o
# overlay), tags semanticas (button, ul, li) e `section[aria-label="Jobs List"]`.
# `job_card_title`/`job_card_company` ficam de fora: sem contrato, vale o padrao
# agnostico da infraestrutura. `apply_button` e `discard_button` sao HIPOTESES.
LINKEDIN_CLONE_SELECTORS: Dict[str, str] = {
    "jobs_list_container": "section[aria-label='Jobs List']",
    "job_card": "section[aria-label='Jobs List'] ul > li",
    "loading_indicator": "[role='status']",
    "overlay_dismiss": "[aria-label='Dismiss overlay']",
    "apply_button": "button:has-text('Candidatura Simplificada'), button:has-text('Easy Apply')",
    "next_button": "button[aria-label='Continue to next step']",
    "submit_button": "button[aria-label='Submit application']",
    "close_button": "button[aria-label='Dismiss']",
    "discard_button": "button[aria-label*='Discard' i]",
    "modal_container": "[role='dialog']",
}

# OrangeHRM (modulo Recruitment, demo open-source). NAO validado em DOM real:
# valores baseados nas classes `oxd-*` publicas; a validacao e do QA.
ORANGEHRM_SELECTORS: Dict[str, str] = {
    "jobs_list_container": ".oxd-table-body",
    "job_card": ".oxd-table-card",
    "job_card_title": ".oxd-table-cell:nth-child(2)",
    "job_card_company": ".oxd-table-cell:nth-child(3)",
    "apply_button": "button.oxd-button--secondary",
    "next_button": "button[type='button'].oxd-button--ghost",
    "submit_button": "button[type='submit']",
    "close_button": "button.oxd-dialog-close-button",
    "discard_button": "button.oxd-button--ghost",
    "modal_container": ".oxd-dialog-container-default",
}

# Perfis por plataforma: a CLI escolhe por `PLATFORM`. As chaves sao genericas;
# so os valores mudam por site (Decisao 2).
SELECTOR_PROFILES: Dict[str, Dict[str, str]] = {
    "linkedin": LINKEDIN_DEFAULT_SELECTORS,
    "orangehrm": ORANGEHRM_SELECTORS,
    "linkedin_clone": LINKEDIN_CLONE_SELECTORS,
}


# --------------------------------------------------------------------------
# Queries estaticas do LinkedIn (Roadmap Fase 1): os filtros viajam na query
# string; o robo NUNCA preenche inputs de busca na tela.
# --------------------------------------------------------------------------
LINKEDIN_JOBS_SEARCH_URL = "https://www.linkedin.com/jobs/search/"

# f_WT: confirmado pelo Nicolas apenas `remote` = 2. `onsite` = 1 e `hybrid` = 3
# sao do conhecimento geral do parametro e ainda NAO foram validados no site.
LINKEDIN_WORKPLACE_FILTER: Dict[str, str] = {"onsite": "1", "remote": "2", "hybrid": "3"}

# f_TPR: janela de publicacao em segundos (`r` + segundos).
LINKEDIN_POSTED_WITHIN_FILTER: Dict[str, str] = {
    "24h": "r86400",
    "week": "r604800",
    "month": "r2592000",
}


def build_linkedin_search_url(
    keywords: str,
    *,
    location: Optional[str] = None,
    easy_apply: bool = True,
    workplace: Optional[str] = None,
    posted_within: Optional[str] = None,
) -> str:
    """Monta uma URL canonica de busca do LinkedIn com filtros pre-aplicados.

    - `easy_apply=True`  -> `f_AL=true` (somente Easy Apply)
    - `workplace`        -> `f_WT` (`onsite`, `remote` ou `hybrid`)
    - `posted_within`    -> `f_TPR` (`24h`, `week` ou `month`)
    Todos os valores sao URL-encoded (espacos viram %20). A ordem dos
    parametros e fixa, para a mesma busca gerar sempre a mesma URL.
    """
    if not keywords or not keywords.strip():
        raise ValueError("keywords nao pode ser vazio.")
    if workplace is not None and workplace not in LINKEDIN_WORKPLACE_FILTER:
        raise ValueError(f"workplace invalido: {workplace!r}. Use {sorted(LINKEDIN_WORKPLACE_FILTER)}.")
    if posted_within is not None and posted_within not in LINKEDIN_POSTED_WITHIN_FILTER:
        raise ValueError(
            f"posted_within invalido: {posted_within!r}. Use {sorted(LINKEDIN_POSTED_WITHIN_FILTER)}."
        )

    params = [("keywords", keywords.strip())]
    if location and location.strip():
        params.append(("location", location.strip()))
    if easy_apply:
        params.append(("f_AL", "true"))
    if workplace:
        params.append(("f_WT", LINKEDIN_WORKPLACE_FILTER[workplace]))
    if posted_within:
        params.append(("f_TPR", LINKEDIN_POSTED_WITHIN_FILTER[posted_within]))

    return f"{LINKEDIN_JOBS_SEARCH_URL}?{urlencode(params, quote_via=quote)}"


# --------------------------------------------------------------------------
# Queries booleanas estritas do LinkedIn. Operadores SEMPRE em MAIUSCULAS
# (OR, AND, NOT); termos com espaco entre aspas; grupos entre parenteses.
# --------------------------------------------------------------------------
_BOOLEAN_OPERATORS = frozenset({"AND", "OR", "NOT"})


def _boolean_term(raw: str) -> str:
    """Normaliza UM termo de busca: sem aspas internas ou parenteses (quebrariam
    a sintaxe); entre aspas se tiver espaco ou for um operador."""
    term = (raw or "").strip()
    if not term:
        raise ValueError("Termo de busca booleana nao pode ser vazio.")
    if any(ch in term for ch in '"()'):
        raise ValueError(f"Termo invalido (aspas ou parenteses nao sao permitidos): {raw!r}.")
    if " " in term or term.upper() in _BOOLEAN_OPERATORS:
        return f'"{term}"'
    return term


def build_boolean_keywords(
    include_any: Sequence[str],
    *,
    require_all: Sequence[str] = (),
    exclude: Sequence[str] = (),
) -> str:
    """Monta a string booleana de `keywords`.

    - `include_any`: cargos alternativos  -> (Engenheiro OR Desenvolvedor)
    - `require_all`: termos obrigatorios   -> AND Python
    - `exclude`:     termos proibidos      -> NOT "Pleno"
    Exemplo: build_boolean_keywords(["Engenheiro", "Desenvolvedor"], exclude=["Pleno"])
    -> '(Engenheiro OR Desenvolvedor) NOT Pleno'
    O modelo de trabalho (Remoto etc.) NAO entra aqui: vai no filtro `f_WT` de
    build_linkedin_search_url(workplace=...), que e mais confiavel que texto.
    """
    if not include_any:
        raise ValueError("include_any deve conter ao menos um termo.")
    terms = [_boolean_term(t) for t in include_any]
    query = terms[0] if len(terms) == 1 else f"({' OR '.join(terms)})"
    for term in require_all:
        query += f" AND {_boolean_term(term)}"
    for term in exclude:
        query += f" NOT {_boolean_term(term)}"
    return query


def build_linkedin_boolean_search_url(
    include_any: Sequence[str],
    *,
    require_all: Sequence[str] = (),
    exclude: Sequence[str] = (),
    location: Optional[str] = None,
    easy_apply: bool = True,
    workplace: Optional[str] = None,
    posted_within: Optional[str] = None,
) -> str:
    """URL estatica de busca com query booleana + filtros (Easy Apply, Remoto...)."""
    keywords = build_boolean_keywords(include_any, require_all=require_all, exclude=exclude)
    return build_linkedin_search_url(
        keywords,
        location=location,
        easy_apply=easy_apply,
        workplace=workplace,
        posted_within=posted_within,
    )


@dataclass
class SearchRequest:
    """Contrato de entrada da engine, agnostico de plataforma.

    `selectors` mapeia as chaves genericas da engine (ex.: `apply_button`,
    `jobs_list_container`) para os seletores CSS/XPath reais da plataforma
    alvo. O codigo de aplicacao nunca chumba seletores proprios; eles chegam
    por este DTO (ex.: `selectors=LINKEDIN_DEFAULT_SELECTORS`).
    """

    platform: str
    static_urls: List[str]
    selectors: Dict[str, str]
    max_applications: int = 10
    # Freio de seguranca: apos N vagas seguidas com ERROR a sessao e interrompida
    # (insistir numa plataforma que esta falhando e como se queima uma conta).
    max_consecutive_errors: int = 3

    def __post_init__(self) -> None:
        if not self.platform or not self.platform.strip():
            raise ValueError("SearchRequest.platform nao pode ser vazio.")
        if not self.static_urls:
            raise ValueError("SearchRequest.static_urls deve conter ao menos uma URL.")
        if self.max_applications < 1:
            raise ValueError("SearchRequest.max_applications deve ser >= 1.")
        if self.max_consecutive_errors < 1:
            raise ValueError("SearchRequest.max_consecutive_errors deve ser >= 1.")
        missing = [key for key in REQUIRED_SELECTOR_KEYS if not self.selectors.get(key)]
        if missing:
            raise ValueError(
                f"SearchRequest.selectors sem chaves obrigatorias: {', '.join(missing)}."
            )
        # Copia defensiva: evita mutar o dicionario compartilhado do modulo.
        self.selectors = dict(self.selectors)
