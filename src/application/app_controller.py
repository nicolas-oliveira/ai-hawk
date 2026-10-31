from collections import Counter
from typing import List

from src.application.app_service import AppService
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import Job, JobStatus


class AppController:
    """Porta de entrada da CLI: valida o SearchRequest, dispara o AppService e
    formata o sumario estatistico da sessao. Sem HTTP, sem framework."""

    def __init__(self, app_service: AppService) -> None:
        self._service = app_service

    def execute(self, request: SearchRequest) -> str:
        self._validate(request)
        jobs = self._service.run(request)
        return self.format_summary(jobs, request)

    # ------------------------------------------------------------ validacao
    @staticmethod
    def _validate(request: SearchRequest) -> None:
        if not isinstance(request, SearchRequest):
            raise TypeError("execute() espera uma instancia de SearchRequest.")
        # Demais invariantes (max_applications, seletores obrigatorios) sao
        # garantidos pelo proprio SearchRequest na construcao.

    # -------------------------------------------------------------- sumario
    @staticmethod
    def format_summary(jobs: List[Job], request: SearchRequest) -> str:
        counts = Counter(job.status for job in jobs)
        lines = [
            "=" * 50,
            f"AIHawk - Resumo da sessao ({request.platform})",
            "=" * 50,
            f"URLs de busca:        {len(request.static_urls)}",
            f"Vagas encontradas:    {len(jobs)}",
            f"Candidaturas:         {counts[JobStatus.APPLIED]} de {request.max_applications} (limite)",
        ]
        for status in JobStatus:
            if status is JobStatus.APPLIED:
                continue
            lines.append(f"{status.value:<21} {counts[status]}")
        return "\n".join(lines)
