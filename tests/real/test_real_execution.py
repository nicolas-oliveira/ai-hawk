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


def test_real_job_206_overlay_stuck_clicks_anti_bot_trap(real_browser_service, stress_http_server):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 8 (A GUILHOTINA ANTI-BOT DA DIRETORIA):
    Armadilha do Overlay / Next Infinito.
    Testa se o robô dispara uma metralhadora de cliques (mais de 2 vezes) em um botao Next
    que nao muda o estado do DOM, gerando assinatura sintetica e banimento imediato.
    O teste falha se a pagina detectar metralhadora de cliques (> 2 cliques sem avanco).
    """
    job_url = f"{stress_http_server}/jobs/view/206/"
    job = Job(url=job_url, platform="linkedin", title="Full Stack", company="TrapCorp")
    request = SearchRequest(
        platform="linkedin",
        static_urls=[job_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
    )

    app_service = AppService(real_browser_service)
    app_service._process_job(job, request)

    page = real_browser_service.get_page()
    spam_detected = page.evaluate("() => window.__METRALHADORA_DETECTADA__ || 0")
    total_clicks = page.evaluate("() => window.__TOTAL_CLICKS__ || 0")

    # A guilhotina da Diretoria: falha imediatamente se o Claude metralhar o botao Next sem mudanca de tela
    assert spam_detected == 0, (
        f"FALHA GRAVE ANTI-BOT (CONFISSAO DO CLAUDE CONFIRMADA): Metralhadora de cliques disparada! "
        f"O robô clicou {total_clicks} vezes consecutivas no botão Next sem nenhuma mudança de estado no DOM. "
        f"Essa repetição cega dispara alerta imediato no Cloudflare/DataDome e causa banimento de conta!"
    )


def test_real_full_orchestration_with_telemetry_export(real_browser_service, stress_http_server, tmp_path):
    """
    SANTUARIO DO PATCHRIGHT - CENARIO 9:
    Validacao Real de Telemetria no Chromium.
    Executa o AppController completo contra a busca real local, verificando:
    1. Orquestracao completa via CLI controller (AppController.execute).
    2. Sumario textual formatado com caminho do relatorio.
    3. Arquivo telemetry_YYYYMMDD.json criado fisicamente no disco.
    4. Funil de telemetria consistente: total_read == sum(funnel states).
    """
    import json
    from datetime import datetime
    from src.application.app_controller import AppController

    search_url = f"{stress_http_server}/jobs/search/"
    request = SearchRequest(
        platform="linkedin",
        static_urls=[search_url],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_applications=2,
    )

    app_service = AppService(real_browser_service)
    controller = AppController(app_service, reports_dir=str(tmp_path))

    summary = controller.execute(request)

    assert "AIHawk - Resumo da sessao (linkedin)" in summary
    assert "Telemetria:" in summary

    # Verifica arquivo gerado em disco
    today_str = datetime.now().strftime("%Y%m%d")
    telemetry_file = tmp_path / f"telemetry_{today_str}.json"
    assert telemetry_file.exists(), f"Relatorio {telemetry_file} nao foi criado em disco."

    with open(telemetry_file, encoding="utf-8") as f:
        data = json.load(f)

    assert len(data["runs"]) == 1
    run = data["runs"][0]
    assert run["platform"] == "linkedin"
    assert run["search_urls"] == 1
    assert run["max_applications"] == 2

    funnel = run["funnel"]
    assert funnel["total_read"] == 5
    assert funnel["applied"] == 2
    assert funnel["not_processed"] == 3
    assert funnel["total_read"] == (
        funnel["applied"]
        + funnel["skipped_complex"]
        + funnel["errors"]
        + funnel["already_applied"]
        + funnel["not_processed"]
    )

