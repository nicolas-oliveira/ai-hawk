from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import re
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

# Parametros de query que IDENTIFICAM a vaga quando o path nao traz o ID
# (ex.: boards.greenhouse.io/empresa/jobs?gh_jid=123). Sem diferenciar caixa.
JOB_ID_QUERY_PARAMS = frozenset({"id", "jobid", "gh_jid"})
_ID_IN_PATH = re.compile(r"\d{6,}")


class JobStatus(StrEnum):
    """Maquina de estados de uma vaga.

    StrEnum permite comparar com strings (`job.status == "PENDING"`) e
    persistir o valor diretamente em cache/JSON.
    """

    PENDING = "PENDING"
    APPLIED = "APPLIED"
    SKIPPED_COMPLEX = "SKIPPED_COMPLEX"
    ALREADY_APPLIED = "ALREADY_APPLIED"
    ERROR = "ERROR"


@dataclass(eq=False)
class Job:
    """Entidade pura de uma vaga (sem dependencia de navegador ou plataforma).

    A identidade de um Job e o par (url, platform), nunca o conteudo mutavel
    (title, company, status, timestamp). Isso permite verificar o cache local
    antes de abrir qualquer card de vaga.
    """

    url: str
    platform: str
    title: str
    company: str
    status: JobStatus = JobStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    # True quando o status veio do cache local (a vaga nem foi aberta nesta execucao).
    from_cache: bool = False

    @staticmethod
    def canonicalize_url(raw_url: str) -> str:
        """Higieniza a URL de uma vaga para servir de identidade estavel.

        Sempre remove o fragmento (#...) e garante a barra final. A query string
        (refId, trackingId, utm_*...) tambem e removida, COM UMA EXCECAO: se o
        path NAO traz o ID da vaga (nenhuma sequencia de 6+ digitos, como em
        /jobs/view/4012345678/), os parametros de identificacao da whitelist
        JOB_ID_QUERY_PARAMS (id, jobId, gh_jid) sao preservados; o resto cai.
        Entrada vazia devolve '' para o Job rejeitar.

        LIMITE CONHECIDO (Fase 2): plataformas que identificam a vaga por outro
        parametro de query exigem ampliar JOB_ID_QUERY_PARAMS; enquanto isso,
        vagas diferentes dessa plataforma colapsariam na mesma URL canonica.
        """
        if not raw_url or not raw_url.strip():
            return ""
        parts = urlsplit(raw_url.strip())
        path = parts.path if parts.path.endswith("/") else parts.path + "/"
        query = ""
        if not _ID_IN_PATH.search(parts.path):
            kept = [
                (key, value)
                for key, value in parse_qsl(parts.query)
                if key.lower() in JOB_ID_QUERY_PARAMS and value
            ]
            query = urlencode(kept, quote_via=quote)
        return urlunsplit((parts.scheme, parts.netloc, path, query, ""))

    def __post_init__(self) -> None:
        if not self.url or not self.url.strip():
            raise ValueError("Job.url nao pode ser vazio.")
        if not self.platform or not self.platform.strip():
            raise ValueError("Job.platform nao pode ser vazio.")

    def __setattr__(self, name: str, value) -> None:
        # Converte e valida o status na criacao e em toda atribuicao posterior
        # (ex.: service marcando a vaga como APPLIED). Valor invalido levanta
        # ValueError.
        if name == "status":
            value = JobStatus(value)
        super().__setattr__(name, value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return (self.url, self.platform) == (other.url, other.platform)

    def __hash__(self) -> int:
        return hash((self.url, self.platform))
