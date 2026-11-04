import pytest
from src.infrastructure.browser_service import BrowserService


def test_real_identity_guard_allows_local_clone(tmp_path):
    """
    Passo A1 (Teste Real): Sessao real com alvo local (127.0.0.1) passa normalmente.
    """
    service = BrowserService(
        platform="test_id_local",
        headless=True,
        session_root_dir=str(tmp_path),
    )
    service.start_session()
    try:
        meta = service.verify_runtime_identity(target_url="http://127.0.0.1:3000/jobs")
        assert meta["engine"] in ("chromium", "firefox")
        assert meta["webdriver"] is False
    finally:
        service.close()


def test_real_identity_guard_blocks_external_target_when_headless_real_or_forbidden(tmp_path, monkeypatch):
    """
    Passo A1 (Ajuste b): Sessao real tentando navegar para alvo externo com modo nao-xvfb
    ou com violacao e bloqueada com RuntimeError antes de qualquer requisicao de rede.
    """
    service = BrowserService(
        platform="test_id_block",
        headless=True,
        session_root_dir=str(tmp_path),
    )
    service.start_session()
    try:
        # Simula violacao de modo para provar que a trava nao deixa passar
        monkeypatch.setattr(service, "get_runtime_metadata", lambda: {
            "engine": service.engine,
            "effective_mode": "headless-real",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36",
            "webdriver": False,
            "plugins_length": 5,
        })
        with pytest.raises(RuntimeError, match="Trava de Identidade violada: Alvo externo exige janela real"):
            service.navigate("https://www.linkedin.com/jobs/view/999/")
    finally:
        service.close()
