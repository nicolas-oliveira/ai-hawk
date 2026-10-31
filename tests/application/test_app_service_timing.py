from unittest.mock import MagicMock

import pytest

from src.application import app_service
from src.application.app_service import AppService, CallTiming, SLOW_CALL_SECONDS, _TimedBrowser


def _relogio(monkeypatch, passos):
    """perf_counter deterministico: cada chamada devolve o proximo valor."""
    valores = iter(passos)
    monkeypatch.setattr(app_service.time, "perf_counter", lambda: next(valores))


def test_proxy_repassa_chamada_e_registra_duracao_e_resultado(monkeypatch):
    _relogio(monkeypatch, [10.0, 13.0])
    inner = MagicMock()
    inner.element_exists.return_value = False
    sink = []

    resultado = _TimedBrowser(inner, sink).element_exists("button.x")

    assert resultado is False
    inner.element_exists.assert_called_once_with("button.x")
    assert sink == [CallTiming("element_exists", "button.x", 3.0, "False")]


def test_proxy_repassa_kwargs_sem_alterar_a_chamada(monkeypatch):
    _relogio(monkeypatch, [0.0, 0.1])
    inner = MagicMock()
    inner.dismiss_overlay_if_present.return_value = True
    sink = []

    _TimedBrowser(inner, sink).dismiss_overlay_if_present("[x]", timeout=3000)

    inner.dismiss_overlay_if_present.assert_called_once_with("[x]", timeout=3000)
    assert sink[0].result == "True"


def test_excecao_e_registrada_e_propagada(monkeypatch):
    _relogio(monkeypatch, [0.0, 2.0])
    inner = MagicMock()
    inner.click.side_effect = TimeoutError("sem elemento")
    sink = []

    with pytest.raises(TimeoutError):
        _TimedBrowser(inner, sink).click("button.y")

    assert sink[0].result == "EXC:TimeoutError"
    assert sink[0].seconds == 2.0


def test_listas_viram_len_no_resultado(monkeypatch):
    _relogio(monkeypatch, [0.0, 0.5])
    inner = MagicMock()
    inner.extract_job_cards.return_value = [{"url": "a"}, {"url": "b"}]
    sink = []

    _TimedBrowser(inner, sink).extract_job_cards("li")

    assert sink[0].result == "len=2"


def test_chamada_lenta_gera_log_info(monkeypatch, caplog):
    _relogio(monkeypatch, [0.0, SLOW_CALL_SECONDS + 1])
    inner = MagicMock()
    inner.element_exists.return_value = False

    with caplog.at_level("INFO", logger="src.application.app_service"):
        _TimedBrowser(inner, []).element_exists("#nada")

    assert "Chamada lenta" in caplog.text and "#nada" in caplog.text


def test_appservice_registra_chamadas_e_separa_sondagem_negativa_da_positiva(monkeypatch):
    inner = MagicMock()
    inner.element_exists.side_effect = [True, False]
    service = AppService(inner)

    service._browser.element_exists("a")
    service._browser.element_exists("b")

    relatorio = "\n".join(service.timing_report())
    assert "element_exists[True]" in relatorio and "element_exists[False]" in relatorio


def test_run_zera_as_medicoes_da_sessao_anterior():
    inner = MagicMock()
    inner.extract_job_cards.return_value = []
    inner.element_exists.return_value = False
    service = AppService(inner)
    service.timings.append(CallTiming("velho", "", 9.0, "None"))

    from src.application.dtos.search_request import SELECTOR_PROFILES, SearchRequest

    service.run(SearchRequest(platform="p", static_urls=["http://x/"], selectors=SELECTOR_PROFILES["linkedin"]))

    assert all(t.method != "velho" for t in service.timings)
    assert any(t.method == "open_url" for t in service.timings)
