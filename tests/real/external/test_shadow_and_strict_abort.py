"""
Testes adversariais de Shadow Mode, Parada Estrita (desafios na listagem e na vaga,
modal que nao abre, modal lento) e Evidencia de Envio / SUBMITTING (Portao A, Bloco 1).
Validados contra o clone local do LinkedIn (http://localhost:3000).
"""
import pytest

from src.application.app_service import AbortReason, AppService, JsonJobCache
from src.application.dtos import search_request as search_request_module
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import Job, JobStatus, ReviewReason
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


def test_base_flow_confirmation_inside_open_modal_applies_and_closes_dialog(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Passo A5 (C1): No fluxo base da v1.5 (sem ?scenario=), o modal permanece aberto
    apos o Submit exibindo [data-testid='modal-submission-success'] dentro do dialogo.
    A vaga termina APPLIED e o AppService fecha o dialogo clicando em close_button.
    """
    selectors = _clone_selectors()
    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=selectors,
        max_applications=1,
    )
    cache = JsonJobCache(str(tmp_path / "cache_base_c1.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    page = hostile_browser.get_page()
    assert len(jobs) == 2
    assert jobs[0].status == JobStatus.APPLIED
    assert app_service.last_abort_reason is None
    assert page.locator(selectors["modal_container"]).count() == 0


def test_close_on_submit_scenario_applies_when_modal_closes_with_banner_outside(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Passo A5 (?scenario=close-on-submit): O modal fecha sozinho no Submit e o banner
    de confirmacao aparece nos detalhes da vaga fora do modal -> APPLIED sem precisar
    clicar em close_button.
    """
    selectors = _clone_selectors()
    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[f"{hostile_clone_server}/?scenario=close-on-submit"],
        selectors=selectors,
        max_applications=1,
    )
    cache = JsonJobCache(str(tmp_path / "cache_close_on_submit.json"))
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.APPLIED
    assert app_service.last_abort_reason is None


def test_no_confirm_scenario_marks_manual_review_and_halts_batch_in_strict_mode(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Passo A5 (?scenario=no-confirm + C4): O modal fecha apos o Submit sem elemento de
    confirmacao -> vaga vira MANUAL_REVIEW (CONFIRMATION_MISSING), e gravada no cache
    antes da parada, e o lote para com MANUAL_REVIEW_STOP sem abrir a segunda vaga.
    """
    selectors = _clone_selectors()
    cache = JsonJobCache(str(tmp_path / "cache_no_confirm.json"))
    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[f"{hostile_clone_server}/?scenario=no-confirm"],
        selectors=selectors,
        max_applications=5,
        strict_abort=True,
    )
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 2
    assert jobs[0].status == JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason == ReviewReason.CONFIRMATION_MISSING
    assert jobs[1].status == JobStatus.PENDING
    assert app_service.last_abort_reason == AbortReason.MANUAL_REVIEW_STOP.format(url=jobs[0].url)
    reloaded = JsonJobCache(str(tmp_path / "cache_no_confirm.json"))
    assert reloaded.get(jobs[0].url) == JobStatus.MANUAL_REVIEW


def test_stuck_submit_scenario_marks_manual_review_and_halts_batch_in_strict_mode(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Passo A5 (?scenario=stuck-submit + C4): O modal permanece aberto apos o Submit sem
    confirmacao -> vaga vira MANUAL_REVIEW (MODAL_STILL_OPEN) e o lote para na hora
    com MANUAL_REVIEW_STOP sem abrir a segunda vaga.
    """
    selectors = _clone_selectors()
    cache = JsonJobCache(str(tmp_path / "cache_stuck_submit.json"))
    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[f"{hostile_clone_server}/?scenario=stuck-submit"],
        selectors=selectors,
        max_applications=5,
        strict_abort=True,
    )
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    assert len(jobs) == 2
    assert jobs[0].status == JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason == ReviewReason.MODAL_STILL_OPEN
    assert jobs[1].status == JobStatus.PENDING
    assert app_service.last_abort_reason == AbortReason.MANUAL_REVIEW_STOP.format(url=jobs[0].url)
    reloaded = JsonJobCache(str(tmp_path / "cache_stuck_submit.json"))
    assert reloaded.get(jobs[0].url) == JobStatus.MANUAL_REVIEW


def test_real_submission_without_submit_confirmation_refuses_before_opening_any_url(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Passo A5 (C2): Envio real (shadow_mode=False) sem 'submit_confirmation' no perfil
    de seletores recusa o lote no inicio do run() com SUBMIT_CONFIRMATION_REQUIRED
    sem abrir nenhuma URL.
    """
    selectors = dict(_clone_selectors())
    selectors.pop("submit_confirmation", None)

    hostile_browser.navigate("about:blank")
    cache = JsonJobCache(str(tmp_path / "cache_c2.json"))
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
    assert app_service.last_abort_reason == AbortReason.SUBMIT_CONFIRMATION_REQUIRED
    assert hostile_browser.get_current_url() == "about:blank"


def test_history_write_failure_on_submitting_discards_modal_without_submit_click(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Passo A5 (C3): Se record_submitting falhar em disco (pai do arquivo de cache e um
    arquivo regular gerando OSError), o motor NAO clica em Submit, descarta o dialogo,
    mantem a vaga PENDING, desfaz SUBMITTING em memoria no cache e para o lote com
    HISTORY_WRITE_FAILED.
    """
    blocking_parent = tmp_path / "regular_file_not_dir"
    blocking_parent.write_text("bloqueio de diretorio pai", encoding="utf-8")
    broken_cache_path = blocking_parent / "jobs_history.json"
    cache = JsonJobCache(str(broken_cache_path))

    selectors = _clone_selectors()
    request = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=selectors,
        max_applications=5,
    )
    app_service = AppService(hostile_browser, cache=cache)
    jobs = app_service.run(request)

    page = hostile_browser.get_page()
    assert len(jobs) == 2
    assert all(j.status == JobStatus.PENDING for j in jobs)
    assert cache.get(jobs[0].url) is None
    assert app_service.last_abort_reason == AbortReason.HISTORY_WRITE_FAILED.format(url=jobs[0].url)
    assert page.evaluate("() => window.sessionStorage.getItem('modal_submission_success')") is None


def test_submission_evidence_and_submitting_crash_recovery(
    hostile_clone_server, hostile_browser, tmp_path
):
    """
    Valida no navegador real:
    1. Crash recovery: SUBMITTING persistido no cache antes de reinicio -> MANUAL_REVIEW sem reabrir.
    2. Regra 1A: envio real sem cache para no Submit com last_abort_reason e vaga PENDING.
    """
    base_selectors = _clone_selectors()

    # 1. Crash recovery: SUBMITTING persistido no cache antes de reinicio -> MANUAL_REVIEW sem reabrir
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
    assert by_url[job_1_url].review_reason == ReviewReason.INTERRUPTED_SUBMISSION

    # 2. Regra 1A: envio real sem cache para no Submit e mantem vaga PENDING
    req_no_cache = SearchRequest(
        platform="linkedin_clone",
        static_urls=[hostile_clone_server],
        selectors=base_selectors,
        max_applications=1,
    )
    svc_no_cache = AppService(hostile_browser, cache=None)
    jobs_no_cache = svc_no_cache.run(req_no_cache)
    assert jobs_no_cache[0].status == JobStatus.PENDING
    assert svc_no_cache.last_abort_reason == AbortReason.HISTORY_REQUIRED.format(url=jobs_no_cache[0].url)
