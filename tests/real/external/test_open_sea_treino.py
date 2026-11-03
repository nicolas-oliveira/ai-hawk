"""TREINO (mar aberto): sandboxes publicos de automacao, somente leitura. Alvos documentados no NOTAS.md."""
import pytest

pytestmark = pytest.mark.external


def test_treino_books_listagem_paginada(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://books.toscrape.com/")
    links = b.extract_links("article.product_pod", "h3 a")
    assert len(links) == 20
    assert len(set(links)) == 20


def test_treino_quotes_scroll_infinito_na_janela(open_sea_browser):
    b = open_sea_browser
    assert b.navigate("https://quotes.toscrape.com/scroll")
    page = b.get_page()
    antes = page.locator("div.quote").count()
    assert b.scroll_container("body", steps=6, delay=0.6)
    depois = page.locator("div.quote").count()
    assert depois > antes, f"lazy loading na janela nao disparou: {antes} -> {depois}"
