import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from src.application.app_controller import AppController
from src.application.dtos.search_request import SearchRequest, LINKEDIN_DEFAULT_SELECTORS
from src.domain.entities.job import Job, JobStatus


@pytest.fixture
def dummy_request():
    return SearchRequest(
        platform="linkedin",
        static_urls=["https://www.linkedin.com/jobs/search/?keywords=python"],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_applications=5,
    )


def test_app_controller_validate_type_error():
    """Valida que execute lanca TypeError se request nao for SearchRequest."""
    mock_service = MagicMock()
    controller = AppController(mock_service, reports_dir=None)

    with pytest.raises(TypeError, match="SearchRequest"):
        controller.execute({"platform": "linkedin"})


def test_app_controller_format_summary(dummy_request):
    """Valida formatacao visual do sumario do console."""
    mock_service = MagicMock()
    controller = AppController(mock_service, reports_dir=None)

    jobs = [
        Job(url="https://www.linkedin.com/jobs/view/101/", platform="linkedin", title="Dev", company="Co", status=JobStatus.APPLIED),
        Job(url="https://www.linkedin.com/jobs/view/102/", platform="linkedin", title="Dev", company="Co", status=JobStatus.SKIPPED_COMPLEX),
        Job(url="https://www.linkedin.com/jobs/view/103/", platform="linkedin", title="Dev", company="Co", status=JobStatus.ERROR),
        Job(url="https://www.linkedin.com/jobs/view/104/", platform="linkedin", title="Dev", company="Co", status=JobStatus.PENDING),
    ]

    summary = controller.format_summary(jobs, dummy_request)

    assert "AIHawk - Resumo da sessao (linkedin)" in summary
    assert "URLs de busca:        1" in summary
    assert "Vagas encontradas:    4" in summary
    assert "Candidaturas:         1 de 5 (limite)" in summary
    assert "SKIPPED_COMPLEX       1" in summary
    assert "ERROR                 1" in summary
    assert "PENDING               1" in summary


def test_app_controller_build_telemetry_funnel(dummy_request):
    """Valida estrutura do funil e taxas de conversao na telemetria."""
    jobs = [
        Job(url="https://www.linkedin.com/jobs/view/101/", platform="linkedin", title="Dev", company="Co", status=JobStatus.APPLIED),
        Job(url="https://www.linkedin.com/jobs/view/102/", platform="linkedin", title="Dev", company="Co", status=JobStatus.SKIPPED_COMPLEX),
        Job(url="https://www.linkedin.com/jobs/view/103/", platform="linkedin", title="Dev", company="Co", status=JobStatus.ERROR),
        Job(url="https://www.linkedin.com/jobs/view/104/", platform="linkedin", title="Dev", company="Co", status=JobStatus.ALREADY_APPLIED),
        Job(url="https://www.linkedin.com/jobs/view/105/", platform="linkedin", title="Dev", company="Co", status=JobStatus.PENDING),
    ]
    started = datetime(2026, 10, 31, 10, 0, 0, tzinfo=timezone.utc)
    finished = datetime(2026, 10, 31, 10, 0, 15, tzinfo=timezone.utc)

    telemetry = AppController.build_telemetry(jobs, dummy_request, started, finished)

    assert telemetry["platform"] == "linkedin"
    assert telemetry["duration_seconds"] == 15.0
    assert telemetry["search_urls"] == 1
    assert telemetry["max_applications"] == 5

    funnel = telemetry["funnel"]
    assert funnel["total_read"] == 5
    assert funnel["applied"] == 1
    assert funnel["skipped_complex"] == 1
    assert funnel["errors"] == 1
    assert funnel["already_applied"] == 1
    assert funnel["not_processed"] == 1

    # Invariante do Funil: total_read deve ser a soma de todos os estados
    assert funnel["total_read"] == (
        funnel["applied"]
        + funnel["skipped_complex"]
        + funnel["errors"]
        + funnel["already_applied"]
        + funnel["not_processed"]
    )

    conversion = telemetry["conversion"]
    assert conversion["applied_over_total"] == 0.2
    assert conversion["skipped_complex_over_total"] == 0.2
    assert conversion["errors_over_total"] == 0.2
    assert len(telemetry["jobs"]) == 5


