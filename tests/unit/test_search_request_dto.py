import pytest


def test_search_request_dto_creation_valid():
    """Valida contrato SearchRequest DTO com todos os atributos mapeados."""
    from src.application.dtos.search_request import SearchRequest

    dto = SearchRequest(
        platform="linkedin",
        static_urls=["https://www.linkedin.com/jobs/search/?keywords=python"],
        max_applications=15,
        selectors={
            "job_card": ".job-card-container",
            "apply_button": "button.jobs-apply-button",
            "next_button": "button[aria-label='Continue to next step']",
            "submit_button": "button[aria-label='Submit application']",
            "close_button": "button[aria-label='Dismiss']",
            "discard_button": "button[data-control-name='discard_application_confirm_btn']",
            "modal_container": ".jobs-easy-apply-modal",
        },
    )

    assert dto.platform == "linkedin"
    assert len(dto.static_urls) == 1
    assert dto.max_applications == 15
    assert dto.selectors["apply_button"] == "button.jobs-apply-button"


def test_search_request_empty_urls_or_platform_raises_error():
    """Valida regras de consistencia: platform obrigatorio e lista de URLs nao vazia."""
    from src.application.dtos.search_request import SearchRequest

    with pytest.raises(ValueError):
        SearchRequest(platform="", static_urls=["https://example.com"], max_applications=5, selectors={})

    with pytest.raises(ValueError):
        SearchRequest(platform="linkedin", static_urls=[], max_applications=5, selectors={})
