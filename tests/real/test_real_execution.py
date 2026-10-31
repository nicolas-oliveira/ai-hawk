import pytest
from tests.real.mock_server import start_local_server
from src.infrastructure.browser_service import BrowserService
from src.application.app_service import AppService
from src.application.dtos.search_request import SearchRequest, LINKEDIN_DEFAULT_SELECTORS
from src.domain.entities.job import Job, JobStatus


@pytest.fixture(scope="module")
def local_http_server():
    """Inicia o servidor HTTP local servindo as rotas da plataforma real."""
    server, base_url = start_local_server()
    yield base_url
    server.shutdown()


@pytest.fixture
def real_browser_service(temp_session_dir):
    """Instancia real do BrowserService com Chromium do Patchright e perfil isolado."""
    service = BrowserService(
        platform="real_suite",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    yield service
    service.close()


def test_real_lazy_loading_and_deduplication(real_browser_service, local_http_server):
    """
    REAL-01: Valida o lazy loading fisico do Chromium real.
    Rola o container com overflow, aciona o listener JS real no DOM
    e coleta todas as vagas anexadas dinamicamente, canonizando URLs.
    """
    search_url = f"{local_http_server}/jobs/search"
    request = SearchRequest(
        platform="linkedin",
        static_urls=[search_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    jobs = app_service._collect_jobs(request)

    # Deve ter extraido as 5 vagas reais (2 iniciais + 3 carregadas via scroll lazy loading)
    assert len(jobs) == 5
    assert all(isinstance(j, Job) for j in jobs)
    assert all(j.status == JobStatus.PENDING for j in jobs)

    # Todas as URLs foram devidamente limpas e canonizadas sem query strings
    assert jobs[0].url == f"{local_http_server}/jobs/view/101/"
    assert jobs[1].url == f"{local_http_server}/jobs/view/102/"
    assert jobs[2].url == f"{local_http_server}/jobs/view/103/"
    assert jobs[3].url == f"{local_http_server}/jobs/view/104/"
    assert jobs[4].url == f"{local_http_server}/jobs/view/105/"


def test_real_job_101_direct_submission(real_browser_service, local_http_server):
    """
    REAL-02: Fluxo feliz direto real.
    Clica em Easy Apply -> modal abre -> Heuristica 3C valida -> Submit real -> APPLIED.
    """
    job_url = f"{local_http_server}/jobs/view/101/"
    job = Job(url=job_url, platform="linkedin", title="Senior Python", company="TechCorp")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.APPLIED


def test_real_job_102_css_trap_anti_ban(real_browser_service, local_http_server):
    """
    REAL-03: Blindagem contra Armadilhas de CSS (Honeypot / Bot Trap).
    Input obrigatorio com display: none NAO deve acionar falso-positivo de campo vazio.
    A Heuristica 3C ignora elemento invisivel e avanca para submissao real.
    """
    job_url = f"{local_http_server}/jobs/view/102/"
    job = Job(url=job_url, platform="linkedin", title="Backend Dev", company="SecureSystems")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.APPLIED


def test_real_job_103_complex_modal_discards_cleanly(real_browser_service, local_http_server):
    """
    REAL-04: Deteccao real de campo obrigatorio vazio (Heuristica 3C).
    Deve identificar complexidade no DOM real, clicar em Close,
    clicar na confirmacao de Discard e marcar SKIPPED_COMPLEX.
    """
    job_url = f"{local_http_server}/jobs/view/103/"
    job = Job(url=job_url, platform="linkedin", title="Data Engineer", company="BigData Inc")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.SKIPPED_COMPLEX


def test_real_job_104_multi_step_submission(real_browser_service, local_http_server):
    """
    REAL-05: Formulario multi-etapas real.
    Passo 1: Next -> DOM renderiza Passo 2 -> Submit -> APPLIED.
    """
    job_url = f"{local_http_server}/jobs/view/104/"
    job = Job(url=job_url, platform="linkedin", title="DevOps", company="CloudNative")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.APPLIED


def test_real_job_105_external_redirect_skipped_complex(real_browser_service, local_http_server):
    """
    REAL-06: Vaga sem candidatura simplificada (apenas link externo).
    Identifica ausencia do botao Easy Apply e marca SKIPPED_COMPLEX com seguranca.
    """
    job_url = f"{local_http_server}/jobs/view/105/"
    job = Job(url=job_url, platform="linkedin", title="Frontend", company="WebSoft")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.SKIPPED_COMPLEX


def test_real_full_orchestration_with_max_applications_ceiling(real_browser_service, local_http_server):
    """
    REAL-07: Execucao completa de ponta a ponta com teto de candidaturas.
    Carrega listagem via lazy loading, processa vaga 101 (APPLIED) e 102 (APPLIED),
    atinge a cota max_applications=2 e encerra imediatamente sem tocar nas demais.
    """
    search_url = f"{local_http_server}/jobs/search"
    request = SearchRequest(
        platform="linkedin",
        static_urls=[search_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_applications=2,
    )

    app_service = AppService(real_browser_service)
    processed_jobs = app_service.run(request)

    assert len(processed_jobs) == 5

    # Vagas 101 e 102 foram aplicadas
    applied = [j for j in processed_jobs if j.status == JobStatus.APPLIED]
    assert len(applied) == 2

    # Vagas 103, 104 e 105 foram ignoradas pelo teto e permaneceram PENDING
    pending = [j for j in processed_jobs if j.status == JobStatus.PENDING]
    assert len(pending) == 3
