from urllib.parse import parse_qs, urlsplit

import pytest

from src.application.dtos.search_request import (
    build_boolean_keywords,
    build_linkedin_boolean_search_url,
)


def test_include_any_vira_grupo_com_or():
    assert build_boolean_keywords(["Engenheiro", "Desenvolvedor"]) == "(Engenheiro OR Desenvolvedor)"


def test_um_unico_cargo_nao_leva_parenteses():
    assert build_boolean_keywords(["Engenheiro"]) == "Engenheiro"


def test_exclusoes_viram_not_e_obrigatorios_viram_and():
    query = build_boolean_keywords(
        ["Engenheiro", "Desenvolvedor"], require_all=["Python"], exclude=["Pleno"]
    )
    assert query == "(Engenheiro OR Desenvolvedor) AND Python NOT Pleno"


def test_termo_com_espaco_vai_entre_aspas():
    query = build_boolean_keywords(["Software Engineer"], exclude=["Senior Staff"])
    assert query == '"Software Engineer" NOT "Senior Staff"'


@pytest.mark.parametrize("operador", ["OR", "and", "Not"])
def test_termo_que_e_operador_e_citado(operador):
    assert build_boolean_keywords([operador]) == f'"{operador}"'


@pytest.mark.parametrize("ruim", ['a"b', "a(b", "a)b"])
def test_aspas_e_parenteses_dentro_do_termo_sao_rejeitados(ruim):
    with pytest.raises(ValueError):
        build_boolean_keywords([ruim])


@pytest.mark.parametrize("vazio", ["", "   "])
def test_termo_vazio_e_rejeitado(vazio):
    with pytest.raises(ValueError):
        build_boolean_keywords(["Dev", vazio])
    with pytest.raises(ValueError):
        build_boolean_keywords(["Dev"], exclude=[vazio])


def test_include_any_vazio_e_rejeitado():
    with pytest.raises(ValueError):
        build_boolean_keywords([])


def test_url_combina_query_booleana_com_filtros_remoto_e_easy_apply():
    url = build_linkedin_boolean_search_url(
        ["Engenheiro", "Desenvolvedor"], exclude=["Pleno"], workplace="remote"
    )
    params = parse_qs(urlsplit(url).query)
    assert params["keywords"] == ["(Engenheiro OR Desenvolvedor) NOT Pleno"]
    assert params["f_WT"] == ["2"]
    assert params["f_AL"] == ["true"]
    assert "%20" in url and "+" not in urlsplit(url).query


def test_url_repassa_validacao_de_filtro_invalido():
    with pytest.raises(ValueError):
        build_linkedin_boolean_search_url(["Dev"], workplace="espacial")
