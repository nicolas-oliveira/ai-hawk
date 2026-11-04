"""PROVA (mar aberto): alvos mantidos so neste arquivo (o Claude nao le). Somente leitura, sem login/envio."""
import pytest

from src.application.app_service import AppService
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import JobStatus

pytestmark = pytest.mark.external


def test_prova_ecommerce_ajax_cards_e_links_unicos(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://webscraper.io/test-sites/e-commerce/more")
    links = b.extract_links("div.card.thumbnail", "a.title")
    # Endurecido: contagem exata dos 3 cards renderizados na tela inicial e URLs unicas
    assert len(links) == 3
    assert len(set(links)) == 3
    assert all(l.startswith("https://webscraper.io/test-sites/e-commerce/more/product/") for l in links)


def test_prova_tabela_paginada_nao_vira_link_falso(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://www.scrapethissite.com/pages/forms/")
    assert b.get_page().locator("tr.team").count() == 25
    assert b.extract_links("tr.team", "a.inexistente") == []


def test_prova_tabela_paginacao_links_reais(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://www.scrapethissite.com/pages/forms/")
    assert b.get_page().locator("tr.team").count() == 25
    # Endurecido: extracao real dos 24 links de paginacao validos (sem assercoes tautologicas com seletores inexistentes)
    p_links = b.extract_links("ul.pagination li", "a")
    assert len(p_links) == 24
    assert len(set(p_links)) == 24
    assert all("?page_num=" in l for l in p_links)


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


def test_prova_app_service_e2e_alvo_cego(open_sea_browser):
    """
    PROVA CEGA DO APPSERVICE:
    Executa o AppService ponta a ponta com seletores montados DENTRO do teste,
    em alvo publico nao listado no NOTAS.md.
    Assercoes especificas e nao tautologicas de contagem exata, URLs unicas e status.
    """
    target_url = "https://webscraper.io/test-sites/e-commerce/more"
    blind_selectors = {
        "jobs_list_container": "div.container",
        "job_card": "div.card.thumbnail",
        "job_card_title": "a.title",
        "apply_button": "[data-aihawk-inerte]",
        "modal_container": "[data-aihawk-inerte]",
        "next_button": "[data-aihawk-inerte]",
        "submit_button": "[data-aihawk-inerte]",
        "close_button": "[data-aihawk-inerte]",
        "discard_button": "[data-aihawk-inerte]",
        "abort_indicator": "[data-aihawk-challenge]",
    }

    req = SearchRequest(
        platform="blind_prova_sandbox",
        static_urls=[target_url],
        selectors=blind_selectors,
        max_applications=10,
        shadow_mode=True,
    )

    app_service = AppService(open_sea_browser)
    jobs = app_service.run(req)

    # 1. Contagem exata de vagas extraidas e processadas (3 cards reais da pagina, sem teto artificial)
    assert len(jobs) == 3
    # 2. Todas as URLs extraidas sao unicas e pertencem ao dominio
    extracted_urls = [j.url for j in jobs]
    assert len(set(extracted_urls)) == 3
    assert all(u.startswith("https://webscraper.io/test-sites/e-commerce/more/product/") for u in extracted_urls)
    # 3. Titulos validos extraidos e empresa vazia (fallback generico sem inventar empresa)
    assert all(len(j.title) > 0 for j in jobs)
    assert all(j.company == "" for j in jobs)
    # 4. Status de descarte seguro sem submissao
    assert all(j.status == JobStatus.SKIPPED_COMPLEX for j in jobs)
    assert not any(j.status == JobStatus.APPLIED for j in jobs)

