"""Shadow Mode (nunca clica em Submit) e parada estrita (tela inesperada aborta o lote)."""
import pytest

from tests.application.fakes import SEL as SEL_COM_CONFIRMACAO, FakeCache
from src.application.app_service import AppService
from src.application.dtos.search_request import LINKEDIN_DEFAULT_SELECTORS, SearchRequest
from src.domain.entities.job import JobStatus

SEL = {**SEL_COM_CONFIRMACAO, "abort_indicator": "[data-x=captcha]"}
CARDS = [{"url": f"https://x.com/jobs/{i}", "title": "t", "company": "c"} for i in (1, 2)]


class Fake:
    def __init__(self, visible):
        self.visible, self.clicks, self.opened = set(visible), [], []

    def open_url(self, url): self.opened.append(url)
    def get_current_url(self): return self.opened[-1] if self.opened else ""
    def scroll_container_to_end(self, sel): pass
    def extract_job_cards(self, card_selector, title_selector=None, company_selector=None): return CARDS
    def element_exists(self, sel): return sel in self.visible
    def click(self, sel): self.clicks.append(sel)
    def has_empty_required_inputs(self, sel): return False
    def modal_signature(self, sel): return ""
    def dismiss_overlay_if_present(self, sel, timeout): return False
    def wait_until_hidden(self, sel, timeout): return True


def _req(**kw):
    return SearchRequest(platform="p", static_urls=["https://x.com/s"], selectors=SEL, **{"strict_abort": False, **kw})


def test_shadow_nunca_clica_submit_e_descarta():
    b = Fake({SEL["apply_button"], SEL["submit_button"]})
    jobs = AppService(b).run(_req(shadow_mode=True, max_applications=5))
    assert SEL["submit_button"] not in b.clicks
    assert b.clicks[-1:] == [SEL["close_button"]]
    assert [j.status for j in jobs] == [JobStatus.SIMULATED] * 2


def test_sem_shadow_clica_submit():
    b = Fake({SEL["apply_button"], SEL["submit_button"]})
    AppService(b, FakeCache()).run(_req(max_applications=1))
    assert SEL["submit_button"] in b.clicks


class NaVaga(Fake):
    """Checkpoint so aparece ao abrir uma VAGA (a listagem carrega normal)."""
    def element_exists(self, sel):
        if sel == "[data-x=captcha]":
            return "/jobs/" in (self.opened[-1] if self.opened else "")
        return super().element_exists(sel)


def test_strict_abort_na_pagina_para_o_lote():
    b = NaVaga(set())
    svc = AppService(b)
    jobs = svc.run(_req(strict_abort=True))
    assert b.opened == ["https://x.com/s", "https://x.com/jobs/1/"]  # nao tentou a vaga 2
    assert [j.status for j in jobs] == [JobStatus.PENDING] * 2
    assert svc.last_abort_reason == (
        "parada estrita: tela inesperada ([data-x=captcha]) em https://x.com/jobs/1/")
    assert b.clicks == []


def test_strict_abort_na_listagem_sem_cards_nao_abre_a_segunda_url():
    b = Fake({"[data-x=captcha]"})
    b.extract_job_cards = lambda *a, **k: []
    svc = AppService(b)
    req = SearchRequest(platform="p", static_urls=["https://x.com/a", "https://x.com/b"],
                        selectors=SEL, strict_abort=True)
    assert svc.run(req) == []
    assert b.opened == ["https://x.com/a"]
    assert svc.last_abort_reason == "parada estrita: tela inesperada ([data-x=captcha]) em https://x.com/a"


def test_strict_abort_por_desvio_de_dominio():
    b = Fake(set())
    b.get_current_url = lambda: "https://outro.com/login" if len(b.opened) > 1 else "https://www.x.com/s"
    svc = AppService(b)
    jobs = svc.run(_req(strict_abort=True))
    assert b.opened == ["https://x.com/s", "https://x.com/jobs/1/"]
    assert jobs[0].status == JobStatus.PENDING and b.clicks == []
    assert svc.last_abort_reason == (
        "parada estrita: desvio de dominio (x.com -> outro.com) em https://x.com/jobs/1/")


def test_url_atual_vazia_nao_e_desvio():
    b = Fake(set())
    b.get_current_url = lambda: ""
    svc = AppService(b)
    svc.run(_req(strict_abort=True, max_applications=1))
    assert svc.last_abort_reason is None


def test_strict_abort_dentro_do_modal_nao_clica_nada():
    class Late(Fake):
        def element_exists(self, sel):
            if sel == "[data-x=captcha]":
                return bool(self.clicks)  # so aparece depois de abrir o modal
            return super().element_exists(sel)
    b = Late({SEL["apply_button"], SEL["submit_button"]})
    svc = AppService(b)
    jobs = svc.run(_req(strict_abort=True, max_applications=5))
    assert b.clicks == [SEL["apply_button"]]
    assert jobs[0].status == JobStatus.PENDING and svc.last_abort_reason


def test_sem_strict_ignora_o_indicador():
    b = Fake({"[data-x=captcha]"})
    svc = AppService(b)
    svc.run(_req())
    assert svc.last_abort_reason is None and len(b.opened) == 3


def test_strict_abort_exige_indicador():
    sem_desafio = {k: v for k, v in LINKEDIN_DEFAULT_SELECTORS.items() if not k.startswith("abort_")}
    with pytest.raises(ValueError, match="abort_indicator"):
        SearchRequest(platform="p", static_urls=["u"], selectors=sem_desafio, strict_abort=True)


def test_shadow_desligado_e_parada_estrita_ligada_por_padrao():
    r = SearchRequest(platform="p", static_urls=["u"], selectors=LINKEDIN_DEFAULT_SELECTORS)
    assert (r.shadow_mode, r.strict_abort) == (False, True)


def test_modal_travado_descarta_com_erro_sem_esperar_15_passos():
    class Preso(Fake):
        def modal_signature(self, sel): return "igual"
    b = Preso({SEL["apply_button"], SEL["next_button"]})
    jobs = AppService(b).run(_req(max_applications=1, max_consecutive_errors=1))
    assert jobs[0].status == JobStatus.ERROR
    assert b.clicks.count(SEL["next_button"]) == 1  # 2o passo ja detecta
    assert b.clicks[-1] == SEL["close_button"]


def test_assinatura_diferente_ou_vazia_nao_trava():
    class Muda(Fake):
        n = 0
        def modal_signature(self, sel):
            Muda.n += 1
            return f"s{Muda.n}"
        def click(self, sel):
            super().click(sel)
            if sel == SEL["next_button"]:
                self.visible = {SEL["apply_button"], SEL["submit_button"], SEL["submit_confirmation"]}
    b = Muda({SEL["apply_button"], SEL["next_button"]})
    jobs = AppService(b, FakeCache()).run(_req(max_applications=1))
    assert jobs[0].status == JobStatus.APPLIED
