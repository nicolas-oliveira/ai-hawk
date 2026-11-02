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
