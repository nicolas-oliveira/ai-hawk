"""Mensagens de log com igualdade EXATA (lote C1 do bloco 2).

`"msg" in caplog.text` nao pega o mutante `"XXmsgXX"`: o texto original continua la dentro.
Aqui cada mensagem e comparada inteira, com nivel, e o numero de registros e fixo.
"""
import logging
import re
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.application import app_service as svc_mod
from src.application.app_controller import AppController
from src.application.app_service import CallTiming, JsonJobCache, MAX_MODAL_STEPS, AppService, _TimedBrowser
from src.application.dtos.search_request import LINKEDIN_DEFAULT_SELECTORS, SearchRequest
from src.domain.entities.job import Job, JobStatus
from tests.application.fakes import SEL, FakeBrowser, cards

ERRO, AVISO, INFO, DEPURA = logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG
MODAL = LINKEDIN_DEFAULT_SELECTORS["modal_container"]
URL = "https://x.com/jobs/1/"


def _job(url=URL):
    return Job(url=url, platform="p", title="", company="")


def _req(**kw):
    return SearchRequest(platform="p", static_urls=["u"], selectors=SEL,
                         **{"strict_abort": False, "shadow_mode": True, **kw})


def _logs(caplog, prefixo=""):
    """(nivel, mensagem) dos registros da aplicacao, na ordem."""
    return [(r.levelno, r.getMessage()) for r in caplog.records
            if r.name.startswith("src.application") and r.getMessage().startswith(prefixo)]


@pytest.fixture(autouse=True)
def _tudo(caplog):
    caplog.set_level(logging.DEBUG)


# ------------------------------------------------------------- telemetria
def test_falha_ao_exportar_telemetria(tmp_path, caplog):
    arquivo = tmp_path / "arquivo"
    arquivo.write_text("x")  # "pasta" que e arquivo: makedirs levanta OSError
    finished = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
    ctrl = AppController(MagicMock(), reports_dir=str(arquivo / "rel"))

    assert ctrl._export_telemetry({}, finished) is None

    caminho = str(arquivo / "rel" / "telemetry_20261102.json")
    assert _logs(caplog) == [(ERRO, f"Falha ao exportar a telemetria em {caminho}")]


def test_telemetria_corrompida_e_preservada(tmp_path, caplog):
    caminho = tmp_path / "telemetry_20261102.json"
    caminho.write_text("{ nao e json")
    finished = datetime(2026, 11, 2, 10, 30, 5, tzinfo=timezone.utc)

    AppController._load_day_document(str(caminho), finished)

    backup = f"{caminho}.corrupt-103005"
    assert _logs(caplog) == [(AVISO, f"Telemetria existente ilegivel; preservada em {backup}")]


# --------------------------------------------------------- proxy cronometrado
def _relogio(monkeypatch, valores):
    it = iter(valores)
    monkeypatch.setattr(svc_mod.time, "perf_counter", lambda: next(it))


def test_chamada_rapida_so_loga_debug(monkeypatch, caplog):
    _relogio(monkeypatch, [0.0, 0.25])
    inner = MagicMock(); inner.element_exists.return_value = False

    _TimedBrowser(inner, []).element_exists("#a")

    assert _logs(caplog) == [(DEPURA, "element_exists(#a) -> False em 0.25 s")]


def test_chamada_lenta_loga_debug_e_info(monkeypatch, caplog):
    _relogio(monkeypatch, [0.0, 2.0])
    inner = MagicMock(); inner.element_exists.return_value = False

    _TimedBrowser(inner, []).element_exists("#a")

    assert _logs(caplog) == [
        (DEPURA, "element_exists(#a) -> False em 2.00 s"),
        (INFO, "Chamada lenta: element_exists(#a) -> False em 2.00 s"),
    ]


def test_resumo_de_tempo_no_log(caplog):
    svc = AppService(FakeBrowser())
    svc.timings.append(CallTiming("open_url", "u", 0.5, "None"))

    svc._log_timing_summary()

    assert _logs(caplog) == [
        (INFO, "Tempo por chamada ao navegador (total 0.50 s):"),
        (INFO, "  " + svc.timing_report()[0]),
    ]


def test_calltiming_e_imutavel():
    with pytest.raises(FrozenInstanceError):
        CallTiming("m", "t", 1.0, "None").seconds = 2.0


# ------------------------------------------------------------------ cache
def test_cache_ilegivel_e_preservado(tmp_path, caplog):
    caminho = tmp_path / "h.json"
    caminho.write_text("{ nao e json")

    JsonJobCache(str(caminho)).get(_job())

    [(nivel, msg)] = _logs(caplog)
    assert nivel == AVISO
    assert re.fullmatch(re.escape(f"Cache ilegivel; preservado em {caminho}.corrupt-") + r"\d{6}", msg)


def test_cache_ilegivel_que_nao_da_para_preservar(tmp_path, monkeypatch, caplog):
    caminho = tmp_path / "h.json"
    caminho.write_text("{ nao e json")
    def falha(*_a): raise OSError("sem permissao")
    monkeypatch.setattr(svc_mod.os, "replace", falha)

    JsonJobCache(str(caminho)).get(_job())

    assert _logs(caplog) == [(ERRO, f"Cache ilegivel e nao foi possivel preserva-lo: {caminho}")]


