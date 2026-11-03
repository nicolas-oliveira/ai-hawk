"""Envio real: so sucesso CONFIRMADO vira APPLIED; o resto vai para revisao manual."""
import pytest

from src.application.app_controller import AppController
from src.application.app_service import AbortReason, AppService
from src.application.dtos.search_request import CHALLENGE_URL_PATTERN, SearchRequest
from src.domain.entities.job import JobStatus, ReviewReason
from tests.application.fakes import SEL, FakeBrowser, FakeCache, cards

CONFIRMACAO = "[data-x=enviado]"
URL_VAGA = "https://x.com/jobs/1/"
ABERTA = {SEL["apply_button"], SEL["modal_container"], SEL["submit_button"]}


def _request(confirmacao=True, **kw):
    seletores = {**SEL, "abort_url_pattern": CHALLENGE_URL_PATTERN}
    if confirmacao:
        seletores["submit_confirmation"] = CONFIRMACAO
    else:
        del seletores["submit_confirmation"]
    return SearchRequest(
        platform="p", static_urls=["https://x.com/s"], selectors=seletores,
        max_applications=5, max_consecutive_errors=1, **kw,
    )


def _envio_fecha_o_modal(browser, confirma=True):
    def ao_enviar(b):
        b.visible.discard(SEL["modal_container"])
        if confirma:
            b.visible.add(CONFIRMACAO)
    browser.on_click[SEL["submit_button"]] = ao_enviar


def _rodar(browser, cache=None, request=None, vagas=(1,)):
    browser.job_cards = cards(*vagas)
    service = AppService(browser, cache if cache is not None else FakeCache())
    return service, service.run(request or _request())


def test_intencao_e_gravada_antes_do_clique_de_envio():
    eventos = []
    browser = FakeBrowser(visible=ABERTA)
    browser.on_click[SEL["submit_button"]] = lambda b: eventos.append("clique_de_envio")

    _rodar(browser, FakeCache(events=eventos))

    assert eventos == ["intencao", "clique_de_envio"]


def test_envio_confirmado_vira_applied_e_vai_para_o_historico():
    browser = FakeBrowser(visible=ABERTA)
    _envio_fecha_o_modal(browser)
    cache = FakeCache()

    _, jobs = _rodar(browser, cache)

    assert jobs[0].status is JobStatus.APPLIED
    assert cache.saved == [(URL_VAGA, JobStatus.APPLIED)]


def test_envio_real_sem_submit_confirmation_recusa_antes_da_primeira_vaga():
    browser = FakeBrowser(visible=ABERTA)
    cache = FakeCache()

    service, jobs = _rodar(browser, cache, _request(confirmacao=False))

    assert service.last_abort_reason == AbortReason.SUBMIT_CONFIRMATION_REQUIRED
    assert AbortReason.SUBMIT_CONFIRMATION_REQUIRED == (
        "envio real exige selectors['submit_confirmation']; nenhuma vaga foi aberta"
    )
    assert (jobs, browser.opened, browser.clicks, cache.intents) == ([], [], [], [])


def test_shadow_sem_submit_confirmation_segue():
    browser = FakeBrowser(visible=ABERTA)

    service, jobs = _rodar(browser, request=_request(confirmacao=False, shadow_mode=True))

    assert service.last_abort_reason is None
    assert jobs[0].status is JobStatus.SIMULATED


def test_submit_sem_confirmacao_vira_revisao_manual():
    browser = FakeBrowser(visible=ABERTA)
    _envio_fecha_o_modal(browser, confirma=False)

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is ReviewReason.CONFIRMATION_MISSING


def test_submit_com_modal_ainda_aberto_vira_revisao_manual():
    browser = FakeBrowser(visible=ABERTA)

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is ReviewReason.MODAL_STILL_OPEN


def test_confirmacao_com_dialogo_aberto_vira_applied_e_fecha_o_dialogo():
    browser = FakeBrowser(visible=ABERTA)
    browser.on_click[SEL["submit_button"]] = lambda b: b.visible.add(CONFIRMACAO)

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.APPLIED
    assert browser.clicks[-2:] == [SEL["submit_button"], SEL["close_button"]]


def test_dialogo_fechado_apos_envio_confirmado_nao_e_fechado_de_novo():
    browser = FakeBrowser(visible=ABERTA)
    _envio_fecha_o_modal(browser)

    _rodar(browser)

    assert browser.clicks[-1] == SEL["submit_button"]


def test_falha_ao_fechar_dialogo_apos_envio_nao_rebaixa_applied(caplog):
    browser = FakeBrowser(visible=ABERTA, click_raises={SEL["close_button"]})
    browser.on_click[SEL["submit_button"]] = lambda b: b.visible.add(CONFIRMACAO)
    cache = FakeCache()

    service, jobs = _rodar(browser, cache)

    assert jobs[0].status is JobStatus.APPLIED
    assert cache.saved == [(URL_VAGA, JobStatus.APPLIED)]
    assert service.last_abort_reason is None
    assert "Envio confirmado, mas o dialogo nao fechou; seguindo." in _mensagens(caplog)


def test_submit_com_excecao_no_clique_vira_revisao_manual_e_nao_erro():
    browser = FakeBrowser(visible=ABERTA, click_raises={SEL["submit_button"]})

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is ReviewReason.CLICK_FAILED


