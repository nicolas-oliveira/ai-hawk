import json
import os
from unittest.mock import MagicMock
import pytest

from src.application.app_service import AppService, JsonJobCache, CACHEABLE_STATUSES
from src.application.app_controller import AppController
from src.application.dtos.search_request import SearchRequest, LINKEDIN_DEFAULT_SELECTORS
from src.domain.entities.job import Job, JobStatus


def test_json_job_cache_put_get_roundtrip(tmp_path):
    """Valida armazenamento e recuperacao no JsonJobCache."""
    cache_file = tmp_path / "jobs_cache.json"
    cache = JsonJobCache(str(cache_file))

    job1 = Job(url="https://www.linkedin.com/jobs/view/100/", platform="linkedin", title="Dev", company="Co", status=JobStatus.APPLIED)
    cache.put(job1)

    assert cache.get(job1) == JobStatus.APPLIED

    # Status nao cacheaveis (ERROR, PENDING) sao ignorados pelo put
    job_err = Job(url="https://www.linkedin.com/jobs/view/101/", platform="linkedin", title="Dev", company="Co", status=JobStatus.ERROR)
    cache.put(job_err)
    assert cache.get(job_err) is None

    job_pending = Job(url="https://www.linkedin.com/jobs/view/102/", platform="linkedin", title="Dev", company="Co", status=JobStatus.PENDING)
    cache.put(job_pending)
    assert cache.get(job_pending) is None


def test_json_job_cache_corrupted_file_handling(tmp_path):
    """Valida que arquivo corrompido e renomeado para .corrupt-HHMMSS e cache reinicia limpo."""
    cache_file = tmp_path / "jobs_cache.json"
    cache_file.write_text("{conteudo_corrompido", encoding="utf-8")

    cache = JsonJobCache(str(cache_file))
    job = Job(url="https://www.linkedin.com/jobs/view/200/", platform="linkedin", title="Dev", company="Co", status=JobStatus.APPLIED)
    cache.put(job)

    assert cache.get(job) == JobStatus.APPLIED
    corrupt_backups = list(tmp_path.glob("jobs_cache.json.corrupt-*"))
    assert len(corrupt_backups) == 1
    assert corrupt_backups[0].read_text(encoding="utf-8") == "{conteudo_corrompido"


def test_app_service_cache_hit_does_not_consume_max_applications(tmp_path, mock_browser_service):
    """Valida que vaga em cache vira ALREADY_APPLIED e nao consome a cota de max_applications."""
    cache_file = tmp_path / "cache.json"
    cache = JsonJobCache(str(cache_file))

    job1 = Job(url="https://www.linkedin.com/jobs/view/301/", platform="linkedin", title="Dev 1", company="Co", status=JobStatus.APPLIED)
    job2 = Job(url="https://www.linkedin.com/jobs/view/302/", platform="linkedin", title="Dev 2", company="Co", status=JobStatus.APPLIED)
    cache.put(job1)

    request = SearchRequest(
        platform="linkedin",
        static_urls=["https://www.linkedin.com/jobs/search"],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_applications=1,  # Cota de 1
    )

    app_service = AppService(mock_browser_service, cache=cache)
    app_service._collect_jobs = lambda req: [
        Job(url="https://www.linkedin.com/jobs/view/301/", platform="linkedin", title="Dev 1", company="Co"),
        Job(url="https://www.linkedin.com/jobs/view/302/", platform="linkedin", title="Dev 2", company="Co"),
    ]
    # Simula aplicacao bem-sucedida na vaga 302
    def fake_process_job(job, req):
        job.status = JobStatus.APPLIED

    app_service._process_job = fake_process_job

    processed = app_service.run(request)
    assert len(processed) == 2
    assert processed[0].status == JobStatus.ALREADY_APPLIED
    assert processed[0].from_cache is True
    assert processed[1].status == JobStatus.APPLIED
    assert processed[1].from_cache is False
    assert sum(1 for j in processed if j.from_cache) == 1


def test_app_service_circuit_breaker_consecutive_errors(mock_browser_service):
    """Valida que 3 erros consecutivos disparam o freio e interrompem a sessao."""
    request = SearchRequest(
        platform="linkedin",
        static_urls=["https://www.linkedin.com/jobs/search"],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_consecutive_errors=3,
        max_applications=10,
    )

    app_service = AppService(mock_browser_service)
    jobs = [
        Job(url=f"https://www.linkedin.com/jobs/view/{i}/", platform="linkedin", title=f"Dev {i}", company="Co")
        for i in range(1, 6)
    ]
    app_service._collect_jobs = lambda req: jobs

    # Simula falha em todos os jobs
    def fail_all(job, req):
        job.status = JobStatus.ERROR

    app_service._process_job = fail_all

    processed = app_service.run(request)

    # Apos 3 falhas, a sessao e abortada
    assert app_service.last_abort_reason == "3 erros consecutivos (limite 3)"
    assert processed[0].status == JobStatus.ERROR
    assert processed[1].status == JobStatus.ERROR
    assert processed[2].status == JobStatus.ERROR
    # As vagas 4 e 5 permanecem PENDING pois nao foram processadas
    assert processed[3].status == JobStatus.PENDING
    assert processed[4].status == JobStatus.PENDING


def test_app_service_circuit_breaker_resets_on_success(mock_browser_service):
    """Valida que uma candidatura com sucesso zera o contador de erros consecutivos."""
    request = SearchRequest(
        platform="linkedin",
        static_urls=["https://www.linkedin.com/jobs/search"],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_consecutive_errors=3,
        max_applications=10,
    )

    app_service = AppService(mock_browser_service)
    jobs = [
        Job(url=f"https://www.linkedin.com/jobs/view/{i}/", platform="linkedin", title=f"Dev {i}", company="Co")
        for i in range(1, 6)
    ]
    app_service._collect_jobs = lambda req: jobs

    # Erro no 1, Erro no 2, Sucesso no 3, Erro no 4 -> nunca atinge 3 consecutivos
    statuses = [JobStatus.ERROR, JobStatus.ERROR, JobStatus.APPLIED, JobStatus.ERROR, JobStatus.APPLIED]

    def sequential_process(job, req):
        idx = int(job.url.split("/")[-2]) - 1
        job.status = statuses[idx]

    app_service._process_job = sequential_process

    processed = app_service.run(request)
    assert app_service.last_abort_reason is None
    assert processed[0].status == JobStatus.ERROR
    assert processed[1].status == JobStatus.ERROR
    assert processed[2].status == JobStatus.APPLIED
    assert processed[3].status == JobStatus.ERROR
    assert processed[4].status == JobStatus.APPLIED
