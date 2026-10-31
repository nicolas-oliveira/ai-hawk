from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit


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

        Remove query string (refId, trackingId, utm_*...), fragmento (#...) e
        garante a barra final. Entrada vazia devolve '' para o Job rejeitar.
        """
        if not raw_url or not raw_url.strip():
            return ""
        parts = urlsplit(raw_url.strip())
        path = parts.path if parts.path.endswith("/") else parts.path + "/"
        return urlunsplit((parts.scheme, parts.netloc, path, "", ""))

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
