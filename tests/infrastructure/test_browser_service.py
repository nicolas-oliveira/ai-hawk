import pytest
import os
import subprocess
import sys
from src.infrastructure.browser_service import BrowserService


def test_browser_service_initialization(temp_session_dir):
    """Valida configuracoes padrao de inicializacao do BrowserService."""
    service = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    assert service.platform == "linkedin"
    assert service.headless is True
    assert service.channel == "chromium"
    assert service.user_data_dir == os.path.join(temp_session_dir, "linkedin")


def test_browser_service_session_persistence(temp_session_dir):
    """Valida persistencia sincrona real entre sessoes consecutivas."""
    service1 = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )

    # Sessao 1: Gravar dado no localStorage
    service1.start_session()
    page1 = service1.get_page()
    page1.goto("https://example.com", wait_until="domcontentloaded")
    page1.evaluate("localStorage.setItem('session_marker', 'agy_v0.1_shift_left')")
    service1.close()

    # Sessao 2: Ler dado no mesmo perfil
    service2 = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service2.start_session()
    page2 = service2.get_page()
    page2.goto("https://example.com", wait_until="domcontentloaded")
    val = page2.evaluate("localStorage.getItem('session_marker')")
    service2.close()

    assert val == "agy_v0.1_shift_left"


def test_browser_service_platform_isolation(temp_session_dir):
    """Valida isolamento de diretorios por plataforma (Decisao 2)."""
    service_a = BrowserService(platform="platform_a", session_root_dir=temp_session_dir)
    service_b = BrowserService(platform="platform_b", session_root_dir=temp_session_dir)

    assert service_a.user_data_dir != service_b.user_data_dir
    assert service_a.user_data_dir.endswith("platform_a")
    assert service_b.user_data_dir.endswith("platform_b")


def test_main_cli_execution():
    """Valida teste de fumaca do CLI sincrono python -m src.main."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "HEADLESS": "true",
            "BROWSER_CHANNEL": "chromium",
            "SESSION_ROOT_DIR": "./tests_scratch/cli_sessions",
        },
    )
    assert result.returncode == 0
    assert "AIHawk v0.1 - Inicializando Infraestrutura Stealth (Sync)" in result.stdout
    assert "Sessao encerrada com sucesso." in result.stdout
