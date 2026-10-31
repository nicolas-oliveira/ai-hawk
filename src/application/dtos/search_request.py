from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SearchRequest:
    """Contrato de entrada da engine, agnostico de plataforma.

    `selectors` mapeia as chaves genericas da engine (ex.: `apply_button`,
    `next_button`, `modal_container`) para os seletores CSS/XPath reais da
    plataforma alvo. O codigo de aplicacao nunca chumba seletores proprios.
    """

    platform: str
    static_urls: List[str]
    max_applications: int
    selectors: Dict[str, str]

    def __post_init__(self) -> None:
        if not self.platform or not self.platform.strip():
            raise ValueError("SearchRequest.platform nao pode ser vazio.")
        if not self.static_urls:
            raise ValueError("SearchRequest.static_urls deve conter ao menos uma URL.")
