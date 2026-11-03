"""Historico em disco: a intencao de envio e gravada de forma duravel, antes do clique."""
import json
import os

import pytest

from src.application.app_service import JsonJobCache
from src.domain.entities.job import Job, JobStatus, ReviewReason


def _job(status=JobStatus.PENDING) -> Job:
    return Job(url="https://x.com/jobs/1/", platform="p", title="Dev", company="Co", status=status)


def _lido(caminho):
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)["jobs"]["p|https://x.com/jobs/1/"]


def test_intencao_de_envio_vai_para_o_arquivo(tmp_path):
    caminho = str(tmp_path / "historico.json")

    JsonJobCache(caminho).record_submitting(_job())

    registro = _lido(caminho)
    assert (registro["status"], registro["title"], registro["company"]) == ("SUBMITTING", "Dev", "Co")


def test_nova_execucao_lembra_a_intencao_sem_resultado(tmp_path):
    caminho = str(tmp_path / "historico.json")
    JsonJobCache(caminho).record_submitting(_job())

    assert JsonJobCache(caminho).get(_job()) is JobStatus.SUBMITTING


def test_resultado_posterior_sobrescreve_a_intencao(tmp_path):
    caminho = str(tmp_path / "historico.json")
    cache = JsonJobCache(caminho)
    cache.record_submitting(_job())
    job = _job(JobStatus.SUBMITTING)
    job.mark_applied()

    cache.put(job)

    assert JsonJobCache(caminho).get(_job()) is JobStatus.APPLIED


def test_revisao_manual_fica_no_historico(tmp_path):
    caminho = str(tmp_path / "historico.json")
    job = _job(JobStatus.SUBMITTING)
    job.mark_manual_review(ReviewReason.CONFIRMATION_MISSING)

    JsonJobCache(caminho).put(job)

    assert JsonJobCache(caminho).get(_job()) is JobStatus.MANUAL_REVIEW


def test_erro_continua_fora_do_historico(tmp_path):
    caminho = str(tmp_path / "historico.json")
    job = _job()
    job.mark_error()

    JsonJobCache(caminho).put(job)

    assert not os.path.exists(caminho)


def test_gravacao_da_intencao_faz_fsync_do_arquivo_e_da_pasta(tmp_path, monkeypatch):
    sincronizados = []
    real_fsync = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (sincronizados.append(fd), real_fsync(fd))[1])

    JsonJobCache(str(tmp_path / "historico.json")).record_submitting(_job())

    assert len(sincronizados) == 2  # arquivo temporario e pasta


def test_falha_ao_gravar_a_intencao_propaga(tmp_path):
    arquivo = tmp_path / "arquivo"
    arquivo.write_text("x")  # uma "pasta" que e arquivo: nao da para gravar dentro
    cache = JsonJobCache(str(arquivo / "historico.json"))

    with pytest.raises(OSError):
        cache.record_submitting(_job())


def _falha_ao_gravar():
    raise OSError("disco cheio")


@pytest.mark.parametrize("anterior", [None, JobStatus.SKIPPED_COMPLEX])
def test_falha_ao_gravar_intencao_nao_deixa_submitting_na_memoria(tmp_path, monkeypatch, anterior):
    caminho = str(tmp_path / "historico.json")
    cache = JsonJobCache(caminho)
    if anterior is not None:
        cache.put(_job(anterior))
    monkeypatch.setattr(cache, "_write_atomic", _falha_ao_gravar)

    with pytest.raises(OSError):
        cache.record_submitting(_job())

    assert cache.get(_job()) is anterior
    monkeypatch.undo()
    cache.put(_job())  # a mesma vaga, ainda PENDING
    outra = Job(url="https://x.com/jobs/2/", platform="p", title="", company="",
                status=JobStatus.SKIPPED_COMPLEX)
    cache.put(outra)  # forca a gravacao de tudo o que esta em memoria
    assert JsonJobCache(caminho).get(_job()) is anterior


def test_falha_ao_gravar_resultado_continua_so_em_memoria(tmp_path):
    arquivo = tmp_path / "arquivo"
    arquivo.write_text("x")
    cache = JsonJobCache(str(arquivo / "historico.json"))
    job = _job(JobStatus.SUBMITTING)
    job.mark_applied()

    cache.put(job)  # nao levanta

    assert cache.get(_job()) is JobStatus.APPLIED


def test_caminho_sem_pasta_grava_na_pasta_atual(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    JsonJobCache("historico.json").record_submitting(_job())

    assert os.listdir(tmp_path) == ["historico.json"]
