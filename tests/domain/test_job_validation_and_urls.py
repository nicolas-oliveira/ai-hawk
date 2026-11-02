import pytest

from src.domain.entities import job as job_module
from src.domain.entities.job import Job


def test_whitelist_de_ids_exata():
    assert job_module.JOB_ID_QUERY_PARAMS == frozenset({"id", "jobid", "gh_jid"})


@pytest.mark.parametrize("campo,msg", [("url", "Job.url nao pode ser vazio."),
                                       ("platform", "Job.platform nao pode ser vazio.")])
@pytest.mark.parametrize("vazio", ["", "   "])
def test_campos_obrigatorios_vazios(campo, msg, vazio):
    dados = {"url": "https://x.com/1", "platform": "p", "title": "t", "company": "c"}
    dados[campo] = vazio
    with pytest.raises(ValueError) as exc:
        Job(**dados)
    assert str(exc.value) == msg


@pytest.mark.parametrize("entrada", ["", "   ", None])
def test_canonicalize_vazio_devolve_vazio(entrada):
    assert Job.canonicalize_url(entrada) == ""


def test_canonicalize_remove_query_quando_path_tem_id_de_6_digitos():
    assert Job.canonicalize_url("https://x.com/jobs/view/123456?id=9&utm=1#f") == "https://x.com/jobs/view/123456/"


def test_canonicalize_com_5_digitos_ainda_olha_a_query():
    # 5 digitos NAO bastam para identificar a vaga: a whitelist vale.
    assert Job.canonicalize_url("https://x.com/jobs/12345?id=9&utm=1") == "https://x.com/jobs/12345/?id=9"


def test_canonicalize_preserva_so_whitelist_e_ignora_valor_vazio():
    url = "https://x.com/jobs?gh_jid=77&utm=1&JobId=5&id="
    assert Job.canonicalize_url(url) == "https://x.com/jobs/?gh_jid=77&JobId=5"


def test_canonicalize_codifica_espacos_com_percent():
    assert Job.canonicalize_url("https://x.com/jobs?id=a%20b") == "https://x.com/jobs/?id=a%20b"


def test_identidade_ignora_conteudo_mutavel():
    a = Job(url="https://x.com/1", platform="p", title="a", company="a")
    b = Job(url="https://x.com/1", platform="p", title="b", company="b")
    assert a == b and hash(a) == hash(b)
    assert a != Job(url="https://x.com/1", platform="q", title="a", company="a")
