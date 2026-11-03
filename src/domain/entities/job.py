from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import re
from typing import Dict, FrozenSet, Optional
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
    # Shadow Mode: percorreu o modal ate o Submit, mas NAO enviou (dry-run).
    SIMULATED = "SIMULATED"
    # Intencao gravada ANTES do clique de envio, ainda sem resultado.
    SUBMITTING = "SUBMITTING"
    # Envio sem sucesso confirmado: um humano confere. Nunca vira ERROR nem e repetido.
    MANUAL_REVIEW = "MANUAL_REVIEW"


class InvalidTransition(ValueError):
    """Mudanca de status que a maquina de estados do Job nao permite."""


class ReviewReason(StrEnum):
    """Por que uma vaga foi para revisao manual (valor unico, nunca string solta)."""

    CLICK_FAILED = "clique de envio falhou ou estourou o tempo"
    MODAL_STILL_OPEN = "modal ainda aberto apos o envio"
    CONFIRMATION_MISSING = "confirmacao de envio ausente"
    INTERRUPTED_BEFORE_RESULT = "execucao interrompida antes do resultado do envio"
    ALREADY_IN_REVIEW = "ja estava em revisao manual de uma execucao anterior"


# Quem pode ir para quem. Fora desta tabela a transicao e invalida.
_ALLOWED_TRANSITIONS: Dict[JobStatus, FrozenSet[JobStatus]] = {
    JobStatus.PENDING: frozenset(
        {
            JobStatus.SUBMITTING,
            JobStatus.SKIPPED_COMPLEX,
            JobStatus.ERROR,
            JobStatus.SIMULATED,
            JobStatus.ALREADY_APPLIED,
        }
    ),
    JobStatus.SUBMITTING: frozenset({JobStatus.APPLIED, JobStatus.MANUAL_REVIEW}),
}

# O que a memoria de execucoes anteriores pode devolver, e em que vira agora.
# Envio gravado (SUBMITTING) sem resultado nunca e repetido: vai para revisao.
_FROM_HISTORY: Dict[JobStatus, JobStatus] = {
    JobStatus.APPLIED: JobStatus.ALREADY_APPLIED,
    JobStatus.ALREADY_APPLIED: JobStatus.ALREADY_APPLIED,
    JobStatus.SKIPPED_COMPLEX: JobStatus.SKIPPED_COMPLEX,
    JobStatus.MANUAL_REVIEW: JobStatus.MANUAL_REVIEW,
    JobStatus.SUBMITTING: JobStatus.MANUAL_REVIEW,
}


@dataclass(frozen=True)
class SubmissionEvidence:
    """O que se observou depois do clique de envio.

    Regra do dominio: so sucesso CONFIRMADO conta como candidatura enviada.
    Sucesso se e somente se o clique foi concluido E a confirmacao foi vista,
    qualquer que seja o estado do dialogo.
    """

    click_completed: bool
    confirmation_seen: bool = False
    modal_still_open: bool = False

    @property
    def review_reason(self) -> Optional[ReviewReason]:
        """Primeira condicao que falhou, ou None quando o envio esta confirmado."""
        if not self.click_completed:
            return ReviewReason.CLICK_FAILED
        if self.confirmation_seen:
            return None
        if self.modal_still_open:
            return ReviewReason.MODAL_STILL_OPEN
        return ReviewReason.CONFIRMATION_MISSING


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
    # Preenchido so quando o status e MANUAL_REVIEW.
    review_reason: Optional[ReviewReason] = None

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

    # ------------------------------------------------ transicoes com intencao
    def _transition(self, target: JobStatus) -> None:
        if target not in _ALLOWED_TRANSITIONS.get(self.status, frozenset()):
            raise InvalidTransition(f"{self.status.value} -> {target.value} nao e permitido.")
        self.status = target

    def mark_submitting(self) -> None:
        self._transition(JobStatus.SUBMITTING)

    def mark_applied(self) -> None:
        self._transition(JobStatus.APPLIED)

    def mark_manual_review(self, reason: ReviewReason) -> None:
        self._transition(JobStatus.MANUAL_REVIEW)
        self.review_reason = reason

    def mark_simulated(self) -> None:
        self._transition(JobStatus.SIMULATED)

    def mark_skipped_complex(self) -> None:
        self._transition(JobStatus.SKIPPED_COMPLEX)

    def mark_error(self) -> None:
        self._transition(JobStatus.ERROR)

    def settle_submission(self, evidence: SubmissionEvidence) -> None:
        """Fecha um envio SUBMITTING: APPLIED so com sucesso confirmado; qualquer
        outro desfecho vai para revisao manual (nunca ERROR, nunca nova tentativa)."""
        reason = evidence.review_reason
        if reason is None:
            self.mark_applied()
        else:
            self.mark_manual_review(reason)

    def restore_from_history(self, remembered: JobStatus) -> None:
        """Aplica o que execucoes anteriores lembram desta vaga (so a partir de PENDING)."""
        target = _FROM_HISTORY.get(remembered)
        if self.status is not JobStatus.PENDING or target is None:
            raise InvalidTransition(f"{self.status.value} nao restaura {remembered.value}.")
        self.status = target
        self.from_cache = True
        if target is JobStatus.MANUAL_REVIEW:
            self.review_reason = (
                ReviewReason.INTERRUPTED_BEFORE_RESULT
                if remembered is JobStatus.SUBMITTING
                else ReviewReason.ALREADY_IN_REVIEW
            )

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
