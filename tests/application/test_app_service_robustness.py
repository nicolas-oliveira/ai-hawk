"""Robustez do AppService contra a realidade crua (mar aberto) e mutantes.

Usa um navegador falso minimo, so com o contrato publico do BrowserPort.
"""
import json
import logging
import re

import pytest

from tests.application.fakes import FakeCache
from src.application import app_service as svc_mod
from src.application.app_service import AppService, JsonJobCache, _TimedBrowser
from src.application.dtos.search_request import LINKEDIN_DEFAULT_SELECTORS, SearchRequest
from src.domain.entities.job import Job, JobStatus

SEL = dict(LINKEDIN_DEFAULT_SELECTORS)


class FakeBrowser:
    def __init__(self, cards=None, exists=lambda s: False, empty=False, click_raises=(),
                 open_raises=()):
        self.cards = cards if cards is not None else []
        self.exists = exists
        self.empty = empty
        self.click_raises = set(click_raises)
        self.open_raises = set(open_raises)
        self.clicks, self.opened, self.scrolled, self.dismissed = [], [], [], []

    def open_url(self, url):
        self.opened.append(url)
        if url in self.open_raises:
            raise RuntimeError("falha de navegacao")

    def scroll_container_to_end(self, sel):
        self.scrolled.append(sel)

    def extract_job_cards(self, card_selector, title_selector=None, company_selector=None):
        return self.cards

    def element_exists(self, sel):
        return self.exists(sel)

    def click(self, sel):
        self.clicks.append(sel)
        if sel in self.click_raises:
            raise RuntimeError("timeout")

    def has_empty_required_inputs(self, sel):
        return self.empty

    def modal_signature(self, sel):
        return ""

    def dismiss_overlay_if_present(self, sel, timeout):
        self.dismissed.append((sel, timeout))
        return True

    def wait_for_loader_to_disappear(self, sel, timeout):
        return True


def _req(selectors=None, urls=("https://x.com/s",), **kw):
    return SearchRequest(platform="linkedin", static_urls=list(urls),
                         selectors=selectors or SEL, **kw)


def _cards(n, **extra):
    return [{"url": f"https://x.com/jobs/{i}/", "title": f"T{i}", "company": f"C{i}", **extra}
            for i in range(1, n + 1)]


def _only(*selectors):
    return lambda s: s in selectors


# ------------------------------------------------------------ mar aberto
def test_lista_sem_empresa_nao_e_falha():
    cards = [{"url": "https://x.com/catalogue/a/", "title": "Livro A"},
             {"url": "https://x.com/catalogue/b/", "title": "Livro B", "company": None}]
    jobs = AppService(FakeBrowser(cards=cards)).run(_req())
    assert [(j.title, j.company) for j in jobs] == [("Livro A", ""), ("Livro B", "")]


def test_titulo_ausente_ou_none_vira_vazio():
    cards = [{"url": "https://x.com/a/"}, {"url": "https://x.com/b/", "title": None}]
    jobs = AppService(FakeBrowser(cards=cards)).run(_req())
    assert [j.title for j in jobs] == ["", ""]


def test_itens_sem_link_proprio_sao_descartados_sem_erro():
    cards = [{"title": "Citacao 1"}, {"url": "", "title": "Citacao 2"}, {"url": None}]
    service = AppService(FakeBrowser(cards=cards))
    assert service.run(_req()) == []
    assert service.last_abort_reason is None


def test_card_sem_url_nao_interrompe_os_seguintes():
    cards = [{"title": "sem link"}] + _cards(1)
    assert len(AppService(FakeBrowser(cards=cards)).run(_req())) == 1


def test_scroll_recebe_o_container_do_perfil_inclusive_body():
    sel = dict(SEL, jobs_list_container="body")
    browser = FakeBrowser(cards=_cards(1))
    AppService(browser).run(_req(selectors=sel))
    assert browser.scrolled == ["body"]


