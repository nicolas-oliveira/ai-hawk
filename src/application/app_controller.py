import json
import logging
import os
from collections import Counter
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from src.application.app_service import AppService
from src.application.dtos.search_request import SearchRequest
from src.domain.entities.job import Job, JobStatus

logger = logging.getLogger(__name__)

DEFAULT_REPORTS_DIR = "reports"


def _now() -> datetime:
    return datetime.now().astimezone()


class AppController:
    """Porta de entrada da CLI: valida o SearchRequest, dispara o AppService,
    formata o sumario da sessao e exporta a telemetria em JSON.
    Sem HTTP, sem framework.

    `reports_dir=None` desliga a exportacao (util em testes). `clock` e
    injetavel para tornar data e duracao deterministicas nos testes.
    """

    def __init__(
        self,
        app_service: AppService,
        reports_dir: Optional[str] = DEFAULT_REPORTS_DIR,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._service = app_service
        self._reports_dir = reports_dir
        self._clock = clock

    def execute(self, request: SearchRequest) -> str:
        self._validate(request)
        started = self._clock()
        jobs = self._service.run(request)
        finished = self._clock()

        summary = self.format_summary(jobs, request)
        report = self.build_telemetry(jobs, request, started, finished)
        path = self._export_telemetry(report, finished)
        if path:
            summary += f"\nTelemetria:           {path}"
        return summary

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

    # ------------------------------------------------------------ telemetria
    @staticmethod
    def build_telemetry(
        jobs: List[Job],
        request: SearchRequest,
        started: datetime,
        finished: datetime,
    ) -> Dict[str, Any]:
        """Funil de conversao de UMA execucao.

        total_read = skipped_complex + applied + errors + already_applied + not_processed
        (`not_processed` = vagas lidas que ficaram PENDING, ex.: teto de candidaturas).
        """
        counts = Counter(job.status for job in jobs)
        total = len(jobs)

        def rate(n: int) -> float:
            return round(n / total, 4) if total else 0.0

        return {
            "started_at": started.isoformat(timespec="seconds"),
            "finished_at": finished.isoformat(timespec="seconds"),
            "duration_seconds": round((finished - started).total_seconds(), 3),
            "platform": request.platform,
            "search_urls": len(request.static_urls),
            "max_applications": request.max_applications,
            "funnel": {
                "total_read": total,
                "skipped_complex": counts[JobStatus.SKIPPED_COMPLEX],
                "applied": counts[JobStatus.APPLIED],
                "errors": counts[JobStatus.ERROR],
                "already_applied": counts[JobStatus.ALREADY_APPLIED],
                "not_processed": counts[JobStatus.PENDING],
            },
            "conversion": {
                "applied_over_total": rate(counts[JobStatus.APPLIED]),
                "skipped_complex_over_total": rate(counts[JobStatus.SKIPPED_COMPLEX]),
                "errors_over_total": rate(counts[JobStatus.ERROR]),
            },
            # Informativo e fora do funil: quantas vagas nem foram reabertas
            # porque o cache local ja as conhecia (v0.6).
            "cache": {"hits": sum(1 for job in jobs if job.from_cache)},
            "jobs": [
                {
                    "url": job.url,
                    "title": job.title,
                    "company": job.company,
                    "status": job.status.value,
                    "from_cache": job.from_cache,
                }
                for job in jobs
            ],
        }

    def _export_telemetry(self, report: Dict[str, Any], finished: datetime) -> Optional[str]:
        """Acrescenta a execucao em `<reports_dir>/telemetry_YYYYMMDD.json`.

        Um arquivo por dia, com a lista de execucoes: rodar duas vezes no mesmo
        dia nao apaga a primeira. Falha de I/O nunca derruba a sessao.
        """
        if self._reports_dir is None:
            return None
        path = os.path.join(self._reports_dir, f"telemetry_{finished:%Y%m%d}.json")
        try:
            os.makedirs(self._reports_dir, exist_ok=True)
            document = self._load_day_document(path, finished)
            document["runs"].append(report)

            tmp_path = f"{path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(document, fh, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)  # escrita atomica
            return path
        except OSError:
            logger.exception("Falha ao exportar a telemetria em %s", path)
            return None

    @staticmethod
    def _load_day_document(path: str, finished: datetime) -> Dict[str, Any]:
        """Le o arquivo do dia; se estiver corrompido, preserva-o como
        `.corrupt-HHMMSS` e comeca um novo (nunca perde dado em silencio)."""
        fresh = {"date": f"{finished:%Y-%m-%d}", "runs": []}
        if not os.path.exists(path):
            return fresh
        try:
            with open(path, encoding="utf-8") as fh:
                document = json.load(fh)
            if isinstance(document, dict) and isinstance(document.get("runs"), list):
                return document
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        backup = f"{path}.corrupt-{finished:%H%M%S}"
        os.replace(path, backup)
        logger.warning("Telemetria existente ilegivel; preservada em %s", backup)
        return fresh