def test_app_controller_export_telemetry_creates_file_and_appends(tmp_path, dummy_request):
    """Valida persistencia em disco e acumulo de multiplas execucoes no mesmo dia."""
    mock_service = MagicMock()
    mock_service.run.return_value = [
        Job(url="https://www.linkedin.com/jobs/view/101/", platform="linkedin", title="Dev", company="Co", status=JobStatus.APPLIED)
    ]

    fixed_time = datetime(2026, 10, 31, 14, 30, 0, tzinfo=timezone.utc)
    controller = AppController(
        mock_service,
        reports_dir=str(tmp_path),
        clock=lambda: fixed_time,
    )

    summary1 = controller.execute(dummy_request)
    expected_file = tmp_path / "telemetry_20261031.json"
    assert expected_file.exists()
    assert str(expected_file) in summary1

    with open(expected_file, encoding="utf-8") as f:
        data1 = json.load(f)
    assert data1["date"] == "2026-10-31"
    assert len(data1["runs"]) == 1

    # Segunda execucao no mesmo dia: deve ACRESCENTAR no array 'runs' sem apagar a anterior
    controller.execute(dummy_request)
    with open(expected_file, encoding="utf-8") as f:
        data2 = json.load(f)
    assert len(data2["runs"]) == 2


def test_app_controller_export_telemetry_handles_corrupted_file(tmp_path, dummy_request):
    """Valida que arquivo corrompido e preservado como .corrupt-HHMMSS e novo json e criado."""
    report_file = tmp_path / "telemetry_20261031.json"
    report_file.write_text("{conteudo_invalido_de_teste", encoding="utf-8")

    mock_service = MagicMock()
    mock_service.run.return_value = []
    fixed_time = datetime(2026, 10, 31, 15, 45, 12, tzinfo=timezone.utc)

    controller = AppController(
        mock_service,
        reports_dir=str(tmp_path),
        clock=lambda: fixed_time,
    )
    controller.execute(dummy_request)

    # Novo arquivo valido gerado
    with open(report_file, encoding="utf-8") as f:
        new_data = json.load(f)
    assert new_data["date"] == "2026-10-31"
    assert len(new_data["runs"]) == 1

    # Arquivo corrompido foi preservado
    corrupt_files = list(tmp_path.glob("telemetry_20261031.json.corrupt-*"))
    assert len(corrupt_files) == 1
    assert corrupt_files[0].read_text(encoding="utf-8") == "{conteudo_invalido_de_teste"


def test_app_controller_reports_dir_none_disables_export(dummy_request):
    """Valida que reports_dir=None nao exporta nenhum arquivo e nao adiciona linha de telemetria."""
    mock_service = MagicMock()
    mock_service.run.return_value = []

    controller = AppController(mock_service, reports_dir=None)
    summary = controller.execute(dummy_request)

    assert "Telemetria:" not in summary


def test_app_controller_export_io_error_does_not_crash(monkeypatch, tmp_path, dummy_request):
    """Valida resiliencia: falha de I/O emite log de erro mas nao derruba a aplicacao."""
    mock_service = MagicMock()
    mock_service.run.return_value = []

    def mock_replace(src, dst):
        raise OSError("Disco bloqueado ou sem permissao")

    monkeypatch.setattr(os, "replace", mock_replace)

    controller = AppController(mock_service, reports_dir=str(tmp_path))
    summary = controller.execute(dummy_request)

    # Nao lancou excecao, executou normalmente
    assert "AIHawk - Resumo da sessao (linkedin)" in summary