def test_falha_numa_url_nao_derruba_as_demais(caplog):
    class Quebra(FakeBrowser):
        def scroll_container_to_end(self, sel):
            if self.opened[-1] == "https://x.com/ruim":
                raise RuntimeError("boom")
            super().scroll_container_to_end(sel)

    browser = Quebra(cards=_cards(1))
    with caplog.at_level(logging.ERROR):
        jobs = AppService(browser).run(_req(urls=["https://x.com/ruim", "https://x.com/boa"]))
    assert len(jobs) == 1
    assert "Falha ao listar vagas em https://x.com/ruim; seguindo para a proxima URL." in caplog.text


def test_timeout_do_overlay_e_constantes():
    assert svc_mod.SHORT_TIMEOUT_MS == 3000 and svc_mod.LOADER_TIMEOUT_MS == 5000
    assert svc_mod.MAX_MODAL_STEPS == 15 and svc_mod.SLOW_CALL_SECONDS == 1.0
    sel = dict(SEL, overlay_dismiss="#x")
    browser = FakeBrowser(cards=[], exists=_only("#x"))
    AppService(browser).run(_req(selectors=sel))
    assert browser.dismissed == [("#x", 3000)]


# ----------------------------------------------------------- laco principal
def test_limite_de_candidaturas_para_o_laco(caplog):
    m, s = SEL["modal_container"], SEL["submit_button"]
    browser = FakeBrowser(cards=_cards(3), exists=_only(SEL["apply_button"], s, m))
    with caplog.at_level(logging.INFO):
        jobs = AppService(browser, FakeCache()).run(_req(max_applications=1))
    assert [j.status for j in jobs] == [JobStatus.APPLIED, JobStatus.PENDING, JobStatus.PENDING]
    assert "Limite de 1 candidaturas atingido." in caplog.text
    assert browser.opened.count("https://x.com/jobs/2/") == 0


def test_freio_registra_erro_e_zera_contador_apos_sucesso(caplog):
    # E,E,OK,E,E com limite 3: so aborta se o contador NAO zerar no OK.
    ruins = {"https://x.com/jobs/1/", "https://x.com/jobs/2/", "https://x.com/jobs/4/", "https://x.com/jobs/5/"}
    browser = FakeBrowser(cards=_cards(5), exists=_only(SEL["apply_button"], SEL["submit_button"]),
                          open_raises=ruins)
    service = AppService(browser, FakeCache())
    jobs = service.run(_req(max_consecutive_errors=3))
    assert [j.status for j in jobs].count(JobStatus.ERROR) == 4
    assert service.last_abort_reason is None

    browser = FakeBrowser(cards=_cards(3), exists=_only(SEL["apply_button"]),
                          open_raises={c["url"] for c in _cards(3)})
    service = AppService(browser)
    with caplog.at_level(logging.ERROR):
        service.run(_req(max_consecutive_errors=2))
    assert service.last_abort_reason == "2 erros consecutivos (limite 2)"
    assert "Sessao interrompida: 2 erros consecutivos (limite 2)." in caplog.text


def test_motivo_de_aborto_comeca_vazio_e_e_limpo_a_cada_run():
    service = AppService(FakeBrowser())
    assert service.last_abort_reason is None
    service.last_abort_reason = "velho"
    service.run(_req())
    assert service.last_abort_reason is None


# ------------------------------------------------------------------- modal
def test_sem_botao_de_candidatura_pula_e_registra(caplog):
    with caplog.at_level(logging.INFO):
        jobs = AppService(FakeBrowser(cards=_cards(1))).run(_req())
    assert jobs[0].status is JobStatus.SKIPPED_COMPLEX
    assert f"Sem botao de candidatura visivel ({SEL['apply_button']}): https://x.com/jobs/1/" in caplog.text


def test_regra_3c_descarta_e_registra(caplog):
    m = SEL["modal_container"]
    browser = FakeBrowser(cards=_cards(1), exists=_only(SEL["apply_button"], SEL["discard_button"]),
                          empty=True)
    with caplog.at_level(logging.INFO):
        jobs = AppService(browser).run(_req())
    assert jobs[0].status is JobStatus.SKIPPED_COMPLEX
    assert browser.clicks == [SEL["apply_button"], SEL["close_button"], SEL["discard_button"]]
    assert f"Regra 3C: campo obrigatorio vazio no passo; descartando ({m})." in caplog.text


