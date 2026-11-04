"""Segunda barreira anti-duplicada: a pagina diz se a vaga ja foi candidatada."""
import json
import logging

import pytest

from src.application.app_service import SHORT_TIMEOUT_MS, AbortReason, AppService, JsonJobCache
from src.application.dtos import search_request as sr
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import JobStatus, ReviewReason
from tests.application.fakes import APLICADA, CONFIRMACAO, SEL, FakeBrowser, FakeCache, cards

URL_LISTA = "https://x.com/s"
URL_VAGA = "https://x.com/jobs/1/"
ABERTA = {SEL["apply_button"], SEL["modal_container"], SEL["submit_button"]}


def _request(selectors=None, **kw):
    return SearchRequest(
        platform="p", static_urls=[URL_LISTA], selectors=selectors or SEL,
        max_applications=5, **kw,
    )


def _rodar(browser, cache=None, request=None, vagas=(1,)):
    browser.job_cards = cards(*vagas)
    service = AppService(browser, cache if cache is not None else FakeCache())
    return service, service.run(request or _request())


def _envio(browser, confirma=True, estado=True):
    def ao_enviar(b):
        b.visible.discard(SEL["modal_container"])
        if confirma:
            b.visible.add(CONFIRMACAO)
        if estado:
            b.visible.add(APLICADA)
    browser.on_click[SEL["submit_button"]] = ao_enviar


# ------------------------------------------------------- antes de abrir o dialogo
def test_pagina_ja_candidatada_vira_already_applied_sem_abrir_o_dialogo(caplog):
    caplog.set_level(logging.INFO)
    browser = FakeBrowser(visible=ABERTA, applied_before=True)
    cache = FakeCache()

    service, jobs = _rodar(browser, cache)

    assert jobs[0].status is JobStatus.ALREADY_APPLIED
    assert (browser.clicks, cache.intents) == ([], [])
    assert browser.state_reads == [(APLICADA, 0)]
    assert cache.saved == [(URL_VAGA, JobStatus.ALREADY_APPLIED)]
    mensagens = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert f"Pagina mostra a vaga como ja candidatada; dialogo nao aberto: {URL_VAGA}" in mensagens


def test_leitura_do_estado_vem_depois_do_strict_abort_e_antes_do_botao():
    eventos = []
    browser = FakeBrowser(visible=ABERTA, applied_before=True)
    original = browser.element_exists
    browser.element_exists = lambda s: (eventos.append(("existe", s)), original(s))[1]
    leitura = browser.job_shows_applied
    browser.job_shows_applied = lambda s, timeout: (eventos.append(("estado", s)), leitura(s, timeout))[1]

    _rodar(browser)

    assert ("estado", APLICADA) in eventos
    assert ("existe", SEL["apply_button"]) not in eventos


def test_selo_que_pinta_tarde_evita_skipped_complex():
    browser = FakeBrowser(visible={APLICADA})  # sem botao de candidatura

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.ALREADY_APPLIED
    assert browser.state_reads == [(APLICADA, 0), (APLICADA, SHORT_TIMEOUT_MS)]
    assert browser.clicks == []


def test_sem_botao_e_sem_selo_continua_skipped_complex():
    browser = FakeBrowser()

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.SKIPPED_COMPLEX
    assert browser.state_reads == [(APLICADA, 0), (APLICADA, SHORT_TIMEOUT_MS)]


def test_leitura_do_estado_que_falha_vira_error_sem_abrir_o_dialogo():
    browser = FakeBrowser(visible=ABERTA)
    def falha(sel, timeout): raise RuntimeError("pagina fechou")
    browser.job_shows_applied = falha

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.ERROR
    assert browser.clicks == [SEL["close_button"]]  # so a limpeza; nenhum clique de candidatura


def test_shadow_sem_applied_state_nao_le_o_estado():
    sem_estado = {k: v for k, v in SEL.items() if k != "applied_state"}
    browser = FakeBrowser(visible=ABERTA)

    service, jobs = _rodar(browser, request=_request(sem_estado, shadow_mode=True))

    assert jobs[0].status is JobStatus.SIMULATED
    assert browser.state_reads == []


