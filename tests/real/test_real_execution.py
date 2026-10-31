import pytest
from src.application.app_service import AppService
from src.application.dtos.search_request import SearchRequest, LINKEDIN_DEFAULT_SELECTORS
from src.domain.entities.job import Job, JobStatus


def test_real_lazy_loading_scroll_physical_trigger(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 1:
    Mede a fisica real do evento de scroll em container com overflow no Chromium.
    Dispara o listener de scroll real e anexa 3 novos cards de vagas dinamicamente.
    """
    search_url = f"{stress_http_server}/jobs/search"
    request = SearchRequest(
        platform="linkedin",
        static_urls=[search_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    jobs = app_service._collect_jobs(request)

    # Deve extrair as 5 vagas reais (2 iniciais + 3 disparadas pelo evento scroll)
    assert len(jobs) == 5
    assert all(isinstance(j, Job) for j in jobs)
    assert all(j.status == JobStatus.PENDING for j in jobs)

    # URLs canonizadas de forma estavel
    assert jobs[0].url == f"{stress_http_server}/jobs/view/201/"
    assert jobs[1].url == f"{stress_http_server}/jobs/view/202/"
    assert jobs[2].url == f"{stress_http_server}/jobs/view/203/"
    assert jobs[3].url == f"{stress_http_server}/jobs/view/204/"
    assert jobs[4].url == f"{stress_http_server}/jobs/view/205/"


def test_real_job_201_async_modal_transition(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 2 (CHOQUE DE REALIDADE):
    O modal abre com delay real de 300ms (animacao/transicao do front-end SPA).
    Testa se o AppService aguarda a estabilizacao do DOM antes de inspecionar ou abortar.
    """
    job_url = f"{stress_http_server}/jobs/view/201/"
    job = Job(url=job_url, platform="linkedin", title="Senior Python", company="TechCorp")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.APPLIED


def test_real_job_202_advanced_css_trap_honeypot(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 3 (ANTI-BAN & BLINDAGEM):
    Honeypots e bot-traps reais: inputs com display: none, visibility: hidden e pais ocultos.
    A Heuristica 3C deve inspecionar apenas nos computados visiveis (checkVisibility),
    impedindo tentativas de interacao que denunciam bot e causam banimento imediato.
    """
    job_url = f"{stress_http_server}/jobs/view/202/"
    job = Job(url=job_url, platform="linkedin", title="Backend Dev", company="SecureSystems")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.APPLIED


def test_real_job_203_complex_modal_delayed_discard_popup(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 4:
    Campo obrigatorio visivel vazio.
    Ao clicar em Close, o popup de confirmacao de descarte demora 200ms para renderizar.
    Testa se o fluxo aguarda e clica em discard_button, garantindo fechamento limpo.
    """
    job_url = f"{stress_http_server}/jobs/view/203/"
    job = Job(url=job_url, platform="linkedin", title="Data Engineer", company="BigData")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.SKIPPED_COMPLEX


def test_real_job_204_multi_step_delayed_transition(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 5:
    Formulario em 2 etapas onde o passo 2 demora 250ms para transicionar apos Next.
    """
    job_url = f"{stress_http_server}/jobs/view/204/"
    job = Job(url=job_url, platform="linkedin", title="DevOps", company="CloudNative")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.APPLIED


def test_real_job_205_external_redirect_skipped_complex(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 6:
    Vaga externa sem Easy Apply. Marca SKIPPED_COMPLEX sem estourar excecao.
    """
    job_url = f"{stress_http_server}/jobs/view/205/"
    job = Job(url=job_url, platform="linkedin", title="Frontend", company="WebSoft")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    assert job.status == JobStatus.SKIPPED_COMPLEX


def test_real_full_orchestration_with_max_applications_ceiling(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 7:
    Loop completo de ponta a ponta com teto de candidaturas max_applications=2.
    """
    search_url = f"{stress_http_server}/jobs/search"
    request = SearchRequest(
        platform="linkedin",
        static_urls=[search_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_applications=2,
    )

    app_service = AppService(real_browser_service)
    processed_jobs = app_service.run(request)

    assert len(processed_jobs) == 5

    # Vagas 201 e 202 foram aplicadas
    applied = [j for j in processed_jobs if j.status == JobStatus.APPLIED]
    assert len(applied) == 2

    # Vagas restantes permanecem PENDING
    pending = [j for j in processed_jobs if j.status == JobStatus.PENDING]
    assert len(pending) == 3
