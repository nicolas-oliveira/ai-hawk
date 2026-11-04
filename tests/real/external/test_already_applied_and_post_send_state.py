"""
Testes adversariais de Reconhecimento de Vaga Ja Candidatada pela Pagina (C2/A3)
e Adaptadores de Porta (wait_until_hidden e job_shows_applied).
Validados contra o clone local do LinkedIn (http://localhost:3000).
"""
import pytest
from src.application.app_service import AbortReason, AppService, JsonJobCache
from src.application.dtos import search_request as search_request_module
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import JobStatus, ReviewReason
from tests.real.external.test_navigation_hostile import SEMANTIC_CLONE_SELECTORS

pytestmark = pytest.mark.external


def _clone_selectors() -> dict:
    profiles = getattr(search_request_module, "SELECTOR_PROFILES", None)
    if isinstance(profiles, dict) and "linkedin_clone" in profiles:
        return dict(profiles["linkedin_clone"])
    return dict(SEMANTIC_CLONE_SELECTORS)


def test_job_shows_applied_instant_reading_skips_modal_and_marks_already_applied(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Cenario C2/A3 (1): Vaga com o selo ja visivel ao abrir (?scenario=already-applied).
    O motor detecta com leitura instantanea (timeout=0), marca ALREADY_APPLIED,
    faz zero cliques no modal e o dialogo nunca abre.
    """
    selectors = _clone_selectors()
    scenario_url = f"{hostile_clone_server}/?scenario=already-applied"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=5,
    )
    cache = JsonJobCache(str(tmp_path / "cache_already_applied.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.ALREADY_APPLIED
    assert app_service.last_abort_reason is None

    # Confirma que foi persistido no cache como ALREADY_APPLIED
    reloaded = JsonJobCache(str(tmp_path / "cache_already_applied.json"))
    assert reloaded.get(jobs[0]) == JobStatus.ALREADY_APPLIED


def test_job_post_submission_with_confirmation_and_applied_state_marks_applied(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Cenario C2/A3 (2): Vaga que ganha o selo depois do envio, com atraso menor que 3s.
    Submit concluido + confirmacao vista + estado atualizado -> vaga marcada como APPLIED.
    """
    selectors = _clone_selectors()
    scenario_url = f"{hostile_clone_server}/"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=1,
    )
    cache = JsonJobCache(str(tmp_path / "cache_applied_ok.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) >= 1
    assert jobs[0].status == JobStatus.APPLIED
    assert app_service.last_abort_reason is None


def test_job_post_submission_confirmation_without_state_change_goes_to_manual_review(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Cenario C2/A3 (3): Confirmacao sem selo (?scenario=confirm-without-state).
    Modal exibe banner de confirmacao mas o estado na pagina nao muda.
    Desfecho obrigatorio: MANUAL_REVIEW com motivo STATE_NOT_CONFIRMED e parada estrita.
    """
    selectors = _clone_selectors()
    scenario_url = f"{hostile_clone_server}/?scenario=confirm-without-state"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=5,
        strict_abort=True,
    )
    cache = JsonJobCache(str(tmp_path / "cache_confirm_no_state.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) >= 1
    assert jobs[0].status == JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason == ReviewReason.STATE_NOT_CONFIRMED
    assert app_service.last_abort_reason == AbortReason.MANUAL_REVIEW_STOP.format(url=jobs[0].url)


def test_job_post_submission_state_without_confirmation_goes_to_manual_review(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Cenario C2/A3 (4): Selo sem confirmacao (?scenario=state-without-confirm).
    Estado na pagina muda para candidatada mas o modal fecha sem confirmacao.
    Desfecho obrigatorio: MANUAL_REVIEW com motivo STATE_WITHOUT_CONFIRMATION e parada estrita.
    """
    selectors = _clone_selectors()
    scenario_url = f"{hostile_clone_server}/?scenario=state-without-confirm"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=5,
        strict_abort=True,
    )
    cache = JsonJobCache(str(tmp_path / "cache_state_no_confirm.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) >= 1
    assert jobs[0].status == JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason == ReviewReason.STATE_WITHOUT_CONFIRMATION
    assert app_service.last_abort_reason == AbortReason.MANUAL_REVIEW_STOP.format(url=jobs[0].url)


def test_job_late_applied_state_after_missing_apply_button_marks_already_applied(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Cenario C2/A3 (5): Selo que pinta so depois da leitura instantanea (400ms),
    com botao de candidatura ausente (?scenario=late-applied).
    A releitura com espera (timeout=3000ms) detecta o selo e marca ALREADY_APPLIED (e nao SKIPPED_COMPLEX).
    """
    selectors = _clone_selectors()
    scenario_url = f"{hostile_clone_server}/?scenario=late-applied"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=5,
    )
    cache = JsonJobCache(str(tmp_path / "cache_late_applied.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.ALREADY_APPLIED
    assert app_service.last_abort_reason is None


def test_real_submission_without_applied_state_refuses_before_opening_any_url(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Contrato C2/A3: Envio real (shadow_mode=False) sem 'applied_state' no perfil
    recusa o lote antes de abrir qualquer vaga com JOB_STATE_REQUIRED.
    """
    selectors = dict(_clone_selectors())
    selectors.pop("applied_state", None)

    hostile_browser.navigate("about:blank")
    cache = JsonJobCache(str(tmp_path / "cache_job_state_req.json"))
    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=selectors,
        max_applications=5,
        shadow_mode=False,
    )
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert jobs == []
    assert app_service.last_abort_reason == AbortReason.JOB_STATE_REQUIRED
    assert hostile_browser.get_current_url() == "about:blank"
