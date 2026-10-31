import pytest
from datetime import datetime


def test_job_entity_creation_valid():
    """Valida criacao valida da entidade Job com todos os campos obrigatorios."""
    from src.domain.entities.job import Job

    job = Job(
        url="https://www.linkedin.com/jobs/view/123456/",
        platform="linkedin",
        title="Software Engineer",
        company="Tech Corp",
        status="PENDING",
        timestamp=datetime(2026, 10, 31, 10, 0, 0),
    )

    assert job.url == "https://www.linkedin.com/jobs/view/123456/"
    assert job.platform == "linkedin"
    assert job.title == "Software Engineer"
    assert job.company == "Tech Corp"
    assert job.status == "PENDING"
    assert job.timestamp == datetime(2026, 10, 31, 10, 0, 0)


def test_job_valid_statuses():
    """Valida que todos os status previstos no contrato sao suportados."""
    from src.domain.entities.job import Job

    valid_statuses = ["PENDING", "APPLIED", "SKIPPED_COMPLEX", "ALREADY_APPLIED", "ERROR"]
    for st in valid_statuses:
        job = Job(
            url="https://example.com/job/1",
            platform="generic",
            title="Dev",
            company="Co",
            status=st,
            timestamp=datetime.now(),
        )
        assert job.status == st


def test_job_invalid_status_raises_error():
    """Valida que status fora da lista do contrato lanca erro de validacao (ValueError)."""
    from src.domain.entities.job import Job

    with pytest.raises(ValueError):
        Job(
            url="https://example.com/job/1",
            platform="generic",
            title="Dev",
            company="Co",
            status="STATUS_INVALIDO_XYZ",
            timestamp=datetime.now(),
        )


def test_job_empty_url_or_platform_raises_error():
    """Valida que url ou platform vazios lancam erro de validacao."""
    from src.domain.entities.job import Job

    with pytest.raises(ValueError):
        Job(url="", platform="linkedin", title="Dev", company="Co", status="PENDING", timestamp=datetime.now())

    with pytest.raises(ValueError):
        Job(url="https://example.com", platform="", title="Dev", company="Co", status="PENDING", timestamp=datetime.now())


def test_job_identity_by_url_and_platform():
    """Valida a Decisao 2: dois Jobs com mesma url e platform sao considerados equivalentes (hash e equality)."""
    from src.domain.entities.job import Job

    job1 = Job(
        url="https://example.com/jobs/100",
        platform="linkedin",
        title="Engenheiro Python",
        company="Startup A",
        status="PENDING",
        timestamp=datetime(2026, 1, 1),
    )

    job2 = Job(
        url="https://example.com/jobs/100",
        platform="linkedin",
        title="Python Dev Senior (Titulo Diferente)",
        company="Empresa Renomeada",
        status="APPLIED",
        timestamp=datetime(2026, 2, 1),
    )

    assert job1 == job2
