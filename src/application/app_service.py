import logging
from typing import Dict, List, Protocol, Set

from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import Job, JobStatus

logger = logging.getLogger(__name__)

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

    def extract_job_cards(self, card_selector: str) -> List[Dict[str, str]]:
        """Retorna um dict por card encontrado, com as chaves `url` (absoluta),
        `title` e `company`. Cards sem URL podem ser omitidos."""

    def element_exists(self, selector: str) -> bool:
        """True se o seletor casa com ao menos um elemento visivel."""

    def click(self, selector: str) -> None:
        """Clica no elemento (com atraso humanizado). Levanta excecao em timeout."""

    def has_empty_required_inputs(self, container_selector: str) -> bool:
        """Inspetor DOM 3C: True se o container tem `input[required]`,
        `aria-required="true"`, `textarea` ou `select` obrigatorios vazios."""


class AppService:
    """Caso de uso principal: percorrer as URLs estaticas, listar vagas e
    conduzir o modal de candidatura (Easy Apply seco, regra 3C).

    Agnostico de plataforma: todo seletor chega por `SearchRequest.selectors`.
    """

    def __init__(self, browser: BrowserPort) -> None:
        self._browser = browser

    # ------------------------------------------------------------------ API
    def run(self, request: SearchRequest) -> List[Job]:
        """Executa a sessao e devolve todas as vagas processadas, com status."""
        jobs = self._collect_jobs(request)
        applied = 0

        for job in jobs:
            if applied >= request.max_applications:
                logger.info("Limite de %d candidaturas atingido.", request.max_applications)
                break
            self._process_job(job, request)
            if job.status == JobStatus.APPLIED:
                applied += 1

        return jobs

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
