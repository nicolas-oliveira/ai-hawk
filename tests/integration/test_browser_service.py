import pytest
import os
import shutil
from src.infrastructure.browser_service import BrowserService


@pytest.fixture
def temp_session_dir():
    test_dir = os.path.abspath("./tests_scratch/session_test")
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, ignore_errors=True)


def test_browser_service_initialization(temp_session_dir):
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
    service = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )

    # Sessao 1: Gravar dado no localStorage
    context = service.start_session()
    page = service.get_page()
    page.goto("https://example.com", wait_until="domcontentloaded")
    page.evaluate("localStorage.setItem('session_marker', 'agy_v0.1_persistent')")
    service.close()

    # Sessao 2: Ler dado no mesmo perfil
    service2 = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    context2 = service2.start_session()
    page2 = service2.get_page()
    page2.goto("https://example.com", wait_until="domcontentloaded")
    val = page2.evaluate("localStorage.getItem('session_marker')")
    service2.close()

    assert val == "agy_v0.1_persistent"


def test_browser_service_platform_isolation(temp_session_dir):
    service_a = BrowserService(platform="platform_a", session_root_dir=temp_session_dir)
    service_b = BrowserService(platform="platform_b", session_root_dir=temp_session_dir)

    assert service_a.user_data_dir != service_b.user_data_dir
    assert service_a.user_data_dir.endswith("platform_a")
    assert service_b.user_data_dir.endswith("platform_b")
