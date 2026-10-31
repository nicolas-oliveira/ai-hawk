import pytest


def test_search_request_dto_valid(valid_search_request_payload):
    """Valida criacao e estrutura do SearchRequest DTO com seletores e URLs."""
    from src.application.dtos.search_request import SearchRequest

    dto = SearchRequest(**valid_search_request_payload)

    assert dto.platform == "linkedin"
    assert len(dto.static_urls) == 1
    assert dto.max_applications == 20
    assert "apply_button" in dto.selectors


def test_search_request_dto_empty_platform_raises_error(valid_search_request_payload):
    """Valida que platform vazio lanca ValueError."""
    from src.application.dtos.search_request import SearchRequest

    payload = dict(valid_search_request_payload)
    payload["platform"] = ""

    with pytest.raises(ValueError):
        SearchRequest(**payload)


def test_search_request_dto_empty_urls_raises_error(valid_search_request_payload):
    """Valida que lista de URLs estaticas vazia lanca ValueError."""
    from src.application.dtos.search_request import SearchRequest

    payload = dict(valid_search_request_payload)
    payload["static_urls"] = []

    with pytest.raises(ValueError):
        SearchRequest(**payload)
