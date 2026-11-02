import os
import shutil

import pytest

from src.infrastructure.browser_service import BrowserService


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