def test_falha_ao_gravar_o_cache_segue_em_memoria(tmp_path, caplog):
    arquivo = tmp_path / "arquivo"
    arquivo.write_text("x")
    caminho = str(arquivo / "h.json")
    job = _job(); job.mark_skipped_complex()

    JsonJobCache(caminho).put(job)

    assert _logs(caplog) == [(ERRO, f"Falha ao gravar o cache em {caminho} (seguindo so em memoria).")]


# ------------------------------------------------------------------ run()
def _servico_que_resolve(status_final):
    svc = AppService(FakeBrowser(job_cards=cards(1, 2, 3)))
    def resolve(job, _request):
        job.status = status_final
    svc._process_job = resolve
    return svc


def test_limite_de_candidaturas_loga_uma_vez_e_para(caplog):
    svc = _servico_que_resolve(JobStatus.APPLIED)

    jobs = svc.run(_req(max_applications=1))

    assert [j.status for j in jobs] == [JobStatus.APPLIED, JobStatus.PENDING, JobStatus.PENDING]
    assert _logs(caplog, "Limite") == [(INFO, "Limite de 1 candidaturas atingido.")]


def test_freio_de_erros_consecutivos_loga_o_motivo(caplog):
    svc = _servico_que_resolve(JobStatus.ERROR)

    svc.run(_req(max_consecutive_errors=2))

    assert svc.last_abort_reason == "2 erros consecutivos (limite 2)"
    assert _logs(caplog, "Sessao") == [(ERRO, "Sessao interrompida: 2 erros consecutivos (limite 2).")]


def test_falha_ao_listar_uma_url(caplog):
    browser = FakeBrowser()
    def falha(url): raise RuntimeError("rede")
    browser.open_url = falha

    AppService(browser)._collect_jobs(_req())

    assert _logs(caplog, "Falha") == [(ERRO, "Falha ao listar vagas em u; seguindo para a proxima URL.")]


# --------------------------------------------------------- _process_job
def test_sem_botao_de_candidatura(caplog):
    job = _job()

    AppService(FakeBrowser())._process_job(job, _req())

    assert job.status is JobStatus.SKIPPED_COMPLEX
    assert _logs(caplog, "Sem botao") == [
        (INFO, f"Sem botao de candidatura visivel ({SEL['apply_button']}): {URL}")]


def test_erro_ao_processar_a_vaga(caplog):
    browser = FakeBrowser()
    def falha(url): raise RuntimeError("rede")
    browser.open_url = falha
    job = _job()

    AppService(browser)._process_job(job, _req())

    assert job.status is JobStatus.ERROR
    assert _logs(caplog, "Erro ao") == [(ERRO, f"Erro ao processar {URL}")]


def test_falha_ao_descartar_apos_erro(caplog):
    browser = FakeBrowser()
    def falha(sel): raise RuntimeError("caiu")
    browser.element_exists = falha

    AppService(browser)._discard_quietly(SEL)

    assert _logs(caplog, "Falha") == [(ERRO, "Falha ao descartar o modal apos erro.")]


# --------------------------------------------------------------- _run_modal
def _modal(vazio=False, assinaturas=None, existe=None):
    b = MagicMock()
    b.has_empty_required_inputs.return_value = vazio
    b.element_exists.side_effect = existe or (lambda s: False)
    b.modal_signature.side_effect = assinaturas or (lambda s: "")
    return b


def test_modal_com_campo_obrigatorio(caplog):
    AppService(_modal(vazio=True))._run_modal(_job(), _req())
    assert _logs(caplog, "Regra") == [
        (INFO, f"Regra 3C: campo obrigatorio vazio no passo; descartando ({MODAL}).")]


def test_modal_shadow(caplog):
    submit = SEL["submit_button"]
    AppService(_modal(existe=lambda s: s == submit))._run_modal(_job(), _req(shadow_mode=True))
    assert _logs(caplog, "Shadow") == [(INFO, f"Shadow Mode: Submit NAO clicado em {URL}.")]


def test_modal_sem_progresso(caplog):
    proximo = SEL["next_button"]
    AppService(_modal(assinaturas=lambda s: "igual", existe=lambda s: s == proximo))._run_modal(_job(), _req())
    assert _logs(caplog, "Modal") == [(AVISO, "Modal sem progresso entre dois passos; descartando.")]


def test_modal_sem_botao_de_avanco(caplog):
    AppService(_modal())._run_modal(_job(), _req())
    assert _logs(caplog, "Passo") == [
        (AVISO, "Passo do modal sem botao de avanco reconhecido; descartando.")]


def test_modal_estoura_o_limite_de_passos(caplog):
    contador = iter(range(1000))
    proximo = SEL["next_button"]
    job = _job()

    AppService(_modal(assinaturas=lambda s: str(next(contador)),
                      existe=lambda s: s == proximo))._run_modal(job, _req())

    assert job.status is JobStatus.ERROR
    assert _logs(caplog, "Limite") == [
        (AVISO, f"Limite de {MAX_MODAL_STEPS} passos do modal excedido; descartando.")]


def test_assinatura_do_primeiro_passo_nao_e_comparada_com_texto_inicial():
    # O valor inicial de `last_signature` nao pode colidir com uma assinatura real.
    assinaturas = iter(["XXXX", "outra"])
    submit, proximo = SEL["submit_button"], SEL["next_button"]
    avancou = []
    b = _modal(assinaturas=lambda s: next(assinaturas),
               existe=lambda s: s == submit if avancou else s == proximo)
    b.click.side_effect = lambda s: avancou.append(s)
    job = _job()

    AppService(b)._run_modal(job, _req(shadow_mode=True))

    assert job.status is JobStatus.SIMULATED
