import pytest
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import Job, JobStatus


def _get_apply_function(app_service):
    """Auxiliar resiliente para invocar a candidatura individual em AppService."""
    if hasattr(app_service, "apply_to_job"):
        return app_service.apply_to_job
    if hasattr(app_service, "_process_job"):
        def wrapper(job, request):
            app_service._process_job(job, request)
            return job
        return wrapper
    raise AttributeError("AppService deve fornecer apply_to_job(job, request) ou _process_job(job, request)")


def _get_controller_run(app_controller):
    """Auxiliar resiliente para invocar a execucao em AppController."""
    if hasattr(app_controller, "run"):
        return app_controller.run
    if hasattr(app_controller, "execute"):
        return app_controller.execute
    raise AttributeError("AppController deve fornecer run(request) ou execute(request)")


def test_apply_to_job_single_step_direct_submission(mock_browser_service, valid_search_request_payload, valid_job_payload):
    """
    Step C: Vaga direta (1 etapa sem campos vazios).
    Deve clicar em apply_button, validar has_empty_required_inputs == False,
    clicar em submit_button e marcar status como APPLIED.
    """
    from src.application.app_service import AppService

    request = SearchRequest(**valid_search_request_payload)
    job = Job(**valid_job_payload)
    app_service = AppService(mock_browser_service)
    apply_fn = _get_apply_function(app_service)

    # Configuracao do DOM mockado
    mock_browser_service.is_visible.side_effect = lambda sel, **kw: True
    mock_browser_service.element_exists.side_effect = lambda sel, **kw: True
    mock_browser_service.has_empty_required_inputs.return_value = False

    result_job = apply_fn(job, request)

    # 1. Navegou para a URL da vaga
    assert mock_browser_service.navigate.called or mock_browser_service.open_url.called

    # 2. Clicou no apply_button
    apply_clicked = any(
        c[0][0] == request.selectors["apply_button"]
        for c in (mock_browser_service.click_element.call_args_list + mock_browser_service.click.call_args_list)
    )
    assert apply_clicked, "Deve ter clicado em apply_button"

    # 3. Validou ausencia de campos obrigatorios vazios (Heuristica 3C)
    mock_browser_service.has_empty_required_inputs.assert_called_with(request.selectors["modal_container"])

    # 4. Clicou no submit_button
    submit_clicked = any(
        c[0][0] == request.selectors["submit_button"]
        for c in (mock_browser_service.click_element.call_args_list + mock_browser_service.click.call_args_list)
    )
    assert submit_clicked, "Deve ter clicado em submit_button"

    # 5. Status final APPLIED
    assert result_job.status == JobStatus.APPLIED


def test_apply_to_job_detects_empty_required_and_aborts_cleanly(mock_browser_service, valid_search_request_payload, valid_job_payload):
    """
    Step C (Heuristica 3C): Modal com campos obrigatorios vazios visiveis.
    Deve abortar imediatamente: clicar em close_button -> discard_button
    e marcar status como SKIPPED_COMPLEX sem clicar em submit ou next.
    """
    from src.application.app_service import AppService

    request = SearchRequest(**valid_search_request_payload)
    job = Job(**valid_job_payload)
    app_service = AppService(mock_browser_service)
    apply_fn = _get_apply_function(app_service)

    # has_empty_required_inputs acusa complexidade (campos vazios)
    mock_browser_service.is_visible.side_effect = lambda sel, **kw: True
    mock_browser_service.element_exists.side_effect = lambda sel, **kw: True
    mock_browser_service.has_empty_required_inputs.return_value = True

    result_job = apply_fn(job, request)

    all_clicks = [c[0][0] for c in (mock_browser_service.click_element.call_args_list + mock_browser_service.click.call_args_list)]

    # Deve acionar o fluxo de fechamento seguro (close_button)
    assert request.selectors["close_button"] in all_clicks

    # NUNCA deve submeter ou avancar
    assert request.selectors["submit_button"] not in all_clicks
    assert request.selectors["next_button"] not in all_clicks

    assert result_job.status == JobStatus.SKIPPED_COMPLEX


def test_apply_to_job_multi_step_simple_submission(mock_browser_service, valid_search_request_payload, valid_job_payload):
    """
    Step C: Modal com 2 passos sem campos vazios.
    Passo 1: clica next_button. Passo 2: clica submit_button -> APPLIED.
    """
    from src.application.app_service import AppService

    request = SearchRequest(**valid_search_request_payload)
    job = Job(**valid_job_payload)
    app_service = AppService(mock_browser_service)
    apply_fn = _get_apply_function(app_service)

    # has_empty_required_inputs sempre False
    mock_browser_service.has_empty_required_inputs.return_value = False

    submit_sel = request.selectors["submit_button"]
    next_sel = request.selectors["next_button"]

    step_state = {"step": 1}

    def custom_exists(selector, **kwargs):
        if selector == submit_sel:
            return step_state["step"] >= 2
        if selector == next_sel:
            return step_state["step"] == 1
        return True

    def custom_click(selector, **kwargs):
        if selector == next_sel:
            step_state["step"] = 2
        return True

    mock_browser_service.is_visible.side_effect = custom_exists
    mock_browser_service.element_exists.side_effect = custom_exists
    mock_browser_service.click_element.side_effect = custom_click
    mock_browser_service.click.side_effect = custom_click

    result_job = apply_fn(job, request)

    assert result_job.status == JobStatus.APPLIED
    assert mock_browser_service.has_empty_required_inputs.call_count >= 2


