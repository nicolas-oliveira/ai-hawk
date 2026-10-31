import pytest
from datetime import datetime


def test_job_creation_valid(valid_job_payload):
    """Valida criacao correta da entidade pura Job utilizando fixture padrao."""
    from src.domain.entities.job import Job

    job = Job(**valid_job_payload)

    assert job.url == valid_job_payload["url"]
    assert job.platform == valid_job_payload["platform"]
    assert job.title == valid_job_payload["title"]
    assert job.company == valid_job_payload["company"]
    assert job.status == "PENDING"
    assert job.timestamp == valid_job_payload["timestamp"]


def test_job_default_values():
    """Valida defaults: status PENDING e timestamp datetime automatico."""
    from src.domain.entities.job import Job

    job = Job(
        url="https://example.com/job/default-test",
        platform="linkedin",
        title="Developer",
        company="Tech Corp",
    )
    assert job.status == "PENDING"
    assert isinstance(job.timestamp, datetime)


def test_job_valid_status_transitions():
    """Valida que todos os status previstos no contrato sao aceitos."""
    from src.domain.entities.job import Job

    allowed_statuses = ["PENDING", "APPLIED", "SKIPPED_COMPLEX", "ALREADY_APPLIED", "ERROR"]
    for st in allowed_statuses:
        job = Job(
            url="https://example.com/job/test",
            platform="generic",
            title="Backend Dev",
            company="Company XYZ",
            status=st,
            timestamp=datetime.now(),
        )
        assert job.status == st


def test_job_invalid_status_raises_error():
    """Valida que status fora da maquina de estados lanca ValueError na criacao."""
    from src.domain.entities.job import Job

    with pytest.raises(ValueError):
        Job(
            url="https://example.com/job/test",
            platform="generic",
            title="Backend Dev",
            company="Company XYZ",
            status="INVALID_STATUS_CODE",
            timestamp=datetime.now(),
        )


def test_job_status_late_assignment_validation():
    """Valida que reatribuicao posterior de status tambem valida contra a maquina de estados."""
    from src.domain.entities.job import Job

    job = Job(
        url="https://example.com/job/test",
        platform="linkedin",
        title="Dev",
        company="Co",
    )
    job.status = "APPLIED"
    assert job.status == "APPLIED"

    with pytest.raises(ValueError):
        job.status = "STATUS_PROIBIDO"


def test_job_empty_required_fields_raises_error():
    """Valida que url ou platform vazios nao sao permitidos."""
    from src.domain.entities.job import Job

    with pytest.raises(ValueError):
        Job(url="", platform="linkedin", title="Dev", company="Co", status="PENDING", timestamp=datetime.now())

    with pytest.raises(ValueError):
        Job(url="https://example.com", platform="", title="Dev", company="Co", status="PENDING", timestamp=datetime.now())


def test_job_canonicalize_url_removes_tracking_and_query_params():
    """
    Step A: Higienizacao de URLs de vagas.
    Valida que Job.canonicalize_url remove query strings (?refId=...&trackingId=...),
    fragmentos (#...) e normaliza com barra trailing.
    """
    from src.domain.entities.job import Job

    assert hasattr(Job, "canonicalize_url"), "Job deve implementar o metodo estatico/classmethod canonicalize_url"

    raw_url1 = "https://www.linkedin.com/jobs/view/123456789/?refId=abc1234&trackingId=xyz5678&position=1&pageNum=0"
    canonical1 = Job.canonicalize_url(raw_url1)
    assert canonical1 == "https://www.linkedin.com/jobs/view/123456789/"

    raw_url2 = "https://www.linkedin.com/jobs/view/987654321?utm_source=share#detail"
    canonical2 = Job.canonicalize_url(raw_url2)
    assert canonical2 == "https://www.linkedin.com/jobs/view/987654321/"

    # Preserva caminhos limpos
    raw_url3 = "https://www.linkedin.com/jobs/view/1122334455/"
    assert Job.canonicalize_url(raw_url3) == "https://www.linkedin.com/jobs/view/1122334455/"


def test_job_equality_and_identity_by_url_and_platform():
    """Valida a Decisao 2: dois Jobs com mesma url e platform sao semanticamente equivalentes."""
    from src.domain.entities.job import Job

    job_a = Job(
        url="https://example.com/jobs/999",
        platform="linkedin",
        title="Python Dev",
        company="Startup A",
        status="PENDING",
        timestamp=datetime(2026, 1, 1),
    )

    job_b = Job(
        url="https://example.com/jobs/999",
        platform="linkedin",
        title="Engenheiro Python Senior (Renomeado)",
        company="Startup A (Adquirida)",
        status="APPLIED",
        timestamp=datetime(2026, 10, 1),
    )

    assert job_a == job_b
    assert hash(job_a) == hash(job_b)
