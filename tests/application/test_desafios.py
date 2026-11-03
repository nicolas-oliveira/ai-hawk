"""Desafios (checkpoint, captcha, trafego incomum, telefone): so parar, registrar e avisar."""
import pytest

from src.application.app_controller import AppController
from src.application.app_service import AbortReason, AppService, url_matches_pattern
from src.application.dtos.search_request import (
    OPTIONAL_SELECTOR_KEYS,
    CHALLENGE_MARKER,
    CHALLENGE_URL_PATTERN,
    SearchRequest,
)
from src.domain.entities.job import JobStatus
from tests.application.fakes import SEL, FakeBrowser

ROTAS = ["/checkpoint/challenge", "/captcha", "/unusual-traffic", "/verify-phone"]
SELETORES = {**SEL, "abort_url_pattern": CHALLENGE_URL_PATTERN, "abort_indicator": CHALLENGE_MARKER}


def _request(urls=("https://x.com/s",), selectors=SELETORES, **kw):
    return SearchRequest(platform="p", static_urls=list(urls), selectors=selectors, **kw)


def _na_vaga_vai_para(rota):
    """Navegador cuja pagina de vaga cai numa rota de desafio; a listagem e normal."""
    def atual(b):
        ultima = b.opened[-1] if b.opened else ""
        return f"https://x.com{rota}" if "/jobs/" in ultima else ultima
    return FakeBrowser(current_url=atual)


def test_contrato_do_padrao_e_do_marcador():
    assert CHALLENGE_URL_PATTERN == r"/(checkpoint|captcha|unusual-traffic|verify-phone)(/|\?|$)"
    assert CHALLENGE_MARKER == "[data-aihawk-challenge]"


@pytest.mark.parametrize("rota", ROTAS)
def test_desafio_na_url_da_vaga_para_o_lote(rota):
    browser = _na_vaga_vai_para(rota)
    service = AppService(browser)

    jobs = service.run(_request(strict_abort=True))

    assert service.last_abort_reason == AbortReason.CHALLENGE_URL.format(
        current=f"https://x.com{rota}", url="https://x.com/jobs/1/"
    )
    assert browser.opened == ["https://x.com/s", "https://x.com/jobs/1/"]
    assert [j.status for j in jobs] == [JobStatus.PENDING, JobStatus.PENDING]
    assert browser.clicks == []


@pytest.mark.parametrize("rota", ROTAS)
def test_desafio_na_listagem_nao_abre_a_segunda_url(rota):
    browser = FakeBrowser(current_url=lambda b: f"https://x.com{rota}")
    service = AppService(browser)

    jobs = service.run(_request(urls=("https://x.com/a", "https://x.com/b"), strict_abort=True))

    assert jobs == []
    assert browser.opened == ["https://x.com/a"]
    assert service.last_abort_reason is not None


def test_desafio_por_marcador_na_pagina_para_o_lote():
    def marcador(b, sel):
        return sel == CHALLENGE_MARKER and "/jobs/" in b.opened[-1]
    browser = FakeBrowser(exists=marcador)
    service = AppService(browser)

    service.run(_request(strict_abort=True))

    assert service.last_abort_reason == AbortReason.UNEXPECTED_SCREEN.format(
        indicator=CHALLENGE_MARKER, url="https://x.com/jobs/1/"
    )
    assert browser.opened == ["https://x.com/s", "https://x.com/jobs/1/"]


def test_url_de_desafio_vale_antes_do_marcador():
    browser = FakeBrowser(
        exists=lambda b, sel: sel == CHALLENGE_MARKER,
        current_url=lambda b: "https://x.com/captcha",
    )
    service = AppService(browser)

    service.run(_request(strict_abort=True))

    assert service.last_abort_reason.startswith("parada estrita: desafio na URL")


