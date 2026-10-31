from dataclasses import dataclass
from typing import Dict, List

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

    def __post_init__(self) -> None:
        if not self.platform or not self.platform.strip():
            raise ValueError("SearchRequest.platform nao pode ser vazio.")
        if not self.static_urls:
            raise ValueError("SearchRequest.static_urls deve conter ao menos uma URL.")
        if self.max_applications < 1:
            raise ValueError("SearchRequest.max_applications deve ser >= 1.")
        missing = [key for key in REQUIRED_SELECTOR_KEYS if not self.selectors.get(key)]
        if missing:
            raise ValueError(
                f"SearchRequest.selectors sem chaves obrigatorias: {', '.join(missing)}."
            )
        # Copia defensiva: evita mutar o dicionario compartilhado do modulo.
        self.selectors = dict(self.selectors)