# ------------------------------------------------------------ recusa no inicio
def test_envio_real_sem_applied_state_recusa_antes_da_primeira_vaga():
    sem_estado = {k: v for k, v in SEL.items() if k != "applied_state"}
    browser = FakeBrowser(visible=ABERTA)
    cache = FakeCache()

    service, jobs = _rodar(browser, cache, _request(sem_estado))

    assert service.last_abort_reason == AbortReason.JOB_STATE_REQUIRED
    assert AbortReason.JOB_STATE_REQUIRED == (
        "envio real exige selectors['applied_state']; nenhuma vaga foi aberta"
    )
    assert (jobs, browser.opened, browser.clicks, cache.intents) == ([], [], [], [])


def test_sem_confirmacao_a_recusa_citada_e_a_da_confirmacao():
    vazio = {k: v for k, v in SEL.items() if k not in ("applied_state", "submit_confirmation")}

    service, _ = _rodar(FakeBrowser(), request=_request(vazio))

    assert service.last_abort_reason == AbortReason.SUBMIT_CONFIRMATION_REQUIRED


# ------------------------------------------------------ depois do envio: combinacao
def test_confirmacao_e_estado_juntos_viram_applied_e_o_estado_espera_o_prazo_curto():
    browser = FakeBrowser(visible=ABERTA)
    _envio(browser)

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.APPLIED
    assert browser.state_reads == [(APLICADA, 0), (APLICADA, SHORT_TIMEOUT_MS)]


@pytest.mark.parametrize(
    "confirma,estado,motivo",
    [
        (True, False, ReviewReason.STATE_NOT_CONFIRMED),
        (False, True, ReviewReason.STATE_WITHOUT_CONFIRMATION),
        (False, False, ReviewReason.CONFIRMATION_MISSING),
    ],
)
def test_so_uma_evidencia_vai_para_revisao_manual_e_para_o_lote(confirma, estado, motivo):
    browser = FakeBrowser(visible=ABERTA)
    _envio(browser, confirma, estado)
    cache = FakeCache()

    service, jobs = _rodar(browser, cache, vagas=(1, 2))

    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is motivo
    assert jobs[1].status is JobStatus.PENDING and browser.opened.count(jobs[1].url) == 0
    assert service.last_abort_reason == AbortReason.MANUAL_REVIEW_STOP.format(url=URL_VAGA)
    assert cache.saved == [(URL_VAGA, JobStatus.MANUAL_REVIEW)]


def test_falha_ao_ler_o_estado_depois_do_envio_vai_para_revisao_manual():
    browser = FakeBrowser(visible=ABERTA)
    _envio(browser, estado=False)
    leitura = browser.job_shows_applied
    def falha(sel, timeout):
        if timeout:
            raise RuntimeError("pagina fechou")
        return leitura(sel, timeout)
    browser.job_shows_applied = falha

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is ReviewReason.CONFIRMATION_MISSING


# --------------------------------------- nunca reenviar: prova com o historico em disco
def test_vaga_em_revisao_manual_nunca_e_reaberta_no_lote_seguinte(tmp_path):
    caminho = str(tmp_path / "historico.json")
    primeiro = FakeBrowser(visible=ABERTA)
    _envio(primeiro, confirma=True, estado=False)  # enviada de verdade, mas a pagina nao mudou
    _rodar(primeiro, JsonJobCache(caminho))

    segundo = FakeBrowser(visible=ABERTA)
    service, jobs = _rodar(segundo, JsonJobCache(caminho))

    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is ReviewReason.ALREADY_IN_REVIEW
    assert (segundo.opened, segundo.clicks) == ([URL_LISTA], [])
    assert service.last_abort_reason is None


def test_already_applied_pela_pagina_vai_para_o_disco_e_nao_reabre(tmp_path):
    caminho = tmp_path / "historico.json"
    _rodar(FakeBrowser(visible=ABERTA, applied_before=True), JsonJobCache(str(caminho)))
    assert json.loads(caminho.read_text())["jobs"][f"p|{URL_VAGA}"]["status"] == "ALREADY_APPLIED"

    segundo = FakeBrowser(visible=ABERTA)
    _, jobs = _rodar(segundo, JsonJobCache(str(caminho)))

    assert jobs[0].status is JobStatus.ALREADY_APPLIED and jobs[0].from_cache
    assert (segundo.opened, segundo.clicks) == ([URL_LISTA], [])


# ------------------------------------------------------------------- perfis
def test_so_o_clone_ganha_applied_state():
    assert sr.LINKEDIN_CLONE_SELECTORS["applied_state"] == "[data-testid='job-applied']"
    assert "applied_state" not in sr.LINKEDIN_DEFAULT_SELECTORS
    assert "applied_state" in sr.OPTIONAL_SELECTOR_KEYS
