import os
import shutil
import subprocess
import time
import urllib.request

import pytest

from src.infrastructure.browser_service import BrowserService

CLONE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "linkedin_clone")
)
CLONE_URL = os.getenv("CLONE_URL", "http://localhost:3000")


def _is_url_up(url: str, timeout: float = 2.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


@pytest.fixture(scope="module")
def hostile_clone_server():
    """Garante que o clone SPA hostil em Next.js esteja rodando em http://localhost:3000."""
    if _is_url_up(CLONE_URL):
        yield CLONE_URL
        return

    proc = subprocess.Popen(
        ["npx", "next", "start", "-p", "3000"],
        cwd=CLONE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.time() + 20.0
        while time.time() < deadline:
            if _is_url_up(CLONE_URL):
                break
            time.sleep(0.3)
        else:
            pytest.skip(f"Nao foi possivel subir o clone Next.js em {CLONE_URL}")

        yield CLONE_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


@pytest.fixture
def hostile_browser():
    """Sessao real do Chromium (Patchright) isolada para testes contra o clone hostil."""
    session_dir = os.path.abspath("./tests_scratch/real_hostile_session")
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir, ignore_errors=True)

    headless = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    service = BrowserService(
        platform="linkedin_clone_test",
        headless=headless,
        channel="chromium",
        session_root_dir=session_dir,
    )
    service.start_session()
    yield service
    service.close()
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir, ignore_errors=True)


@pytest.fixture
def open_sea_browser():
    """Chromium real (Patchright) isolado para a validacao em mar aberto (somente leitura, sem login)."""
    session_dir = os.path.abspath("./tests_scratch/open_sea_session")
    shutil.rmtree(session_dir, ignore_errors=True)
    service = BrowserService(
        platform="open_sea",
        headless=os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes"),
        channel="chromium",
        session_root_dir=session_dir,
    )
    service.start_session()
    yield service
    service.close()
    shutil.rmtree(session_dir, ignore_errors=True)