def test_review_button_opcional_avanca_quando_next_nao_existe():
    sel = dict(SEL, review_button="button.review")
    estado = {"passo": 0}

    def exists(s):
        if s == sel["apply_button"]:
            return True
        if s == sel["submit_button"]:
            return estado["passo"] >= 1
        return s == "button.review" and estado["passo"] == 0

    class Passo(FakeBrowser):
        def click(self, s):
            super().click(s)
            if s == "button.review":
                estado["passo"] = 1

    browser = Passo(cards=_cards(1), exists=exists)
    jobs = AppService(browser, FakeCache()).run(_req(selectors=sel))
    assert jobs[0].status is JobStatus.APPLIED
    assert browser.clicks == [sel["apply_button"], "button.review", sel["submit_button"]]


def test_passo_sem_botao_de_avanco_descarta_com_erro(caplog):
    browser = FakeBrowser(cards=_cards(1), exists=_only(SEL["apply_button"]))
    with caplog.at_level(logging.WARNING):
        jobs = AppService(browser).run(_req())
    assert jobs[0].status is JobStatus.ERROR
    assert SEL["close_button"] in browser.clicks
    assert "Passo do modal sem botao de avanco reconhecido; descartando." in caplog.text


def test_modal_que_nao_termina_para_em_15_passos(caplog):
    browser = FakeBrowser(cards=_cards(1), exists=_only(SEL["apply_button"], SEL["next_button"]))
    with caplog.at_level(logging.WARNING):
        jobs = AppService(browser).run(_req())
    assert jobs[0].status is JobStatus.ERROR
    assert browser.clicks.count(SEL["next_button"]) == 15
    assert "Limite de 15 passos do modal excedido; descartando." in caplog.text


def test_excecao_no_card_vira_erro_e_descarta_o_modal(caplog):
    browser = FakeBrowser(cards=_cards(1), exists=_only(SEL["apply_button"], SEL["modal_container"]),
                          click_raises={SEL["apply_button"]})
    with caplog.at_level(logging.ERROR):
        jobs = AppService(browser).run(_req())
    assert jobs[0].status is JobStatus.ERROR
    assert SEL["close_button"] in browser.clicks
    assert "Erro ao processar https://x.com/jobs/1/" in caplog.text


def test_descarte_apos_erro_nunca_propaga(caplog):
    def exists(s):
        if s == SEL["modal_container"]:
            raise RuntimeError("DOM sumiu")
        return s == SEL["apply_button"]

    browser = FakeBrowser(cards=_cards(1), exists=exists, click_raises={SEL["apply_button"]})
    with caplog.at_level(logging.ERROR):
        jobs = AppService(browser).run(_req())
    assert jobs[0].status is JobStatus.ERROR
    assert "Falha ao descartar o modal apos erro." in caplog.text


def test_descarte_sem_modal_visivel_nao_clica_em_fechar():
    browser = FakeBrowser(cards=_cards(1), exists=_only(SEL["apply_button"]),
                          click_raises={SEL["apply_button"]})
    AppService(browser).run(_req())
    assert SEL["close_button"] not in browser.clicks


# ------------------------------------------------------------------- cache
def _job(status=JobStatus.APPLIED, url="https://x.com/jobs/1/"):
    return Job(url=url, platform="linkedin", title="Engenheiro São", company="Ação", status=status)


def test_cache_grava_registro_completo_e_cria_pasta(tmp_path):
    path = tmp_path / "sub" / "c.json"
    JsonJobCache(str(path)).put(_job())
    texto = path.read_text(encoding="utf-8")
    doc = json.loads(texto)
    assert texto.startswith('{\n  "version": 1') and "Engenheiro São" in texto
    rec = doc["jobs"]["linkedin|https://x.com/jobs/1/"]
    assert (rec["status"], rec["title"], rec["company"]) == ("APPLIED", "Engenheiro São", "Ação")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d", rec["at"])
    assert not list(tmp_path.glob("sub/*.tmp")) and JsonJobCache.VERSION == 1


def test_cache_relido_devolve_o_status(tmp_path):
    path = str(tmp_path / "c.json")
    JsonJobCache(path).put(_job(JobStatus.SKIPPED_COMPLEX))
    assert JsonJobCache(path).get(_job(JobStatus.PENDING)) is JobStatus.SKIPPED_COMPLEX
    assert JsonJobCache(path).get(_job(url="https://x.com/outra/")) is None


