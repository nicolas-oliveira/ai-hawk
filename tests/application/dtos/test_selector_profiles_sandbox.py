import pytest

from src.application.dtos.search_request import (
    BOOKS_TOSCRAPE_SELECTORS,
    QUOTES_TOSCRAPE_SELECTORS,
    SELECTOR_PROFILES,
    SearchRequest,
)


@pytest.mark.parametrize("nome,perfil", [("books_toscrape", BOOKS_TOSCRAPE_SELECTORS),
                                         ("quotes_toscrape", QUOTES_TOSCRAPE_SELECTORS)])
def test_perfil_de_sandbox_e_valido_e_registrado(nome, perfil):
    assert SELECTOR_PROFILES[nome] is perfil
    SearchRequest(platform=nome, static_urls=["https://x.com"], selectors=perfil)


def test_sandboxes_nunca_tem_botao_de_candidatura_real():
    for perfil in (BOOKS_TOSCRAPE_SELECTORS, QUOTES_TOSCRAPE_SELECTORS):
        for chave in ("apply_button", "next_button", "submit_button",
                      "close_button", "discard_button", "modal_container"):
            assert perfil[chave] == "[data-aihawk-inerte]"
        assert "job_card_company" not in perfil  # lista sem empresa e normal


def test_valores_do_dom_conferido():
    assert BOOKS_TOSCRAPE_SELECTORS["job_card"] == "article.product_pod"
    assert BOOKS_TOSCRAPE_SELECTORS["job_card_title"] == "h3 a"
    assert BOOKS_TOSCRAPE_SELECTORS["jobs_list_container"] == "ol.row"
    assert QUOTES_TOSCRAPE_SELECTORS["jobs_list_container"] == "body"  # rola a janela
    assert QUOTES_TOSCRAPE_SELECTORS["job_card"] == "div.quote"


def test_perfil_orangehrm_vagas_publicas_exato():
    from src.application.dtos.search_request import ORANGEHRM_VAGAS_PUBLICAS_SELECTORS as P
    assert SELECTOR_PROFILES["orangehrm_vagas_publicas"] is P
    assert P["jobs_list_container"] == "div.orangehrm-container"
    assert P["job_card"] == "div.orangehrm-card-container"
    assert P["job_card_title"] == "p.oxd-text--card-title"
    assert all(P[k] == "[data-aihawk-inerte]" for k in (
        "apply_button", "next_button", "submit_button", "close_button",
        "discard_button", "modal_container"))
    assert "job_card_company" not in P and "abort_indicator" not in P
    SearchRequest(platform="orangehrm_vagas_publicas", static_urls=["https://x.com"], selectors=P)


def test_valores_exatos_dos_perfis_de_producao():
    from src.application.dtos.search_request import (
        LINKEDIN_CLONE_SELECTORS as C, LINKEDIN_DEFAULT_SELECTORS as L, ORANGEHRM_SELECTORS as O)
    assert L == {
        "jobs_list_container": ".jobs-search-results-list",
        "job_card": ".job-card-container",
        "job_card_title": ".job-card-list__title, .base-search-card__title, h3, h4, .title",
        "job_card_company": ".job-card-container__primary-description, .base-search-card__subtitle, .company",
        "apply_button": "button.jobs-apply-button",
        "next_button": "button[aria-label='Continue to next step']",
        "submit_button": "button[aria-label='Submit application']",
        "close_button": "button[aria-label='Dismiss']",
        "discard_button": "button[data-control-name='discard_application_confirm_btn']",
        "modal_container": ".jobs-easy-apply-modal",
    }
    assert C == {
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
    assert O == {
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


def test_valores_exatos_dos_sandboxes_e_padroes():
    assert BOOKS_TOSCRAPE_SELECTORS["job_card_title"] == "h3 a"
    assert QUOTES_TOSCRAPE_SELECTORS["job_card_title"] == "span.text"
    r = SearchRequest(platform="p", static_urls=["u"], selectors=BOOKS_TOSCRAPE_SELECTORS)
    assert (r.max_applications, r.max_consecutive_errors) == (10, 3)
