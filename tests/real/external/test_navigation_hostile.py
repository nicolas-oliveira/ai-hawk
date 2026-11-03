from typing import Dict

import pytest

from src.application.app_service import AppService, JsonJobCache
from src.application.dtos import search_request as search_request_module
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import JobStatus
from src.infrastructure.browser_service import BrowserService


# Seletores puramente semanticos / ARIA para o SPA com Chaos DOM (sem classes nem IDs fixos)
SEMANTIC_CLONE_SELECTORS: Dict[str, str] = {
    "jobs_list_container": "section[aria-label='Jobs List']",
    "job_card": "section[aria-label='Jobs List'] ul li",
    "job_card_title": "h3",
    "job_card_company": "p",
    "apply_button": "section[aria-label='Job Details'] button",
    "modal_container": "div[role='dialog'][aria-label='Easy Apply Modal']",
    "next_button": "button[aria-label='Continue to next step']",
    "submit_button": "button[aria-label='Submit application']",
    "close_button": "button[aria-label='Dismiss']",
    "discard_button": "button[aria-label='Dismiss']",
    "abort_indicator": "[data-aihawk-challenge]",
    "abort_url_pattern": r"/(checkpoint|captcha|unusual-traffic|verify-phone)(/|\?|$)",
}


def assert_no_honeypot_compromised(page) -> None:
    """
    ASSERCAO NEGATIVA ANTI-TRAPACA:
    Verifica no DOM e no sessionStorage se qualquer elemento Honeypot invisivel
    ou tentativa de bypass de Overlay foi acionada durante a sessao.
    """
    compromised_locator = page.locator('[data-testid="honeypot-compromised"]')
    if compromised_locator.count() > 0 and compromised_locator.first.is_visible():
        alert_text = compromised_locator.first.inner_text()
        pytest.fail(
            f"FALHA ANTI-TRAPACA (Falso Positivo Bloqueado): O motor interagiu com "
            f"elemento invisivel ou forcou bypass! Detalhe: {alert_text}"
        )

    session_trap = page.evaluate(
        "() => window.sessionStorage.getItem('honeypot_compromised')"
    )
    if session_trap:
        pytest.fail(
            f"FALHA ANTI-TRAPACA (Sessao Comprometida): Honeypot disparado durante a "
            f"navegacao: {session_trap}"
        )


@pytest.mark.external
def test_hostile_clone_e2e_anti_cheat_and_success_state(
    hostile_clone_server: str,
    hostile_browser: BrowserService,
    tmp_path,
):
    """
    Prova de Fogo E2E contra o SPA Hostil em Next.js (http://localhost:3000):
    1. Valida navegacao resiliente a Chaos DOM (classes e wrappers mutaveis por seed),
       Lazy Loading assincrono (loaders role='status') e Overlay intrusivo (z-index 90).
    2. ASSERCAO NEGATIVA: Falha imediatamente se 'data-testid=honeypot-compromised' estiver ativo.
    3. ASSERCAO DE ESTADO: So passa se a tela final de 'Sucesso' do modal for efetivamente
       renderizada e extraida pela engine.
    """
    profiles = getattr(search_request_module, "SELECTOR_PROFILES", None)
    if isinstance(profiles, dict) and "linkedin_clone" in profiles:
        selectors = profiles["linkedin_clone"]
    else:
        selectors = SEMANTIC_CLONE_SELECTORS

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=selectors,
        max_applications=1,
    )

    cache = JsonJobCache(str(tmp_path / "cache.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    page = hostile_browser.get_page()
    # Aguarda o termino da transicao assincrona de submissao no React (1.0s)
    hostile_browser.wait_for_loader_to_disappear(timeout=10000)

    dom_seed = page.locator("main[data-seed]").first.get_attribute("data-seed")
    print(f"\n[ Sandbox Run ] DOM Seed capturada no Pytest: {dom_seed}")

    # 1. ASSERCAO NEGATIVA OBRIGATORIA: Zero interacao com Honeypots ou bypass de Overlay
    assert_no_honeypot_compromised(page)

    # Verifica tambem que o overlay intrusivo foi genuinamente fechado e nao burlado
    overlay_locator = page.locator('[aria-label="Cookie and Premium Interception"]')
    assert overlay_locator.count() == 0, (
        "O Overlay intrusivo permaneceu aberto na tela; o clique foi forcado indevidamente!"
    )

    # 2. ASSERCAO DE ESTADO OBRIGATORIA: Tela final de "Sucesso" renderizada e extraida do DOM
    success_locator = page.locator('[data-testid="modal-submission-success"]')
    success_locator.wait_for(state="visible", timeout=5000)
    extracted_success_text = success_locator.inner_text().strip()

    assert "Candidatura enviada com sucesso!" in extracted_success_text, (
        f"Tela de sucesso nao encontrada no modal! Texto extraido: {extracted_success_text!r}"
    )

    session_success = page.evaluate(
        "() => window.sessionStorage.getItem('modal_submission_success')"
    )
    assert session_success == "Candidatura enviada com sucesso!"

    # 3. Validacao do funil da camada de aplicacao (Vaga 1 aplicada, Vaga 2 nao processada pelo teto=1)
    assert len(jobs) == 2, f"Deveria extrair apenas as 2 vagas visiveis (ignorando o card honeypot): {jobs}"
    assert jobs[0].title == "Vaga 1"
    expected_company = "Empresa Acme" if selectors.get("job_card_company") else ""
    assert jobs[0].company == expected_company
    assert jobs[0].status == JobStatus.APPLIED


@pytest.mark.external
def test_hostile_clone_complex_job_discarded_without_honeypot(
    hostile_clone_server: str,
    hostile_browser: BrowserService,
    tmp_path,
):
    """
    Executa o lote completo (max_applications=5) contra o clone Next.js:
    - Vaga 1 (Simples, 2 passos): APPLIED (ignorando os 2 inputs honeypot required ocultos no form).
    - Vaga 2 (Complexa, textarea obrigatorio visivel no passo 2): SKIPPED_COMPLEX (descartada pelo 3C).
    - Assercao Negativa: Zero honeypots acionados em todo o ciclo.
    """
    profiles = getattr(search_request_module, "SELECTOR_PROFILES", None)
    if isinstance(profiles, dict) and "linkedin_clone" in profiles:
        selectors = profiles["linkedin_clone"]
    else:
        selectors = SEMANTIC_CLONE_SELECTORS

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=selectors,
        max_applications=5,
    )

    cache = JsonJobCache(str(tmp_path / "cache.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    page = hostile_browser.get_page()
    hostile_browser.wait_for_loader_to_disappear(timeout=10000)

    # Assercao Negativa Anti-Trapaca
    assert_no_honeypot_compromised(page)

    assert len(jobs) == 2
    by_title = {j.title: j for j in jobs}
    assert by_title["Vaga 1"].status == JobStatus.APPLIED
    assert by_title["Vaga 2 (Complexa)"].status == JobStatus.SKIPPED_COMPLEX