@pytest.mark.parametrize("conteudo", ["{ ruim", "[]", '{"jobs": 1}'])
def test_cache_ilegivel_e_preservado(tmp_path, caplog, conteudo):
    path = tmp_path / "c.json"
    path.write_text(conteudo, encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        assert JsonJobCache(str(path)).get(_job()) is None
    backups = list(tmp_path.glob("c.json.corrupt-*"))
    assert len(backups) == 1 and backups[0].read_text(encoding="utf-8") == conteudo
    assert "Cache ilegivel; preservado em" in caplog.text


def test_cache_falha_de_gravacao_so_em_memoria(tmp_path, caplog):
    ocupado = tmp_path / "arquivo"
    ocupado.write_text("x")
    cache = JsonJobCache(str(ocupado / "c.json"))
    with caplog.at_level(logging.ERROR):
        cache.put(_job())
    assert cache.get(_job()) is JobStatus.APPLIED
    assert "Falha ao gravar o cache em" in caplog.text


def test_vaga_desconhecida_nao_impede_as_seguintes_de_usar_o_cache(tmp_path):
    cache = JsonJobCache(str(tmp_path / "c.json"))
    cache.put(_job(url="https://x.com/jobs/2/"))
    browser = FakeBrowser(cards=_cards(2), exists=_only(SEL["apply_button"]))
    jobs = AppService(browser, cache=cache).run(_req())
    assert [j.from_cache for j in jobs] == [False, True]
    assert jobs[1].status is JobStatus.ALREADY_APPLIED


# --------------------------------------------------------------- cronometro
def test_chamada_lenta_loga_no_limite_de_1s(monkeypatch, caplog):
    class Obj:
        def ping(self):
            return True

    def wrapper(duracao):
        seq = iter([10.0, 10.0 + duracao])
        monkeypatch.setattr(svc_mod.time, "perf_counter", lambda: next(seq))
        sink = []
        _TimedBrowser(Obj(), sink).ping()
        return sink[0]

    with caplog.at_level(logging.INFO):
        wrapper(0.9)
        assert "Chamada lenta" not in caplog.text
        t = wrapper(1.0)
    assert "Chamada lenta: ping() -> True em 1.00 s" in caplog.text
    assert (t.method, t.target, t.result) == ("ping", "", "True")


def test_resultado_resumido_e_excecao_registrada():
    class Obj:
        def a(self):
            return None

        def b(self, x):
            return [1, 2]

        def c(self, x):
            return {"k": 1}

        def d(self):
            return "texto"

        def e(self):
            raise ValueError("x")

    sink = []
    t = _TimedBrowser(Obj(), sink)
    t.a(), t.b("sel"), t.c("s"), t.d()
    with pytest.raises(ValueError):
        t.e()
    assert [x.result for x in sink] == ["None", "len=2", "len=1", "str", "EXC:ValueError"]
    assert sink[1].target == "sel"


def test_relatorio_de_tempo_ordenado_e_formatado(caplog):
    service = AppService(FakeBrowser())
    T = svc_mod.CallTiming
    service.timings.extend([
        T("click", "x", 0.5, "None"),
        T("element_exists", "a", 1.5, "False"),
        T("element_exists", "b", 2.0, "False"),
        T("element_exists", "c", 0.1, "True"),
    ])
    rel = service.timing_report()
    assert rel[0] == f"{'element_exists[False]':<40} {2:>3} chamadas {3.5:>7.2f} s"
    assert [l.split()[0] for l in rel] == ["element_exists[False]", "click", "element_exists[True]"]

    with caplog.at_level(logging.INFO):
        service._log_timing_summary()
    assert "Tempo por chamada ao navegador (total 4.10 s):" in caplog.text
    assert "  element_exists[False]" in caplog.text


def test_sem_chamadas_nao_loga_resumo(caplog):
    with caplog.at_level(logging.INFO):
        AppService(FakeBrowser())._log_timing_summary()
    assert "Tempo por chamada" not in caplog.text
