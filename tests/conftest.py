import pytest
import os
import shutil
from typing import Dict, Any


@pytest.fixture
def temp_session_dir():
    """Diretorio temporario isolado para testes reais de sessao de infraestrutura."""
    test_dir = os.path.abspath("./tests_scratch/session_test")
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def valid_job_payload() -> Dict[str, Any]:
    """Payload de exemplo valido para criacao de entidade Job."""
    from datetime import datetime

    return {
        "url": "https://www.linkedin.com/jobs/view/123456789/",
        "platform": "linkedin",
        "title": "Senior Python Engineer",
        "company": "Tech Global Inc",
        "status": "PENDING",
        "timestamp": datetime(2026, 10, 31, 12, 0, 0),
    }


@pytest.fixture
def valid_search_request_payload() -> Dict[str, Any]:
    """Payload de exemplo valido para criacao de DTO SearchRequest."""
    return {
        "platform": "linkedin",
        "static_urls": [
            "https://www.linkedin.com/jobs/search/?keywords=python"
        ],
        "max_applications": 20,
        "selectors": {
            "job_card": ".job-card-container",
            "apply_button": "button.jobs-apply-button",
            "next_button": "button[aria-label='Continue to next step']",
            "submit_button": "button[aria-label='Submit application']",
            "close_button": "button[aria-label='Dismiss']",
            "discard_button": "button[data-control-name='discard_application_confirm_btn']",
            "modal_container": ".jobs-easy-apply-modal",
        },
    }


@pytest.fixture
def mock_browser_service(mocker):
    """
    Mock 100% desacoplado do BrowserService para os testes da aplicacao (Claude).
    Permite testar controllers e services em milissegundos sem abrir o Chromium.
    """
    mock = mocker.MagicMock()
    mock.platform = "mock_platform"
    mock.headless = True
    mock.channel = "chromium"
    mock.user_data_dir = "/tmp/mock_session"

    mock_page = mocker.MagicMock()
    mock_page.title.return_value = "Mock Page Title"
    mock_page.evaluate.return_value = "mock_val"
    mock_page.goto.return_value = None

    mock.get_page.return_value = mock_page
    mock.start_session.return_value = mocker.MagicMock()
    mock.close.return_value = None

    return mock
