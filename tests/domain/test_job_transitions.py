"""Maquina de estados do Job: transicoes com nome de intencao e regra do envio."""
import itertools

import pytest

from src.domain.entities.job import (
    InvalidTransition,
    Job,
    JobStatus,
    ReviewReason,
    SubmissionEvidence,
)

S = JobStatus
PERMITIDAS = {
    (S.PENDING, S.SUBMITTING),
    (S.PENDING, S.SKIPPED_COMPLEX),
    (S.PENDING, S.ERROR),
    (S.PENDING, S.SIMULATED),
    (S.PENDING, S.ALREADY_APPLIED),
    (S.SUBMITTING, S.APPLIED),
    (S.SUBMITTING, S.MANUAL_REVIEW),
}


def _job(status=S.PENDING) -> Job:
    return Job(url="https://x.com/jobs/1", platform="p", title="t", company="c", status=status)


def _ir_para(job: Job, alvo: JobStatus) -> None:
    {
        S.SUBMITTING: job.mark_submitting,
        S.APPLIED: job.mark_applied,
        S.MANUAL_REVIEW: lambda: job.mark_manual_review(ReviewReason.CLICK_FAILED),
        S.SIMULATED: job.mark_simulated,
        S.SKIPPED_COMPLEX: job.mark_skipped_complex,
        S.ERROR: job.mark_error,
        S.ALREADY_APPLIED: lambda: job._transition(S.ALREADY_APPLIED),
        S.PENDING: lambda: job._transition(S.PENDING),
    }[alvo]()


@pytest.mark.parametrize("origem,alvo", list(itertools.product(S, S)))
def test_matriz_de_transicoes(origem, alvo):
    job = _job(origem)
    if (origem, alvo) in PERMITIDAS:
        _ir_para(job, alvo)
        assert job.status is alvo
    else:
        with pytest.raises(InvalidTransition):
            _ir_para(job, alvo)
        assert job.status is origem


def test_transicao_invalida_diz_origem_e_destino():
    with pytest.raises(InvalidTransition, match=r"APPLIED -> ERROR nao e permitido\."):
        _job(S.APPLIED).mark_error()


def test_mark_manual_review_guarda_o_motivo():
    job = _job(S.SUBMITTING)
    job.mark_manual_review(ReviewReason.MODAL_STILL_OPEN)
    assert job.review_reason is ReviewReason.MODAL_STILL_OPEN


def test_vaga_nova_nao_tem_motivo_de_revisao():
    assert _job().review_reason is None


@pytest.mark.parametrize(
    "clique,confirmacao,modal,motivo",
    [
        (True, True, False, None),
        (False, True, False, ReviewReason.CLICK_FAILED),
        (False, False, True, ReviewReason.CLICK_FAILED),
        (True, True, True, ReviewReason.MODAL_STILL_OPEN),
        (True, False, True, ReviewReason.MODAL_STILL_OPEN),
        (True, False, False, ReviewReason.CONFIRMATION_MISSING),
    ],
)
def test_evidencia_so_confirma_com_as_tres_condicoes(clique, confirmacao, modal, motivo):
    ev = SubmissionEvidence(clique, confirmacao, modal)
    assert ev.review_reason is motivo


def test_envio_confirmado_vira_applied():
    job = _job(S.SUBMITTING)
    job.settle_submission(SubmissionEvidence(True, True, False))
    assert job.status is S.APPLIED and job.review_reason is None


def test_envio_sem_confirmacao_vira_revisao_manual_e_nao_error():
    job = _job(S.SUBMITTING)
    job.settle_submission(SubmissionEvidence(True, False, False))
    assert job.status is S.MANUAL_REVIEW
    assert job.review_reason is ReviewReason.CONFIRMATION_MISSING


def test_settle_exige_envio_em_andamento():
    with pytest.raises(InvalidTransition):
        _job(S.PENDING).settle_submission(SubmissionEvidence(True, True, False))


@pytest.mark.parametrize(
    "lembrado,esperado,motivo",
    [
        (S.APPLIED, S.ALREADY_APPLIED, None),
        (S.ALREADY_APPLIED, S.ALREADY_APPLIED, None),
        (S.SKIPPED_COMPLEX, S.SKIPPED_COMPLEX, None),
        (S.MANUAL_REVIEW, S.MANUAL_REVIEW, ReviewReason.ALREADY_IN_REVIEW),
        (S.SUBMITTING, S.MANUAL_REVIEW, ReviewReason.INTERRUPTED_BEFORE_RESULT),
    ],
)
def test_historico_restaura_a_vaga_sem_reabri_la(lembrado, esperado, motivo):
    job = _job()
    job.restore_from_history(lembrado)
    assert (job.status, job.review_reason, job.from_cache) == (esperado, motivo, True)


@pytest.mark.parametrize("lembrado", [S.PENDING, S.ERROR, S.SIMULATED])
def test_historico_recusa_status_que_nao_se_lembra(lembrado):
    with pytest.raises(InvalidTransition):
        _job().restore_from_history(lembrado)


def test_historico_so_restaura_vaga_pendente():
    with pytest.raises(InvalidTransition):
        _job(S.ERROR).restore_from_history(S.APPLIED)
