"""
Testes adversariais de Shadow Mode, Parada Estrita (desafios na listagem e na vaga,
modal que nao abre, modal lento) e Evidencia de Envio / SUBMITTING (Portao A, Bloco 1).
Validados contra o clone local do LinkedIn (http://localhost:3000).
"""
import pytest

from src.application.app_service import AppService, JsonJobCache
from src.application.dtos import search_request as search_request_module
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import Job, JobStatus
from tests.real.external.test_navigation_hostile import SEMANTIC_CLONE_SELECTORS

pytestmark = pytest.mark.external


def _clone_selectors() -> dict:
    profiles = getattr(search_request_module, "SELECTOR_PROFILES", None)
    if isinstance(profiles, dict) and "linkedin_clone" in profiles:
        return dict(profiles["linkedin_clone"])
    return dict(SEMANTIC_CLONE_SELECTORS)


def test_shadow_mode_dry_run_never_submits(hostile_clone_server, hostile_browser):
    """
    CONTRATO SHADOW MODE (Modo Simulacao / Dry-Run):
    1. Com shadow_mode=True no SearchRequest, o motor percorre a vaga e o modal
       ate a tela de envio, mas o botao final ('Submit application') NUNCA e clicado.
    2. A vaga termina com status SIMULATED (nunca APPLIED).
    3. O DOM e o sessionStorage do clone confirmam ZERO envios reais.
    """
    selectors = _clone_selectors()
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

    assert len(jobs) > 0, "Deveria ter inspecionado ao menos 1 vaga no clone"
    assert all(j.status != JobStatus.APPLIED for j in jobs)
    assert jobs[0].status == JobStatus.SIMULATED
    assert page.locator('[data-testid="modal-submission-success"]').count() == 0

    session_success = page.evaluate(
        "() => window.sessionStorage.getItem('modal_submission_success')"
    )
    assert session_success is None


@pytest.mark.parametrize(
    "route_path",
    [
        "/checkpoint/challenge",
        "/captcha",
        "/unusual-traffic",
        "/verify-phone",
    ],
)
def test_strict_abort_on_unexpected_screen_or_captcha(
    hostile_clone_server, hostile_browser, route_path
):
    """
    CONTRATO PARADA ESTRITA NAS 4 ROTAS DE DESAFIO NA LISTAGEM:
    1. Cada rota (/checkpoint/challenge, /captcha, /unusual-traffic, /verify-phone)
       como primeira URL da fila encerra a sessao imediatamente.
    2. Zero vagas coletadas e a segunda URL nunca e aberta.
    3. last_abort_reason preenchido com motivo claro.
    """
    selectors = _clone_selectors()
    challenge_url = f"{hostile_clone_server}{route_path}"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[challenge_url, hostile_clone_server],
        selectors=selectors,
        max_applications=5,
    )

    app_service = AppService(hostile_browser)
    jobs = app_service.run(request)

    assert len(jobs) == 0, f"Deveria abortar com 0 vagas em {route_path}, obteve: {jobs}"
    assert app_service.last_abort_reason is not None
    assert "parada estrita" in app_service.last_abort_reason.lower()
    assert hostile_browser.get_current_url().startswith(challenge_url)


def test_strict_abort_variant_marker_only_neutral_url(
    hostile_clone_server, hostile_browser
):
    """
    Variante so com marcador DOM ([data-aihawk-challenge]) em URL neutra (/notice/security-check):
    Para na primeira URL sem abrir a segunda.
    """
    selectors = _clone_selectors()
    neutral_challenge_url = f"{hostile_clone_server}/notice/security-check"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[neutral_challenge_url, hostile_clone_server],
        selectors=selectors,
        max_applications=5,
    )

    app_service = AppService(hostile_browser)
    jobs = app_service.run(request)

    assert len(jobs) == 0
    assert app_service.last_abort_reason is not None
    assert "data-aihawk-challenge" in app_service.last_abort_reason
    assert hostile_browser.get_current_url().startswith(neutral_challenge_url)


