import re

import pytest

from src.application.dtos.search_request import (
    OPTIONAL_SELECTOR_KEYS,
    REQUIRED_SELECTOR_KEYS,
    SELECTOR_PROFILES,
    SearchRequest,
)


def test_perfis_esperados_existem():
    assert {"linkedin", "orangehrm", "linkedin_clone"} <= set(SELECTOR_PROFILES)


@pytest.mark.parametrize("nome", sorted(SELECTOR_PROFILES))
def test_todo_perfil_tem_as_chaves_obrigatorias_e_so_conhecidas(nome):
    perfil = SELECTOR_PROFILES[nome]
    assert set(REQUIRED_SELECTOR_KEYS) <= set(perfil)
    assert set(perfil) <= set(REQUIRED_SELECTOR_KEYS) | set(OPTIONAL_SELECTOR_KEYS)


@pytest.mark.parametrize("nome", sorted(SELECTOR_PROFILES))
def test_todo_perfil_e_aceito_pelo_search_request(nome):
    request = SearchRequest(platform=nome, static_urls=["http://exemplo"], selectors=SELECTOR_PROFILES[nome])
    assert request.selectors == SELECTOR_PROFILES[nome]


def test_linkedin_clone_nao_usa_classes_css():
    """O DOM do clone muta classes: so semantica/aria-label vale."""
    for chave, seletor in SELECTOR_PROFILES["linkedin_clone"].items():
        assert not re.search(r"(^|[\s,>+~\]\)])\.[A-Za-z_-]", seletor), f"{chave} usa classe CSS: {seletor}"


def test_linkedin_clone_declara_overlay_e_loader_do_contrato():
    perfil = SELECTOR_PROFILES["linkedin_clone"]
    assert perfil["overlay_dismiss"] == "[aria-label='Dismiss overlay']"
    assert perfil["loading_indicator"] == "[role='status']"
