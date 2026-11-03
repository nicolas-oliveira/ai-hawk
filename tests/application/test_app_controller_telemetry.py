import json
import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.application import app_controller
from src.application.app_controller import AppController
from src.application.dtos.search_request import LINKEDIN_DEFAULT_SELECTORS, SearchRequest
from src.domain.entities.job import Job, JobStatus

START = datetime(2026, 11, 2, 10, 30, 5, 123456, tzinfo=timezone.utc)
END = datetime(2026, 11, 2, 10, 30, 6, 358456, tzinfo=timezone.utc)  # +1,235 s


@pytest.fixture
def request_():
    return SearchRequest(
        platform="linkedin",
        static_urls=["https://x.com/a", "https://x.com/b"],
        selectors=LINKEDIN_DEFAULT_SELECTORS,
        max_applications=5,
    )


def _job(n, status, **kw):
    return Job(url=f"https://x.com/jobs/{n}/", platform="linkedin", title=f"T{n}",
               company=f"C{n}", status=status, **kw)


def _clock():
    it = iter([START, END])
    return lambda: next(it)


def test_pasta_padrao_de_relatorios():
    assert app_controller.DEFAULT_REPORTS_DIR == "reports"
    assert AppController(MagicMock())._reports_dir == "reports"


def test_sumario_exato():
    req = SearchRequest(platform="p", static_urls=["u1", "u2"],
                        selectors=LINKEDIN_DEFAULT_SELECTORS, max_applications=3)
    jobs = [_job(1, JobStatus.APPLIED), _job(2, JobStatus.ERROR)]
    esperado = "\n".join([
        "=" * 50,
        "AIHawk - Resumo da sessao (p)",
        "=" * 50,
        "URLs de busca:        2",
        "Vagas encontradas:    2",
        "Candidaturas:         1 de 3 (limite)",
        "PENDING               0",
        "SKIPPED_COMPLEX       0",
        "ALREADY_APPLIED       0",
        "ERROR                 1",
        "SIMULATED             0",
        "SUBMITTING            0",
        "MANUAL_REVIEW         0",
    ])
    assert AppController.format_summary(jobs, req) == esperado


def test_telemetria_campos_e_taxas(request_):
    jobs = [
        _job(1, JobStatus.APPLIED, from_cache=True),
        _job(2, JobStatus.SKIPPED_COMPLEX, from_cache=True),
        _job(3, JobStatus.ERROR),
    ]
    rep = AppController.build_telemetry(jobs, request_, START, END, aborted_reason="freio")

    assert rep["started_at"] == "2026-11-02T10:30:05+00:00"  # sem microssegundos
    assert rep["finished_at"] == "2026-11-02T10:30:06+00:00"
    assert rep["duration_seconds"] == 1.235
    assert rep["platform"] == "linkedin"
    assert rep["search_urls"] == 2
    assert rep["max_applications"] == 5
    assert rep["aborted_reason"] == "freio"
    assert rep["conversion"] == {
        "applied_over_total": 0.3333,
        "skipped_complex_over_total": 0.3333,
        "errors_over_total": 0.3333,
    }
    assert rep["cache"] == {"hits": 2}
    assert rep["jobs"][0] == {
        "url": "https://x.com/jobs/1/", "title": "T1", "company": "C1",
        "status": "APPLIED", "from_cache": True,
    }
    assert rep["jobs"][2]["from_cache"] is False


def test_telemetria_sem_vagas_tem_taxa_zero(request_):
    rep = AppController.build_telemetry([], request_, START, END)
    assert rep["aborted_reason"] is None
    assert rep["conversion"]["applied_over_total"] == 0.0
    assert rep["cache"] == {"hits": 0}
    assert rep["jobs"] == []


def test_execute_exporta_e_anexa_caminho_no_sumario(tmp_path, request_):
    service = MagicMock()
    service.run.return_value = [_job(1, JobStatus.APPLIED)]
    service.last_abort_reason = "freio de erros"
    out = tmp_path / "rel"
    summary = AppController(service, reports_dir=str(out), clock=_clock()).execute(request_)

    path = out / "telemetry_20261102.json"
    assert summary.endswith(f"\nTelemetria:           {path}")
    texto = path.read_text(encoding="utf-8")
    doc = json.loads(texto)
    assert doc["date"] == "2026-11-02"
    assert doc["runs"][0]["aborted_reason"] == "freio de erros"
    assert texto.startswith('{\n  "date"')  # indent=2


def test_execute_ignora_motivo_que_nao_e_texto(tmp_path, request_):
    service = MagicMock()  # last_abort_reason vira MagicMock, nao str
    service.run.return_value = []
    AppController(service, reports_dir=str(tmp_path), clock=_clock()).execute(request_)
    doc = json.loads((tmp_path / "telemetry_20261102.json").read_text(encoding="utf-8"))
    assert doc["runs"][0]["aborted_reason"] is None


def test_export_preserva_acentos(tmp_path, request_):
    service = MagicMock()
    service.run.return_value = [Job(url="https://x.com/j/1/", platform="linkedin",
                                    title="Engenheiro São Paulo", company="Ação")]
    AppController(service, reports_dir=str(tmp_path), clock=_clock()).execute(request_)
    texto = (tmp_path / "telemetry_20261102.json").read_text(encoding="utf-8")
    assert "Engenheiro São Paulo" in texto and "Ação" in texto


def test_segunda_execucao_no_dia_acrescenta(tmp_path, request_):
    service = MagicMock()
    service.run.return_value = []
    for _ in range(2):
        AppController(service, reports_dir=str(tmp_path), clock=_clock()).execute(request_)
    doc = json.loads((tmp_path / "telemetry_20261102.json").read_text(encoding="utf-8"))
    assert len(doc["runs"]) == 2


@pytest.mark.parametrize("conteudo", ["{ nao e json", "[]", '{"runs": "x"}'])
def test_arquivo_ilegivel_e_preservado(tmp_path, request_, caplog, conteudo):
    path = tmp_path / "telemetry_20261102.json"
    path.write_text(conteudo, encoding="utf-8")
    service = MagicMock()
    service.run.return_value = []
    with caplog.at_level(logging.WARNING):
        AppController(service, reports_dir=str(tmp_path), clock=_clock()).execute(request_)

    backup = tmp_path / "telemetry_20261102.json.corrupt-103006"
    assert backup.read_text(encoding="utf-8") == conteudo
    assert len(json.loads(path.read_text(encoding="utf-8"))["runs"]) == 1
    assert "preservada em" in caplog.text and str(backup) in caplog.text


def test_falha_de_io_nao_derruba_e_e_registrada(tmp_path, request_, caplog):
    ocupado = tmp_path / "arquivo"
    ocupado.write_text("x")  # reports_dir apontando para um ARQUIVO => OSError
    service = MagicMock()
    service.run.return_value = []
    with caplog.at_level(logging.ERROR):
        summary = AppController(service, reports_dir=str(ocupado), clock=_clock()).execute(request_)

    assert "Telemetria:" not in summary
    assert "Falha ao exportar a telemetria em" in caplog.text