def test_strict_abort_variant_url_only_without_marker(
    hostile_clone_server, hostile_browser
):
    """
    Variante so com padrao de URL (/checkpoint/url-only) sem marcador DOM:
    Para na primeira URL pela precedencia de abort_url_pattern sem abrir a segunda.
    """
    selectors = _clone_selectors()
    url_only_challenge = f"{hostile_clone_server}/checkpoint/url-only"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[url_only_challenge, hostile_clone_server],
        selectors=selectors,
        max_applications=5,
    )

    app_service = AppService(hostile_browser)
    jobs = app_service.run(request)

    assert len(jobs) == 0
    assert app_service.last_abort_reason is not None
    assert "parada estrita" in app_service.last_abort_reason.lower()
    assert "checkpoint" in app_service.last_abort_reason.lower()
    assert hostile_browser.get_current_url().startswith(url_only_challenge)


def test_strict_abort_on_job_detail_page_halts_batch(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Desafio anti-bot na pagina de detalhe da vaga (e nao so na listagem):
    A primeira vaga exibe [data-aihawk-challenge]; o lote para imediatamente,
    a vaga permanece PENDING e a segunda vaga nunca e aberta.
    """
    selectors = _clone_selectors()
    scenario_url = f"{hostile_clone_server}/?scenario=job-challenge"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=5,
    )

    cache = JsonJobCache(str(tmp_path / "cache.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 2
    assert all(j.status == JobStatus.PENDING for j in jobs)
    assert app_service.last_abort_reason is not None
    assert "parada estrita" in app_service.last_abort_reason.lower()
    assert "job-challenge" in app_service.last_abort_reason


def test_strict_abort_when_modal_does_not_open(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Modal que nao abre apos clique em Apply:
    Com strict_abort=True (padrao 2A), vira parada estrita com last_abort_reason
    ('parada estrita: modal nao abriu em <url>'), a vaga fica PENDING (nao ERROR)
    e a vaga seguinte nao e tentada.
    """
    selectors = _clone_selectors()
    scenario_url = f"{hostile_clone_server}/?scenario=broken-modal"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=5,
    )

    cache = JsonJobCache(str(tmp_path / "cache.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 2
    assert all(j.status == JobStatus.PENDING for j in jobs), (
        f"Modal que nao abre deve deixar vagas PENDING e nao ERROR: {jobs}"
    )
    assert app_service.last_abort_reason is not None
    assert "modal nao abriu" in app_service.last_abort_reason.lower()
    assert "job-broken-modal" in app_service.last_abort_reason


def test_slow_modal_opens_within_timeout_and_applies(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Modal lento que abre dentro do prazo do element_exists (600ms < 3000ms):
    O lote segue normal e conclui a candidatura como APPLIED.
    """
    selectors = {
        **_clone_selectors(),
        "submit_confirmation": "[data-testid='modal-submission-success']",
    }
    scenario_url = f"{hostile_clone_server}/?scenario=slow-modal"

    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[scenario_url],
        selectors=selectors,
        max_applications=5,
    )

    cache = JsonJobCache(str(tmp_path / "cache.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.APPLIED
    assert app_service.last_abort_reason is None


def test_slow_modal_exceeding_injected_timeout_triggers_strict_abort(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Passo A1: Com visibility_timeout_ms=1000 injetado no motor (folgado para o restante
    da navegacao) e modal lento configurado com delayMs=2500 no clone, o element_exists
    estoura o prazo de abertura do modal e aciona parada estrita (MODAL_NOT_OPENED)
    mantendo a vaga PENDING.
    """
    selectors = {
        **_clone_selectors(),
        "submit_confirmation": "[data-testid='modal-submission-success']",
    }
    scenario_url = f"{hostile_clone_server}/?scenario=slow-modal&delayMs=2500"

    prev_timeout = hostile_browser.visibility_timeout_ms
    hostile_browser.visibility_timeout_ms = 1000
    try:
        request = SearchRequest(
            platform="linkedin_clone",
            static_urls=[scenario_url],
            selectors=selectors,
            max_applications=5,
        )
        cache = JsonJobCache(str(tmp_path / "cache_slow_abort.json"))
        app_service = AppService(hostile_browser, cache=cache)
        jobs = app_service.run(request)
    finally:
        hostile_browser.visibility_timeout_ms = prev_timeout

    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.PENDING
    assert app_service.last_abort_reason is not None
    assert "modal nao abriu" in app_service.last_abort_reason.lower()


def test_submission_evidence_and_submitting_crash_recovery(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Valida no navegador real:
    1. Submit com modal que nao fecha -> MANUAL_REVIEW (nunca APPLIED nem ERROR).
    2. Submit sem confirmacao visivel -> MANUAL_REVIEW.
    3. Vaga gravada como SUBMITTING antes de reinicio -> vira MANUAL_REVIEW sem reabrir.
    4. Regra 1A: envio real sem cache para no Submit com last_abort_reason e vaga PENDING.
    """
    base_selectors = {
        **_clone_selectors(),
        "submit_confirmation": "[data-testid='modal-submission-success']",
    }

    # 1. Submit com modal que nao fecha -> MANUAL_REVIEW
    cache_stuck = JsonJobCache(str(tmp_path / "cache_stuck.json"))
    req_stuck = SearchRequest(
        platform="linkedin_clone",
        static_urls=[f"{hostile_clone_server}/?scenario=stuck-submit"],
        selectors=base_selectors,
        max_applications=1,
    )
    svc_stuck = AppService(hostile_browser, cache=cache_stuck)
    jobs_stuck = svc_stuck.run(req_stuck)
    assert len(jobs_stuck) == 1
    assert jobs_stuck[0].status == JobStatus.MANUAL_REVIEW

    # 2. Submit sem elemento de confirmacao -> MANUAL_REVIEW
    cache_noconf = JsonJobCache(str(tmp_path / "cache_noconf.json"))
    req_noconf = SearchRequest(
        platform="linkedin_clone",
        static_urls=[f"{hostile_clone_server}/?scenario=no-confirm"],
        selectors=base_selectors,
        max_applications=1,
    )
    svc_noconf = AppService(hostile_browser, cache=cache_noconf)
    jobs_noconf = svc_noconf.run(req_noconf)
    assert len(jobs_noconf) == 1
    assert jobs_noconf[0].status == JobStatus.MANUAL_REVIEW

    # 3. Crash recovery: SUBMITTING persistido no cache antes de reinicio -> MANUAL_REVIEW sem reabrir
    cache_crash = JsonJobCache(str(tmp_path / "cache_crash.json"))
    job_1_url = f"{hostile_clone_server}/?jobId=job-1"
    dangling_job = Job(url=job_1_url, platform="linkedin_clone", title="Vaga 1", company="Empresa Acme")
    dangling_job.mark_submitting()
    cache_crash.record_submitting(dangling_job)

    req_crash = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=base_selectors,
        max_applications=1,
    )
    svc_crash = AppService(hostile_browser, cache=cache_crash)
    jobs_crash = svc_crash.run(req_crash)
    by_url = {j.url: j for j in jobs_crash}
    assert by_url[job_1_url].status == JobStatus.MANUAL_REVIEW

    # 4. Regra 1A: envio real sem cache para no Submit e mantem vaga PENDING
    req_no_cache = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=base_selectors,
        max_applications=1,
    )
    svc_no_cache = AppService(hostile_browser, cache=None)
    jobs_no_cache = svc_no_cache.run(req_no_cache)
    assert jobs_no_cache[0].status == JobStatus.PENDING
    assert svc_no_cache.last_abort_reason is not None
