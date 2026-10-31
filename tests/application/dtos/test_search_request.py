import pytest


def test_search_request_dto_valid(valid_search_request_payload):
    """Valida criacao e estrutura do SearchRequest DTO com seletores e URLs."""
    from src.application.dtos.search_request import SearchRequest

    dto = SearchRequest(**valid_search_request_payload)

    assert dto.platform == "linkedin"
    assert len(dto.static_urls) == 1
    assert dto.max_applications == 20
    assert "apply_button" in dto.selectors
    assert "jobs_list_container" in dto.selectors


def test_search_request_dto_default_max_applications(valid_search_request_payload):
    """Valida default de max_applications = 10 quando omitido."""
    from src.application.dtos.search_request import SearchRequest

    payload = dict(valid_search_request_payload)
    del payload["max_applications"]

    dto = SearchRequest(**payload)
    assert dto.max_applications == 10


def test_search_request_dto_invalid_max_applications_raises_error(valid_search_request_payload):
    """Valida que max_applications <= 0 lanca ValueError."""
    from src.application.dtos.search_request import SearchRequest

    payload = dict(valid_search_request_payload)
    payload["max_applications"] = 0

    with pytest.raises(ValueError):
        SearchRequest(**payload)

    payload["max_applications"] = -5
    with pytest.raises(ValueError):
        SearchRequest(**payload)


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


def test_search_request_dto_missing_mandatory_selectors_raises_error(valid_search_request_payload):
    """
    Step A: Valida que selectors deve conter todas as chaves operacionais obrigatorias
    para suportar o Loop Easy Apply Seco da v0.5.
    """
    from src.application.dtos.search_request import SearchRequest

    mandatory_keys = [
        "jobs_list_container",
        "job_card",
        "apply_button",
        "next_button",
        "submit_button",
        "close_button",
        "discard_button",
        "modal_container",
    ]

    for key in mandatory_keys:
        incomplete_payload = dict(valid_search_request_payload)
        incomplete_selectors = dict(valid_search_request_payload["selectors"])
        del incomplete_selectors[key]
        incomplete_payload["selectors"] = incomplete_selectors

        with pytest.raises(ValueError, match=f".*{key}.*"):
            SearchRequest(**incomplete_payload)


def test_search_request_dto_linkedin_default_selectors_has_all_keys():
    """Valida que LINKEDIN_DEFAULT_SELECTORS exportado contem todas as 8 chaves obrigatorias."""
    from src.application.dtos.search_request import LINKEDIN_DEFAULT_SELECTORS

    expected_keys = {
        "jobs_list_container",
        "job_card",
        "apply_button",
        "next_button",
        "submit_button",
        "close_button",
        "discard_button",
        "modal_container",
    }
    assert expected_keys.issubset(LINKEDIN_DEFAULT_SELECTORS.keys())


def test_build_linkedin_search_url_minimal():
    """Valida geracao de URL canonica com apenas palavras-chave e default de Easy Apply."""
    from src.application.dtos.search_request import build_linkedin_search_url

    url = build_linkedin_search_url("python developer")
    assert url == "https://www.linkedin.com/jobs/search/?keywords=python%20developer&f_AL=true"


def test_build_linkedin_search_url_full_filters():
    """Valida geracao de URL canonica com todos os filtros pre-codificados."""
    from src.application.dtos.search_request import build_linkedin_search_url

    url = build_linkedin_search_url(
        "python developer",
        location="Sao Paulo, Brazil",
        workplace="remote",
        posted_within="24h",
        easy_apply=True,
    )
    expected = (
        "https://www.linkedin.com/jobs/search/?"
        "keywords=python%20developer&location=Sao%20Paulo%2C%20Brazil&f_AL=true&f_WT=2&f_TPR=r86400"
    )
    assert url == expected


def test_build_linkedin_search_url_without_easy_apply():
    """Valida omissao do parametro f_AL quando easy_apply=False."""
    from src.application.dtos.search_request import build_linkedin_search_url

    url = build_linkedin_search_url("rust engineer", easy_apply=False)
    assert "f_AL=true" not in url
    assert url == "https://www.linkedin.com/jobs/search/?keywords=rust%20engineer"


def test_build_linkedin_search_url_empty_keywords_raises():
    """Valida que keywords vazio ou espacos lanca ValueError."""
    from src.application.dtos.search_request import build_linkedin_search_url

    with pytest.raises(ValueError, match="keywords nao pode ser vazio"):
        build_linkedin_search_url("")

    with pytest.raises(ValueError, match="keywords nao pode ser vazio"):
        build_linkedin_search_url("   ")


def test_build_linkedin_search_url_invalid_workplace_raises():
    """Valida que workplace invalido lanca ValueError."""
    from src.application.dtos.search_request import build_linkedin_search_url

    with pytest.raises(ValueError, match="workplace invalido"):
        build_linkedin_search_url("python", workplace="mars_office")


def test_build_linkedin_search_url_invalid_posted_within_raises():
    """Valida que posted_within invalido lanca ValueError."""
    from src.application.dtos.search_request import build_linkedin_search_url

    with pytest.raises(ValueError, match="posted_within invalido"):
        build_linkedin_search_url("python", posted_within="last_century")

