import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Protocol, Set

from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import Job, JobStatus

logger = logging.getLogger(__name__)

# Somente estes status valem a pena lembrar entre execucoes. ERROR e PENDING
# NUNCA entram no cache: precisam ser tentados de novo.
CACHEABLE_STATUSES = frozenset(
    {JobStatus.APPLIED, JobStatus.SKIPPED_COMPLEX, JobStatus.ALREADY_APPLIED}
)

# Trava de seguranca da maquina de estados do modal (passos Next/Review/Submit).
MAX_MODAL_STEPS = 15


class BrowserPort(Protocol):
    """Contrato das capacidades de navegador exigidas pela camada de aplicacao.

    A implementacao real fica em `src/infrastructure/browser_service.py` (Agy).
    Esta camada nao importa patchright nem conhece Page/Locator. Todos os
    metodos sao sincronos. `open_url` e `click` ja devem aplicar os atrasos
    humanizados; o AppService nao dorme por conta propria.
    """

    def open_url(self, url: str) -> None:
        """Navega para a URL e aguarda o carregamento basico (DOMContentLoaded)."""

    def scroll_container_to_end(self, container_selector: str) -> None:
        """Rola o container (overflow-y) ate o fim, repetidamente, ate o lazy
        loading parar de trazer itens novos."""

    def extract_job_cards(
        self,
        card_selector: str,
        title_selector: Optional[str] = None,
        company_selector: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Retorna um dict por card encontrado, com as chaves `url` (absoluta),
        `title` e `company`. Cards sem URL podem ser omitidos.

        `title_selector` e `company_selector` (chaves opcionais `job_card_title`
        e `job_card_company` do SearchRequest) dizem onde achar cada campo
        DENTRO do card; None = padrao da infraestrutura. O AppService passara
        os dois assim que o BrowserService aceitar os parametros."""

    def element_exists(self, selector: str) -> bool:
        """True se o seletor casa com ao menos um elemento visivel."""

    def click(self, selector: str) -> None:
        """Clica no elemento (com atraso humanizado). Levanta excecao em timeout."""

    def has_empty_required_inputs(self, container_selector: str) -> bool:
        """Inspetor DOM 3C: True se o container tem `input[required]`,
        `aria-required="true"`, `textarea` ou `select` obrigatorios vazios."""


class JobCache(Protocol):
    """Memoria de vagas ja processadas, para nunca reabrir o mesmo card."""

    def get(self, job: Job) -> Optional[JobStatus]:
        """Status lembrado para a vaga (identidade url + platform) ou None."""

    def put(self, job: Job) -> None:
        """Lembra o status da vaga. Ignora status fora de CACHEABLE_STATUSES."""


class JsonJobCache:
    """JobCache em arquivo JSON local: `{"version": 1, "jobs": {"<platform>|<url>": {...}}}`.

    Escrita atomica a cada `put`, para uma queda no meio da sessao nao perder
    o que ja foi feito. Arquivo ilegivel e preservado como `.corrupt-<hora>` e
    um cache novo e iniciado. Falha de escrita nunca derruba a sessao.
    """

    VERSION = 1

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Optional[Dict] = None

    @staticmethod
    def _key(job: Job) -> str:
        return f"{job.platform}|{job.url}"

    def _jobs(self) -> Dict[str, Dict]:
        if self._data is None:
            self._data = self._load()
        return self._data["jobs"]

    def _load(self) -> Dict:
        fresh = {"version": self.VERSION, "jobs": {}}
        if not os.path.exists(self._path):
            return fresh
        try:
            with open(self._path, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict) and isinstance(data.get("jobs"), dict):
                return data
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            pass
        backup = f"{self._path}.corrupt-{datetime.now():%H%M%S}"
        try:
            os.replace(self._path, backup)
            logger.warning("Cache ilegivel; preservado em %s", backup)
        except OSError:
            logger.exception("Cache ilegivel e nao foi possivel preserva-lo: %s", self._path)
        return fresh

    def get(self, job: Job) -> Optional[JobStatus]:
        record = self._jobs().get(self._key(job))
        if not isinstance(record, dict):
            return None
        try:
            status = JobStatus(record.get("status"))
        except ValueError:
            return None
        return status if status in CACHEABLE_STATUSES else None

    def put(self, job: Job) -> None:
        if job.status not in CACHEABLE_STATUSES:
            return
        self._jobs()[self._key(job)] = {
            "status": job.status.value,
            "title": job.title,
            "company": job.company,
            "at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        self._flush()

    def _flush(self) -> None:
        try:
            directory = os.path.dirname(self._path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            tmp_path = f"{self._path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._path)
        except OSError:
            logger.exception("Falha ao gravar o cache em %s (seguindo so em memoria).", self._path)


class AppService:
    """Caso de uso principal: percorrer as URLs estaticas, listar vagas e
    conduzir o modal de candidatura (Easy Apply seco, regra 3C).

    Agnostico de plataforma: todo seletor chega por `SearchRequest.selectors`.
    `cache` e opcional (None = desligado); quem monta a CLI decide ligar.
    """

    def __init__(self, browser: BrowserPort, cache: Optional[JobCache] = None) -> None:
        self._browser = browser
        self._cache = cache
        # Preenchido quando a sessao e interrompida de proposito (ex.: freio v0.7).
        self.last_abort_reason: Optional[str] = None

    # ------------------------------------------------------------------ API
    def run(self, request: SearchRequest) -> List[Job]:
        """Executa a sessao e devolve todas as vagas lidas, com status."""
        self.last_abort_reason = None
        jobs = self._collect_jobs(request)
        self._apply_cache(jobs)
        applied = 0
        consecutive_errors = 0

        for job in jobs:
            if job.from_cache:
                continue  # ja resolvida em execucao anterior: nao reabre o card
            if applied >= request.max_applications:
                logger.info("Limite de %d candidaturas atingido.", request.max_applications)
                break
            self._process_job(job, request)
            if self._cache is not None:
                self._cache.put(job)
            if job.status == JobStatus.APPLIED:
                applied += 1

            # v0.7: freio de erros consecutivos. As vagas restantes ficam PENDING.
            if job.status == JobStatus.ERROR:
                consecutive_errors += 1
                if consecutive_errors >= request.max_consecutive_errors:
                    self.last_abort_reason = (
                        f"{consecutive_errors} erros consecutivos "
                        f"(limite {request.max_consecutive_errors})"
                    )
                    logger.error("Sessao interrompida: %s.", self.last_abort_reason)
                    break
            else:
                consecutive_errors = 0

        return jobs

    # ---------------------------------------------------------- v0.6: cache
    def _apply_cache(self, jobs: List[Job]) -> None:
        """Marca as vagas ja resolvidas antes. Candidatura anterior bem-sucedida
        vira ALREADY_APPLIED (nao foi esta execucao que aplicou)."""
        if self._cache is None:
            return
        for job in jobs:
            remembered = self._cache.get(job)
            if remembered is None:
                continue
            job.status = (
                JobStatus.ALREADY_APPLIED if remembered is JobStatus.APPLIED else remembered
            )
            job.from_cache = True

    # ------------------------------------------------- v0.3: listagem de vagas
    def _collect_jobs(self, request: SearchRequest) -> List[Job]:
        """Abre cada URL estatica, rola o painel e extrai vagas unicas por
        (url, platform). Falha em uma URL nao derruba as demais."""
        sel = request.selectors
        seen: Set[Job] = set()
        jobs: List[Job] = []

        for page_url in request.static_urls:
            try:
                self._browser.open_url(page_url)
                self._browser.scroll_container_to_end(sel["jobs_list_container"])
                cards = self._browser.extract_job_cards(sel["job_card"])
            except Exception:
                logger.exception("Falha ao listar vagas em %s; seguindo para a proxima URL.", page_url)
                continue

            for card in cards:
                url = Job.canonicalize_url(card.get("url") or "")
                if not url:
                    continue
                job = Job(
                    url=url,
                    platform=request.platform,
                    title=card.get("title", ""),
                    company=card.get("company", ""),
                )
                if job in seen:
                    continue
                seen.add(job)
                jobs.append(job)

        return jobs

    # ------------------------------------- v0.4/v0.5: modal e regra 3C
    def _process_job(self, job: Job, request: SearchRequest) -> None:
        """Blindagem por card: qualquer excecao marca o Job como ERROR e o
        loop principal continua."""
        sel = request.selectors
        try:
            self._browser.open_url(job.url)

            if not self._browser.element_exists(sel["apply_button"]):
                # Sem Easy Apply (candidatura externa ou ja enviada): fora do
                # escopo da v1.0. Decisao a validar pelo QA/Nicolas.
                job.status = JobStatus.SKIPPED_COMPLEX
                return

            self._browser.click(sel["apply_button"])
            job.status = self._run_modal(sel)
        except Exception:
            logger.exception("Erro ao processar %s", job.url)
            job.status = JobStatus.ERROR
            self._discard_quietly(sel)

    def _run_modal(self, sel: Dict[str, str]) -> JobStatus:
        """Avanco linear do modal. Regra 3C: inspeciona o DOM ANTES de qualquer
        clique de avanco (Next, Review ou Submit)."""
        modal = sel["modal_container"]

        for _ in range(MAX_MODAL_STEPS):
            if self._browser.has_empty_required_inputs(modal):
                self._discard(sel)
                return JobStatus.SKIPPED_COMPLEX

            if self._browser.element_exists(sel["submit_button"]):
                self._browser.click(sel["submit_button"])
                return JobStatus.APPLIED

            # `review_button` e opcional: nem toda plataforma tem esse passo.
            advance = next(
                (
                    sel[key]
                    for key in ("next_button", "review_button")
                    if key in sel and self._browser.element_exists(sel[key])
                ),
                None,
            )
            if advance is None:
                logger.warning("Passo do modal sem botao de avanco reconhecido; descartando.")
                self._discard(sel)
                return JobStatus.ERROR

            self._browser.click(advance)

        logger.warning("Limite de %d passos do modal excedido; descartando.", MAX_MODAL_STEPS)
        self._discard(sel)
        return JobStatus.ERROR

    def _discard(self, sel: Dict[str, str]) -> None:
        """Sequencia segura: Fechar -> Descartar (se a confirmacao aparecer)."""
        self._browser.click(sel["close_button"])
        if self._browser.element_exists(sel["discard_button"]):
            self._browser.click(sel["discard_button"])

    def _discard_quietly(self, sel: Dict[str, str]) -> None:
        """Limpeza best-effort apos erro: nunca propaga excecao."""
        try:
            if self._browser.element_exists(sel["modal_container"]):
                self._discard(sel)
        except Exception:
            logger.exception("Falha ao descartar o modal apos erro.")
