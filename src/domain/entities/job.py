from dataclasses import dataclass
from datetime import datetime

VALID_STATUSES = frozenset(
    {"PENDING", "APPLIED", "SKIPPED_COMPLEX", "ALREADY_APPLIED", "ERROR"}
)


@dataclass(eq=False)
class Job:
    """Entidade pura de uma vaga.

    A identidade de um Job e o par (url, platform), nunca o conteudo mutavel
    (title, company, status, timestamp). Isso permite verificar o cache local
    antes de abrir qualquer card de vaga.
    """

    url: str
    platform: str
    title: str
    company: str
    status: str
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.url or not self.url.strip():
            raise ValueError("Job.url nao pode ser vazio.")
        if not self.platform or not self.platform.strip():
            raise ValueError("Job.platform nao pode ser vazio.")

    def __setattr__(self, name: str, value) -> None:
        # Garante o invariante do status tambem em atribuicoes posteriores
        # (ex.: service marcando a vaga como APPLIED ou SKIPPED_COMPLEX).
        if name == "status" and value not in VALID_STATUSES:
            raise ValueError(
                f"Status invalido: {value!r}. Permitidos: {sorted(VALID_STATUSES)}."
            )
        super().__setattr__(name, value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return (self.url, self.platform) == (other.url, other.platform)

    def __hash__(self) -> int:
        return hash((self.url, self.platform))
