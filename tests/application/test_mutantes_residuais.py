"""Mutantes residuais: mensagens, chaves e arredondamentos que ninguem fixava."""
import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.application import app_service as svc_mod
from src.application.app_controller import AppController
from src.application.app_service import AppService
from src.application.dtos import search_request as sr
from src.application.dtos.search_request import LINKEDIN_DEFAULT_SELECTORS, SearchRequest
from src.domain.entities.job import Job, JobStatus

T0 = datetime(2026, 11, 2, 10, 0, 0, tzinfo=timezone.utc)


def _req(**kw):
    return SearchRequest(platform="p", static_urls=["u"], selectors=LINKEDIN_DEFAULT_SELECTORS, **kw)


def test_controller_mensagem_de_tipo_e_linha_de_telemetria(tmp_path):
    with pytest.raises(TypeError, match=r"^execute\(\) espera uma instancia de SearchRequest\.$"):
        AppController(MagicMock()).execute("nao e request")
    svc = MagicMock(); svc.run.return_value = []; svc.last_abort_reason = None
    out = AppController(svc, reports_dir=str(tmp_path)).execute(_req())
    assert "\nTelemetria:           " in out and out.startswith("=" * 50)


def test_telemetria_arredonda_em_3_casas_e_conta_simulated():
    rep = AppController.build_telemetry(
        [Job(url="https://x.com/1/", platform="p", title="", company="", status=JobStatus.SIMULATED)],
        _req(), T0, T0 + timedelta(seconds=1, microseconds=234567))
    assert rep["duration_seconds"] == 1.235
    assert rep["funnel"]["simulated"] == 1


def test_company_vem_da_chave_company():
    b = MagicMock()
    b.extract_job_cards.return_value = [{"url": "https://x.com/jobs/1/", "title": "t", "company": "Acme"}]
    jobs = AppService(b)._collect_jobs(_req())
    assert (jobs[0].title, jobs[0].company) == ("t", "Acme")


def test_chaves_opcionais_registradas():
    assert "review_button" in sr.OPTIONAL_SELECTOR_KEYS and "abort_indicator" in sr.OPTIONAL_SELECTOR_KEYS


@pytest.mark.parametrize("termo", ['a"b', "a(b", "a)b"])
def test_termo_booleano_rejeita_aspas_e_parenteses(termo):
    with pytest.raises(ValueError, match="aspas ou parenteses"):
        sr.build_boolean_keywords([termo])


def test_mensagem_strict_abort_exata():
    with pytest.raises(ValueError, match=r"^strict_abort exige selectors\['abort_indicator'\]\.$"):
        SearchRequest(platform="p", static_urls=["u"], selectors=LINKEDIN_DEFAULT_SELECTORS, strict_abort=True)


def test_motivo_exato_da_parada_estrita():
    b = MagicMock(); b.element_exists.return_value = True
    svc = AppService(b)
    sel = {**LINKEDIN_DEFAULT_SELECTORS, "abort_indicator": "#cap"}
    req = SearchRequest(platform="p", static_urls=["u"], selectors=sel, strict_abort=True)
    assert svc._strict_abort("https://x.com/1/", req)
    assert svc.last_abort_reason == "parada estrita: tela inesperada (#cap) em https://x.com/1/"


def test_logs_do_modal_e_da_parada(caplog):
    caplog.set_level(logging.DEBUG)
    b = MagicMock()
    b.element_exists.return_value = True
    b.has_empty_required_inputs.return_value = True
    b.modal_signature.return_value = "s"
    svc = AppService(b)
    job = Job(url="https://x.com/1/", platform="p", title="", company="")
    svc._run_modal(job, _req())
    assert "Regra 3C: campo obrigatorio vazio no passo; descartando (.jobs-easy-apply-modal)." in caplog.text
    b.has_empty_required_inputs.return_value = False
    svc._run_modal(job, _req(shadow_mode=True))
    assert "Shadow Mode: Submit NAO clicado em https://x.com/1/." in caplog.text
    b.element_exists.side_effect = lambda s: s == LINKEDIN_DEFAULT_SELECTORS["next_button"]
    svc._run_modal(job, _req())
    assert "Modal sem progresso entre dois passos; descartando." in caplog.text


def test_termo_booleano_com_letra_x_e_valido():
    assert sr.build_boolean_keywords(["Xamarin", "Linux"]) == "(Xamarin OR Linux)"
