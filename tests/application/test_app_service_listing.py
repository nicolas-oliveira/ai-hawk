import pytest
from src.application.dtos.search_request import SearchRequest


def test_extract_jobs_navigates_scrolls_and_extracts_canonical_jobs(mock_browser_service, valid_search_request_payload):
    """
    Step B: Valida que a extracao/coleta de vagas navega para a URL estatica,
    executa o scroll do container para lazy loading, extrai os dados e retorna
    entidades Job unicas com URLs canonizadas e status PENDING.
    """
    from src.application.app_service import AppService
    from src.domain.entities.job import Job

    # Prepara retorno de cards no mock (com URLs sujas de tracking e uma duplicata)
    mock_browser_service.extract_job_cards.return_value = [
        {"url": "https://www.linkedin.com/jobs/view/100000001/?refId=tracking_abc", "title": "Python Dev", "company": "Tech Corp"},
        {"url": "https://www.linkedin.com/jobs/view/100000002/?trackingId=xyz_123", "title": "Backend Dev", "company": "Global Inc"},
        {"url": "https://www.linkedin.com/jobs/view/100000001/?refId=outro_param_mesma_vaga", "title": "Python Dev", "company": "Tech Corp"},
    ]
    mock_browser_service.extract_links.return_value = [
        "https://www.linkedin.com/jobs/view/100000001/?refId=tracking_abc",
        "https://www.linkedin.com/jobs/view/100000002/?trackingId=xyz_123",
        "https://www.linkedin.com/jobs/view/100000001/?refId=outro_param_mesma_vaga",
    ]

    request = SearchRequest(**valid_search_request_payload)
    app_service = AppService(mock_browser_service)

    # Identifica o metodo de coleta de vagas (extract_jobs ou _collect_jobs)
    collect_fn = getattr(app_service, "extract_jobs", getattr(app_service, "_collect_jobs", None))
    assert callable(collect_fn), "AppService deve possuir metodo extract_jobs ou _collect_jobs"

    jobs = collect_fn(request)

    # 1. Deve navegar para a URL de busca
    assert (
        mock_browser_service.navigate.called
        or mock_browser_service.open_url.called
    ), "Browser deve ter sido acionado para abrir a URL estatica"

    # 2. Deve acionar o scroll do container de lazy loading
    assert (
        mock_browser_service.scroll_container.called
        or mock_browser_service.scroll_container_to_end.called
    ), "Browser deve ter rolado o container jobs_list_container"

    # 3. Deve retornar apenas 2 Jobs (deduplicados pela identidade ou URL canonica)
    assert len(jobs) == 2
    assert all(isinstance(j, Job) for j in jobs)
    assert all(j.status == "PENDING" for j in jobs)
    assert all(j.platform == "linkedin" for j in jobs)


def test_extract_jobs_handles_empty_listing_gracefully(mock_browser_service, valid_search_request_payload):
    """Step B: Valida retorno de lista vazia sem quebrar quando a busca nao tem vagas."""
    from src.application.app_service import AppService

    mock_browser_service.extract_job_cards.return_value = []
    mock_browser_service.extract_links.return_value = []

    request = SearchRequest(**valid_search_request_payload)
    app_service = AppService(mock_browser_service)
    collect_fn = getattr(app_service, "extract_jobs", getattr(app_service, "_collect_jobs", None))

    jobs = collect_fn(request)
    assert jobs == []


def test_extract_jobs_iterates_multiple_static_urls(mock_browser_service, valid_search_request_payload):
    """Step B: Valida navegacao e agregacao quando multiplas static_urls sao fornecidas."""
    from src.application.app_service import AppService

    payload = dict(valid_search_request_payload)
    payload["static_urls"] = [
        "https://www.linkedin.com/jobs/search/?keywords=python",
        "https://www.linkedin.com/jobs/search/?keywords=backend",
    ]
    request = SearchRequest(**payload)

    # Primeira busca retorna vaga 1; segunda busca retorna vaga 1 e vaga 2
    mock_browser_service.extract_job_cards.side_effect = [
        [{"url": "https://www.linkedin.com/jobs/view/101/?refId=1", "title": "Dev 1", "company": "Co 1"}],
        [
            {"url": "https://www.linkedin.com/jobs/view/101/?refId=2", "title": "Dev 1", "company": "Co 1"},
            {"url": "https://www.linkedin.com/jobs/view/102/", "title": "Dev 2", "company": "Co 2"},
        ],
    ]

    app_service = AppService(mock_browser_service)
    collect_fn = getattr(app_service, "extract_jobs", getattr(app_service, "_collect_jobs", None))
    jobs = collect_fn(request)

    call_count = mock_browser_service.navigate.call_count + mock_browser_service.open_url.call_count
    assert call_count >= 2
    assert len(jobs) == 2
