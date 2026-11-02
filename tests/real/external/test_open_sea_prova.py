"""PROVA (mar aberto): alvos mantidos so neste arquivo (o Claude nao le). Somente leitura, sem login/envio."""
import pytest

pytestmark = pytest.mark.external


def test_prova_ecommerce_ajax_cards_e_links_unicos(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://webscraper.io/test-sites/e-commerce/more")
    links = b.extract_links("div.card.thumbnail", "a.title")
    assert len(links) >= 3
    assert len(set(links)) == len(links)


def test_prova_tabela_paginada_nao_vira_link_falso(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://www.scrapethissite.com/pages/forms/")
    assert b.get_page().locator("tr.team").count() == 25
    assert b.extract_links("tr.team", "a.inexistente") == []


def test_prova_overlay_modal_intrusivo(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://the-internet.herokuapp.com/entry_ad")
    assert b.is_visible("div.modal", timeout=8000)
    b.dismiss_overlay_if_present("div.modal-footer p")
    assert not b.is_visible("div.modal", timeout=2000)


def test_prova_carregamento_dinamico_sem_login(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://the-internet.herokuapp.com/dynamic_loading/2")
    assert b.click_element("#start button")
    assert b.is_visible("#finish", timeout=10000)