def test_falha_ao_observar_o_envio_vira_revisao_manual():
    browser = FakeBrowser(visible=ABERTA)
    def falha(sel, timeout):
        raise RuntimeError("pagina fechou")
    browser.wait_for_loader_to_disappear = falha

    _, jobs = _rodar(browser)

    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is ReviewReason.CONFIRMATION_MISSING


def test_revisao_manual_nao_conta_no_freio_de_erros():
    browser = FakeBrowser(visible=ABERTA, click_raises={SEL["submit_button"]})

    service, jobs = _rodar(browser, vagas=(1, 2))

    assert [j.status for j in jobs] == [JobStatus.MANUAL_REVIEW] * 2
    assert service.last_abort_reason is None


def test_revisao_manual_fica_no_historico_e_nao_e_reenviada():
    cache = FakeCache()
    browser = FakeBrowser(visible=ABERTA, click_raises={SEL["submit_button"]})

    _rodar(browser, cache)

    assert cache.saved == [(URL_VAGA, JobStatus.MANUAL_REVIEW)]


def test_queda_apos_a_intencao_nunca_reabre_a_vaga():
    cache = FakeCache(remembered={("p", URL_VAGA): JobStatus.SUBMITTING})
    browser = FakeBrowser(visible=ABERTA)

    _, jobs = _rodar(browser, cache)

    assert browser.opened == ["https://x.com/s"]
    assert jobs[0].status is JobStatus.MANUAL_REVIEW
    assert jobs[0].review_reason is ReviewReason.INTERRUPTED_BEFORE_RESULT
    assert jobs[0].from_cache is True


def test_falha_ao_gravar_a_intencao_nao_clica_em_enviar():
    class CacheSemDisco(FakeCache):
        def record_submitting(self, job):
            raise OSError("disco cheio")
    browser = FakeBrowser(visible=ABERTA)

    _, jobs = _rodar(browser, CacheSemDisco())

    assert SEL["submit_button"] not in browser.clicks
    assert jobs[0].status is JobStatus.ERROR


def test_shadow_mode_nunca_grava_intencao():
    cache = FakeCache()
    browser = FakeBrowser(visible=ABERTA)

    _, jobs = _rodar(browser, cache, _request(shadow_mode=True))

    assert cache.intents == []
    assert jobs[0].status is JobStatus.SIMULATED


def test_envio_real_sem_historico_nao_envia_e_para_o_lote():
    browser = FakeBrowser(visible=ABERTA)
    browser.job_cards = cards(1, 2)
    service = AppService(browser)

    jobs = service.run(_request())

    assert service.last_abort_reason == AbortReason.HISTORY_REQUIRED.format(url=URL_VAGA)
    assert SEL["submit_button"] not in browser.clicks
    assert browser.clicks[-1] == SEL["close_button"]
    assert [j.status for j in jobs] == [JobStatus.PENDING, JobStatus.PENDING]
    assert browser.opened == ["https://x.com/s", URL_VAGA]


def test_shadow_mode_roda_sem_historico():
    browser = FakeBrowser(visible=ABERTA)
    service = AppService(browser)

    jobs = service.run(_request(shadow_mode=True))

    assert service.last_abort_reason is None
    assert jobs[0].status is JobStatus.SIMULATED


class _Servico:
    last_abort_reason = None

    def __init__(self, jobs):
        self._jobs = jobs

    def run(self, request):
        return self._jobs


def test_sumario_lista_a_revisao_manual_no_fim():
    browser = FakeBrowser(visible=ABERTA, click_raises={SEL["submit_button"]})
    _, jobs = _rodar(browser)

    resumo = AppController(_Servico(jobs), reports_dir=None).execute(_request())

    assert resumo.splitlines()[-2:] == [
        "Revisao manual:",
        f"  - t | {URL_VAGA} | {ReviewReason.CLICK_FAILED}",
    ]


def test_sumario_sem_revisao_manual_nao_traz_a_lista():
    resumo = AppController(_Servico([]), reports_dir=None).execute(_request())
    assert "Revisao manual" not in resumo


def test_telemetria_conta_a_revisao_manual_no_funil():
    browser = FakeBrowser(visible=ABERTA, click_raises={SEL["submit_button"]})
    _, jobs = _rodar(browser)

    from datetime import datetime
    agora = datetime(2026, 11, 3)
    relatorio = AppController.build_telemetry(jobs, _request(), agora, agora)

    assert relatorio["funnel"]["manual_review"] == 1


def _mensagens(caplog):
    # Mensagem inteira, nao trecho: um texto embrulhado em outro nao pode passar.
    return [registro.getMessage() for registro in caplog.records]


def test_clique_de_envio_que_falha_deixa_rastro_no_log(caplog):
    browser = FakeBrowser(visible=ABERTA, click_raises={SEL["submit_button"]})
    _rodar(browser)
    assert "Clique de envio falhou; vaga vai para revisao manual." in _mensagens(caplog)


def test_observacao_que_falha_deixa_rastro_no_log(caplog):
    browser = FakeBrowser(visible=ABERTA)
    def falha(sel, timeout):
        raise RuntimeError("pagina fechou")
    browser.wait_for_loader_to_disappear = falha
    _rodar(browser)
    assert "Nao foi possivel observar o envio; vaga vai para revisao manual." in _mensagens(caplog)
