"""Modal que nao abre apos o clique em Apply: com parada estrita, o lote para."""
from src.application.app_service import AbortReason, AppService
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import JobStatus
from tests.application.fakes import SEL, FakeBrowser, FakeCache, cards

INDICADOR = "[data-x=captcha]"
SELETORES = {**SEL, "abort_indicator": INDICADOR}


def _request(**kw):
    return SearchRequest(platform="p", static_urls=["https://x.com/s"], selectors=SELETORES, **kw)


def test_modal_que_nao_abre_para_o_lote_com_motivo():
    browser = FakeBrowser(visible={SEL["apply_button"]})
    service = AppService(browser)

    jobs = service.run(_request(strict_abort=True, max_applications=5))

    assert service.last_abort_reason == AbortReason.MODAL_NOT_OPENED.format(
        url="https://x.com/jobs/1/"
    )
    assert [j.status for j in jobs] == [JobStatus.PENDING, JobStatus.PENDING]


def test_modal_que_nao_abre_nao_tenta_a_vaga_seguinte():
    browser = FakeBrowser(visible={SEL["apply_button"]})

    AppService(browser).run(_request(strict_abort=True, max_applications=5))

    assert browser.opened == ["https://x.com/s", "https://x.com/jobs/1/"]


def test_modal_que_nao_abre_nao_clica_em_fechar_nem_descartar():
    browser = FakeBrowser(visible={SEL["apply_button"]})

    AppService(browser).run(_request(strict_abort=True))

    assert browser.clicks == [SEL["apply_button"]]


def test_modal_que_nao_abre_nao_vai_para_o_historico():
    cache = FakeCache()

    AppService(FakeBrowser(visible={SEL["apply_button"]}), cache).run(_request(strict_abort=True))

    assert cache.saved == []


def test_modal_aberto_segue_o_fluxo_normal():
    browser = FakeBrowser(
        visible={SEL["apply_button"], SEL["modal_container"], SEL["submit_button"]},
        job_cards=cards(1),
    )
    def envia(b):
        b.visible.discard(SEL["modal_container"])
        b.visible.update({SEL["submit_confirmation"], SEL["applied_state"]})
    browser.on_click[SEL["submit_button"]] = envia
    service = AppService(browser, FakeCache())

    jobs = service.run(_request(strict_abort=True, max_applications=5))

    assert service.last_abort_reason is None
    assert [j.status for j in jobs] == [JobStatus.APPLIED]


def test_sem_parada_estrita_modal_ausente_continua_sendo_erro():
    browser = FakeBrowser(visible={SEL["apply_button"]})
    service = AppService(browser)

    jobs = service.run(_request(strict_abort=False, max_applications=5, max_consecutive_errors=9))

    assert service.last_abort_reason is None
    assert jobs[0].status is JobStatus.ERROR
