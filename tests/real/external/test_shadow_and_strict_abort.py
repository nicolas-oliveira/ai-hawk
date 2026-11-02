"""
Testes adversariais de Shadow Mode e Parada Estrita (meta v1.5).
Validados contra o clone local do LinkedIn (http://localhost:3000).
"""
import os
import pytest

from src.application.app_service import AppService
from src.application.dtos import search_request as search_request_module
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import JobStatus
from tests.real.external.test_navigation_hostile import SEMANTIC_CLONE_SELECTORS

pytestmark = pytest.mark.external


def test_shadow_mode_dry_run_never_submits(hostile_clone_server, hostile_browser):
    """
    CONTRATO SHADOW MODE (Modo Simulacao / Dry-Run):
    1. Com shadow_mode=True no SearchRequest, o motor percorre a vaga e o modal
       ate a tela de envio, mas o botao final ('Submit application') NUNCA e clicado.
    2. A vaga termina com status SIMULATED (nunca APPLIED).
    3. O DOM e o sessionStorage do clone confirmam ZERO envios reais.
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
        shadow_mode=True,
    )

    app_service = AppService(hostile_browser)
    jobs = app_service.run(request)

    page = hostile_browser.get_page()

    # 1. Nenhuma vaga e marcada como APPLIED; deve ser marcada como SIMULATED
    assert len(jobs) > 0, "Deveria ter inspecionado ao menos 1 vaga no clone"
    assert all(j.status != JobStatus.APPLIED for j in jobs), (
        f"Shadow Mode violado! Vaga marcada como APPLIED: {[j for j in jobs if j.status == JobStatus.APPLIED]}"
    )
    assert jobs[0].status == JobStatus.SIMULATED

    # 2. No DOM do clone, a mensagem de sucesso de envio nao existe
    assert page.locator('[data-testid="modal-submission-success"]').count() == 0

    # 3. No sessionStorage do clone, nenhum envio foi registrado
    session_success = page.evaluate(
        "() => window.sessionStorage.getItem('modal_submission_success')"
    )
    assert session_success is None, (
        f"Shadow Mode violado! modal_submission_success encontrado no sessionStorage: {session_success}"
    )


def test_strict_abort_on_unexpected_screen_or_captcha(
    hostile_clone_server, hostile_browser
):
    """
    CONTRATO PARADA ESTRITA (Circuit Breaker Imediato contra Anti-Bot):
    1. Com strict_abort=True e selectors['abort_indicator'] configurado, qualquer
       tela inesperada (ex: rota de captcha/checkpoint simulada em '/checkpoint')
       encerra a sessao IMEDIATAMENTE na primeira ocorrencia.
    2. Nenhuma vaga subsequente da fila deve ser tentada.
    3. last_abort_reason do AppService registra o motivo claro citando o indicador.
    """
    profiles = getattr(search_request_module, "SELECTOR_PROFILES", None)
    if isinstance(profiles, dict) and "linkedin_clone" in profiles:
        base_selectors = profiles["linkedin_clone"]
    else:
        base_selectors = SEMANTIC_CLONE_SELECTORS

    selectors = {
        **base_selectors,
        "abort_indicator": "[data-testid='security-checkpoint'], [data-testid='captcha-challenge']",
    }

    checkpoint_url = f"{hostile_clone_server}/checkpoint"

    # Duas URLs na fila: a primeira aponta para a armadilha de checkpoint/captcha
    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[checkpoint_url, hostile_clone_server],
        selectors=selectors,
        max_applications=5,
        strict_abort=True,
    )

    app_service = AppService(hostile_browser)
    jobs = app_service.run(request)

    # 1. Interrupcao imediata: a vaga de checkpoint fica PENDING
    assert len(jobs) >= 1, "Deveria ter detectado ao menos a URL inicial"
    assert jobs[0].status == JobStatus.PENDING

    # 2. O motivo do aborto deve ser registrado com clareza
    abort_reason = getattr(app_service, "last_abort_reason", None)
    assert abort_reason is not None, "last_abort_reason nao foi preenchido na interrupcao"
    assert "parada estrita" in abort_reason.lower()
    assert (
        "security-checkpoint" in abort_reason
        or "captcha-challenge" in abort_reason
    )
