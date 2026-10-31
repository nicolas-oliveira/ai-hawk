from dataclasses import dataclass
from typing import Dict, List, Optional
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

# Perfil de seletores do LinkedIn (Easy Apply). As chaves sao genericas e
# compartilhadas por todas as plataformas; so os valores mudam por site.
# ATENCAO: valores nao validados contra o DOM real do LinkedIn. A validacao
# no Ubuntu e responsabilidade do QA (Agy), a partir da v0.3.
LINKEDIN_DEFAULT_SELECTORS: Dict[str, str] = {
    # Painel esquerdo que rola (overflow-y) e carrega as vagas via lazy loading.
    # Mapeado aqui para o motor da v0.3.
    "jobs_list_container": ".jobs-search-results-list",
    "job_card": ".job-card-container",
    "apply_button": "button.jobs-apply-button",
    "next_button": "button[aria-label='Continue to next step']",
    "submit_button": "button[aria-label='Submit application']",
    "close_button": "button[aria-label='Dismiss']",
    "discard_button": "button[data-control-name='discard_application_confirm_btn']",
    "modal_container": ".jobs-easy-apply-modal",
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