def test_sem_parada_estrita_desafio_e_ignorado():
    browser = FakeBrowser(current_url=lambda b: "https://x.com/captcha")
    service = AppService(browser)

    service.run(_request(strict_abort=False))

    assert service.last_abort_reason is None
    assert len(browser.opened) == 3


def test_so_url_basta_para_ligar_a_parada_estrita():
    so_url = {k: v for k, v in SELETORES.items() if k != "abort_indicator"}
    assert _request(selectors=so_url, strict_abort=True).strict_abort is True


def test_regex_invalida_falha_na_construcao():
    with pytest.raises(ValueError, match=r"^selectors\['abort_url_pattern'\] nao e uma regex valida: "):
        _request(selectors={**SELETORES, "abort_url_pattern": "(["})


@pytest.mark.parametrize(
    "url,casa",
    [
        ("https://x.com/CAPTCHA", True),
        ("https://x.com/checkpoint/challenge?x=1", True),
        ("https://x.com/verify-phone", True),
        ("https://x.com/unusual-traffic?a=b", True),
        ("https://x.com/captcha-tips", False),
        ("https://x.com/jobs/captchas", False),
        ("https://x.com/jobs/1/", False),
        ("", False),
        (None, False),
    ],
)
def test_padrao_de_desafio_casa_so_a_rota_inteira(url, casa):
    assert url_matches_pattern(url, CHALLENGE_URL_PATTERN) is casa


class _ServicoParado:
    last_abort_reason = "parada estrita: teste"

    def run(self, request):
        return []


def test_sumario_avisa_a_parada():
    resumo = AppController(_ServicoParado(), reports_dir=None).execute(_request())
    assert resumo.splitlines()[-1] == "Sessao interrompida:  parada estrita: teste"


def test_sumario_sem_parada_nao_traz_aviso():
    service = _ServicoParado()
    service.last_abort_reason = None
    resumo = AppController(service, reports_dir=None).execute(_request())
    assert "Sessao interrompida" not in resumo


def test_chaves_novas_do_perfil_sao_opcionais_conhecidas():
    assert {"abort_url_pattern", "submit_confirmation"} <= set(OPTIONAL_SELECTOR_KEYS)


def test_so_indicador_basta_para_ligar_a_parada_estrita():
    so_indicador = {k: v for k, v in SELETORES.items() if k != "abort_url_pattern"}
    assert _request(selectors=so_indicador, strict_abort=True).strict_abort is True


def test_url_ausente_nunca_casa_com_o_padrao():
    assert url_matches_pattern(None, ".") is False


@pytest.mark.parametrize("motivo", ["", 5, object()])
def test_sumario_ignora_motivo_vazio_ou_que_nao_e_texto(motivo):
    service = _ServicoParado()
    service.last_abort_reason = motivo
    resumo = AppController(service, reports_dir=None).execute(_request())
    assert "Sessao interrompida" not in resumo


def test_sumario_com_parada_mantem_o_resumo_e_acrescenta_o_aviso():
    resumo = AppController(_ServicoParado(), reports_dir=None).execute(_request())
    assert resumo.startswith("=" * 50 + "\nAIHawk - Resumo da sessao (p)")
    assert resumo.endswith("\nSessao interrompida:  parada estrita: teste")


def test_razoes_de_parada_tem_formato_fixo():
    assert AbortReason.MODAL_NOT_OPENED == "parada estrita: modal nao abriu em {url}"
    assert AbortReason.CHALLENGE_URL == "parada estrita: desafio na URL ({current}) em {url}"
    assert AbortReason.HISTORY_REQUIRED == (
        "envio real exige historico (cache) ligado; nada foi enviado em {url}"
    )


def test_parada_registra_o_motivo_no_log(caplog):
    browser = FakeBrowser(current_url=lambda b: "https://x.com/captcha")
    AppService(browser).run(_request(strict_abort=True))
    assert "Sessao interrompida: parada estrita: desafio na URL (https://x.com/captcha) em https://x.com/s." in caplog.text