def test_apply_to_job_external_redirect_skipped_complex(mock_browser_service, valid_search_request_payload, valid_job_payload):
    """Step C: Vaga sem botao de Easy Apply (redirecionamento externo) -> SKIPPED_COMPLEX."""
    from src.application.app_service import AppService

    request = SearchRequest(**valid_search_request_payload)
    job = Job(**valid_job_payload)
    app_service = AppService(mock_browser_service)
    apply_fn = _get_apply_function(app_service)

    # apply_button nao esta visivel/existente
    apply_sel = request.selectors["apply_button"]
    mock_browser_service.is_visible.side_effect = lambda sel, **kw: False if sel == apply_sel else True
    mock_browser_service.element_exists.side_effect = lambda sel, **kw: False if sel == apply_sel else True

    result_job = apply_fn(job, request)

    assert result_job.status == JobStatus.SKIPPED_COMPLEX


def test_apply_to_job_exceeding_max_steps_aborts_cleanly(mock_browser_service, valid_search_request_payload, valid_job_payload):
    """
    Step C: Modal multi-etapas que excede o limite de passos sem submissao -> Aborta via close/discard
    e marca SKIPPED_COMPLEX ou ERROR de forma segura para evitar loops infinitos.
    """
    from src.application.app_service import AppService

    request = SearchRequest(**valid_search_request_payload)
    job = Job(**valid_job_payload)
    app_service = AppService(mock_browser_service)
    apply_fn = _get_apply_function(app_service)

    mock_browser_service.has_empty_required_inputs.return_value = False
    # submit_button nunca fica visivel, next_button sempre visivel
    mock_browser_service.is_visible.side_effect = lambda sel, **kw: False if sel == request.selectors["submit_button"] else True
    mock_browser_service.element_exists.side_effect = lambda sel, **kw: False if sel == request.selectors["submit_button"] else True

    result_job = apply_fn(job, request)

    all_clicks = [c[0][0] for c in (mock_browser_service.click_element.call_args_list + mock_browser_service.click.call_args_list)]

    # Deve ter clicado no close_button
    assert request.selectors["close_button"] in all_clicks
    assert result_job.status in (JobStatus.SKIPPED_COMPLEX, JobStatus.ERROR)


def test_run_orchestration_respects_max_applications_ceiling(mock_browser_service, valid_search_request_payload):
    """
    Step C: Valida que AppService.run interrompe o loop assim que o numero
    de vagas com status APPLIED atinge search_request.max_applications.
    """
    from src.application.app_service import AppService
    from src.domain.entities.job import Job

    payload = dict(valid_search_request_payload)
    payload["max_applications"] = 2
    request = SearchRequest(**payload)

    # 5 vagas extraidas
    mock_jobs = [
        Job(url=f"https://www.linkedin.com/jobs/view/10{i}/", platform="linkedin", title=f"Job {i}", company="Co")
        for i in range(1, 6)
    ]

    app_service = AppService(mock_browser_service)
    # Mock da coleta de vagas
    if hasattr(app_service, "extract_jobs"):
        app_service.extract_jobs = lambda req: mock_jobs
    elif hasattr(app_service, "_collect_jobs"):
        app_service._collect_jobs = lambda req: mock_jobs

    # Vaga 1: APPLIED, Vaga 2: SKIPPED_COMPLEX, Vaga 3: APPLIED -> total APPLIED = 2 atingido!
    def mock_apply(job, req):
        if job.url.endswith("101/"):
            job.status = JobStatus.APPLIED
        elif job.url.endswith("102/"):
            job.status = JobStatus.SKIPPED_COMPLEX
        elif job.url.endswith("103/"):
            job.status = JobStatus.APPLIED
        else:
            job.status = JobStatus.APPLIED
        return job

    if hasattr(app_service, "apply_to_job"):
        app_service.apply_to_job = mock_apply
    elif hasattr(app_service, "_process_job"):
        app_service._process_job = lambda job, req: mock_apply(job, req)

    result = app_service.run(request)

    applied_jobs = [j for j in getattr(result, "jobs", result) if j.status == JobStatus.APPLIED]
    assert len(applied_jobs) == 2

    # As vagas 4 e 5 NAO devem ter sido processadas (permanecem PENDING)
    assert mock_jobs[3].status == JobStatus.PENDING
    assert mock_jobs[4].status == JobStatus.PENDING


def test_app_controller_run_delegates_to_service_and_returns_summary(mock_browser_service, valid_search_request_payload):
    """Valida integracao do AppController chamando AppService.run e retornando objeto/sumario."""
    from src.application.app_service import AppService
    from src.application.app_controller import AppController
    from src.domain.entities.job import Job

    request = SearchRequest(**valid_search_request_payload)
    app_service = AppService(mock_browser_service)
    app_controller = AppController(app_service, reports_dir=None)

    job1 = Job(url="https://www.linkedin.com/jobs/view/201/", platform="linkedin", title="Dev 1", company="Co", status=JobStatus.APPLIED)
    job2 = Job(url="https://www.linkedin.com/jobs/view/202/", platform="linkedin", title="Dev 2", company="Co", status=JobStatus.SKIPPED_COMPLEX)

    app_service.run = lambda req: [job1, job2]

    run_fn = _get_controller_run(app_controller)
    result = run_fn(request)
    assert result is not None
