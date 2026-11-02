"""TREINO (mar aberto) com a camada de aplicacao e os perfis de sandbox. Somente leitura, sem login/envio."""
import pytest

from src.application.app_service import AppService
from src.application.dtos.search_request import SELECTOR_PROFILES, SearchRequest

pytestmark = pytest.mark.external


def _run(browser, platform, url):
    request = SearchRequest(
        platform=platform,
        static_urls=[url],
        selectors=SELECTOR_PROFILES[platform],
        max_applications=3,
    )
    return AppService(browser).run(request)


def test_app_books_toscrape_extrai_20_urls_unicas_sem_empresa(open_sea_browser):
    jobs = _run(open_sea_browser, "books_toscrape", "https://books.toscrape.com/")
    assert len(jobs) == 20
    assert len({j.url for j in jobs}) == 20
    assert all(j.company == "" for j in jobs)
    assert all(j.title for j in jobs)
    # somente leitura: nenhum envio real
    assert not any(j.status.name == "APPLIED" for j in jobs)


def test_app_quotes_toscrape_termina_sem_erro_e_com_rolagem_real(open_sea_browser):
    page = open_sea_browser.get_page()
    jobs = _run(open_sea_browser, "quotes_toscrape", "https://quotes.toscrape.com/scroll")
    # Prova de rolagem real da janela: a pagina inicial possui 10 quotes; apos scroll lazy loading deve ter > 10
    quotes_count = page.locator("div.quote").count()
    assert quotes_count > 10, (
        f"A janela nao rolou via lazy loading: contagem permaneceu em {quotes_count} (esperado > 10)"
    )
    # Seguranca de dados: cards sem link sao descartados limpos sem gerar Job com url invalida
    assert jobs == []
