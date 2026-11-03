import pytest

from src.application.dtos import search_request as sr
from src.application.dtos.search_request import (
    LINKEDIN_DEFAULT_SELECTORS,
    SearchRequest,
    build_boolean_keywords,
    build_linkedin_search_url,
)


def _req(**kw):
    base = dict(platform="p", static_urls=["u"], selectors=LINKEDIN_DEFAULT_SELECTORS)
    base.update(kw)
    return SearchRequest(**base)


def test_filtros_do_linkedin_exatos():
    assert sr.LINKEDIN_WORKPLACE_FILTER == {"onsite": "1", "remote": "2", "hybrid": "3"}
    assert sr.LINKEDIN_POSTED_WITHIN_FILTER == {"24h": "r86400", "week": "r604800", "month": "r2592000"}


def test_url_com_todos_os_filtros_em_ordem_fixa():
    url = build_linkedin_search_url("python dev", location="São Paulo", workplace="hybrid", posted_within="month")
    assert url == ("https://www.linkedin.com/jobs/search/?keywords=python%20dev&location=S%C3%A3o%20Paulo"
                   "&f_AL=true&f_WT=3&f_TPR=r2592000")
    assert "f_TPR=r604800" in build_linkedin_search_url("a", posted_within="week")
    assert "f_WT=1" in build_linkedin_search_url("a", workplace="onsite")


def test_mensagens_da_url():
    with pytest.raises(ValueError) as e:
        build_linkedin_search_url("  ")
    assert str(e.value) == "keywords nao pode ser vazio."
    with pytest.raises(ValueError) as e:
        build_linkedin_search_url("a", workplace="mars")
    assert str(e.value) == "workplace invalido: 'mars'. Use ['hybrid', 'onsite', 'remote']."
    with pytest.raises(ValueError) as e:
        build_linkedin_search_url("a", posted_within="year")
    assert str(e.value) == "posted_within invalido: 'year'. Use ['24h', 'month', 'week']."


def test_mensagens_da_query_booleana():
    with pytest.raises(ValueError) as e:
        build_boolean_keywords([])
    assert str(e.value) == "include_any deve conter ao menos um termo."
    with pytest.raises(ValueError) as e:
        build_boolean_keywords([" "])
    assert str(e.value) == "Termo de busca booleana nao pode ser vazio."
    for ruim in ('a"b', "a(b", "a)b"):
        with pytest.raises(ValueError) as e:
            build_boolean_keywords([ruim])
        assert str(e.value) == f"Termo invalido (aspas ou parenteses nao sao permitidos): {ruim!r}."


def test_mensagens_do_search_request():
    with pytest.raises(ValueError) as e:
        _req(platform=" ")
    assert str(e.value) == "SearchRequest.platform nao pode ser vazio."
    with pytest.raises(ValueError) as e:
        _req(static_urls=[])
    assert str(e.value) == "SearchRequest.static_urls deve conter ao menos uma URL."
    with pytest.raises(ValueError) as e:
        _req(max_applications=0)
    assert str(e.value) == "SearchRequest.max_applications deve ser >= 1."
    with pytest.raises(ValueError) as e:
        _req(max_consecutive_errors=0)
    assert str(e.value) == "SearchRequest.max_consecutive_errors deve ser >= 1."


def test_limites_inferiores_aceitos_e_padrao_do_freio():
    r = _req(max_applications=1, max_consecutive_errors=1)
    assert (r.max_applications, r.max_consecutive_errors) == (1, 1)
    assert _req().max_consecutive_errors == 3


def test_selectors_faltando_lista_todas_as_chaves():
    sel = dict(LINKEDIN_DEFAULT_SELECTORS)
    for k in ("job_card", "apply_button"):
        sel[k] = ""
    with pytest.raises(ValueError) as e:
        _req(selectors=sel)
    assert str(e.value) == "SearchRequest.selectors sem chaves obrigatorias: job_card, apply_button."
