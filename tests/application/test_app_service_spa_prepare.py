from unittest.mock import MagicMock, call

from src.application.app_service import AppService, LOADER_TIMEOUT_MS, SHORT_TIMEOUT_MS
from src.application.dtos.search_request import (
    LINKEDIN_DEFAULT_SELECTORS,
    SELECTOR_PROFILES,
    SearchRequest,
)


def _request(selectors, urls=("http://exemplo/busca",)):
    return SearchRequest(platform="p", static_urls=list(urls), selectors=selectors, max_applications=1)


def _browser(cards=()):
    browser = MagicMock()
    browser.extract_job_cards.return_value = list(cards)
    browser.element_exists.return_value = True
    return browser


def test_listagem_espera_loader_e_depois_dispensa_overlay_na_ordem():
    browser = _browser()
    AppService(browser)._collect_jobs(_request(SELECTOR_PROFILES["linkedin_clone"]))

    nomes = [c[0] for c in browser.method_calls]
    assert nomes.index("open_url") < nomes.index("wait_for_loader_to_disappear")
    assert nomes.index("wait_for_loader_to_disappear") < nomes.index("element_exists")
    assert nomes.index("element_exists") < nomes.index("dismiss_overlay_if_present")
    assert nomes.index("dismiss_overlay_if_present") < nomes.index("scroll_container_to_end")


def test_usa_timeouts_curtos_do_contrato_sem_pausa_fixa():
    browser = _browser()
    AppService(browser)._collect_jobs(_request(SELECTOR_PROFILES["linkedin_clone"]))

    browser.wait_for_loader_to_disappear.assert_called_once_with("[role='status']", timeout=LOADER_TIMEOUT_MS)
    browser.dismiss_overlay_if_present.assert_called_once_with(
        "[aria-label='Dismiss overlay']", timeout=SHORT_TIMEOUT_MS
    )
    assert 2000 <= SHORT_TIMEOUT_MS <= 5000 and 2000 <= LOADER_TIMEOUT_MS <= 5000


def test_overlay_que_nao_aparece_nao_e_clicado():
    browser = _browser()
    browser.element_exists.return_value = False
    AppService(browser)._collect_jobs(_request(SELECTOR_PROFILES["linkedin_clone"]))

    browser.dismiss_overlay_if_present.assert_not_called()


def test_perfil_sem_chaves_spa_nao_chama_loader_nem_overlay():
    browser = _browser()
    AppService(browser)._collect_jobs(_request(LINKEDIN_DEFAULT_SELECTORS))

    browser.wait_for_loader_to_disappear.assert_not_called()
    browser.dismiss_overlay_if_present.assert_not_called()


def test_titulo_e_empresa_do_perfil_chegam_ao_extrator():
    browser = _browser()
    AppService(browser)._collect_jobs(_request(LINKEDIN_DEFAULT_SELECTORS))

    browser.extract_job_cards.assert_called_once_with(
        LINKEDIN_DEFAULT_SELECTORS["job_card"],
        title_selector=LINKEDIN_DEFAULT_SELECTORS["job_card_title"],
        company_selector=LINKEDIN_DEFAULT_SELECTORS["job_card_company"],
    )


def test_perfil_sem_titulo_e_empresa_repassa_none_para_usar_o_padrao_da_infra():
    browser = _browser()
    AppService(browser)._collect_jobs(_request(SELECTOR_PROFILES["linkedin_clone"]))

    kwargs = browser.extract_job_cards.call_args.kwargs
    assert kwargs == {"title_selector": None, "company_selector": None}


def test_ao_abrir_a_vaga_tambem_prepara_a_pagina():
    browser = _browser()
    service = AppService(browser)
    from src.domain.entities.job import Job

    job = Job(url="http://exemplo/vaga/123456/", platform="p", title="t", company="c")
    service._process_job(job, _request(SELECTOR_PROFILES["linkedin_clone"]))

    browser.wait_for_loader_to_disappear.assert_called()
    browser.dismiss_overlay_if_present.assert_called()
