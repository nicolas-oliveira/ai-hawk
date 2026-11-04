"""Maquina de estados do Job: transicoes com nome de intencao e regra do envio."""
import dataclasses
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
    with pytest.raises(InvalidTransition, match=r"^APPLIED -> ERROR nao e permitido\.$"):
        _job(S.APPLIED).mark_error()


def test_mark_manual_review_guarda_o_motivo():
    job = _job(S.SUBMITTING)
    job.mark_manual_review(ReviewReason.MODAL_STILL_OPEN)
    assert job.review_reason is ReviewReason.MODAL_STILL_OPEN


def test_vaga_nova_nao_tem_motivo_de_revisao():
    assert _job().review_reason is None


def _linhas_da_evidencia():
    """Tabela-verdade completa (16 linhas): clique, confirmacao, estado, dialogo."""
    for clique in (True, False):
        for confirmacao in (True, False):
            for estado in (True, False):
                for modal in (True, False):
                    if not clique:
                        motivo = ReviewReason.CLICK_FAILED
                    elif confirmacao and estado:
                        motivo = None  # so sucesso confirmado dos DOIS lados, qualquer dialogo
                    elif confirmacao:
                        motivo = ReviewReason.STATE_NOT_CONFIRMED
                    elif estado:
                        motivo = ReviewReason.STATE_WITHOUT_CONFIRMATION
                    elif modal:
                        motivo = ReviewReason.MODAL_STILL_OPEN
                    else:
                        motivo = ReviewReason.CONFIRMATION_MISSING
                    yield clique, confirmacao, estado, modal, motivo


@pytest.mark.parametrize("clique,confirmacao,estado,modal,motivo", list(_linhas_da_evidencia()))
def test_confirmacao_e_estado_decidem_o_envio(clique, confirmacao, estado, modal, motivo):
    ev = SubmissionEvidence(clique, confirmacao, modal, estado)
    assert ev.review_reason is motivo


@pytest.mark.parametrize(
    "clique,confirmacao,estado,modal,motivo",
    [
        (True, True, True, True, None),
        (True, True, False, False, ReviewReason.STATE_NOT_CONFIRMED),
        (True, False, True, False, ReviewReason.STATE_WITHOUT_CONFIRMATION),
        (True, False, False, True, ReviewReason.MODAL_STILL_OPEN),
        (True, False, False, False, ReviewReason.CONFIRMATION_MISSING),
        (False, True, True, False, ReviewReason.CLICK_FAILED),
    ],
)
def test_linhas_da_tabela_escritas_a_mao(clique, confirmacao, estado, modal, motivo):
    # Independente do gerador acima: se a regra e o gerador errarem juntos, esta pega.
    assert SubmissionEvidence(clique, confirmacao, modal, estado).review_reason is motivo


def test_envio_confirmado_vira_applied():
    job = _job(S.SUBMITTING)
    job.settle_submission(SubmissionEvidence(True, True, False, True))
    assert job.status is S.APPLIED and job.review_reason is None


def test_envio_sem_confirmacao_vira_revisao_manual_e_nao_error():
    job = _job(S.SUBMITTING)
    job.settle_submission(SubmissionEvidence(True, False, False))
    assert job.status is S.MANUAL_REVIEW
    assert job.review_reason is ReviewReason.CONFIRMATION_MISSING


def test_settle_exige_envio_em_andamento():
    with pytest.raises(InvalidTransition):
        _job(S.PENDING).settle_submission(SubmissionEvidence(True, True, False, True))


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


def test_historico_recusa_com_mensagem_exata():
    with pytest.raises(InvalidTransition, match=r"^ERROR nao restaura APPLIED\.$"):
        _job(S.ERROR).restore_from_history(S.APPLIED)


@pytest.mark.parametrize(
    "motivo,texto",
    [
        (ReviewReason.CLICK_FAILED, "clique de envio falhou ou estourou o tempo"),
        (ReviewReason.MODAL_STILL_OPEN, "modal ainda aberto apos o envio"),
        (ReviewReason.CONFIRMATION_MISSING, "confirmacao de envio ausente"),
        (ReviewReason.STATE_NOT_CONFIRMED, "confirmacao vista, mas a pagina nao mostra a vaga como candidatada"),
        (ReviewReason.STATE_WITHOUT_CONFIRMATION, "pagina mostra a vaga como candidatada, mas sem confirmacao de envio"),
        (ReviewReason.INTERRUPTED_BEFORE_RESULT, "execucao interrompida antes do resultado do envio"),
        (ReviewReason.ALREADY_IN_REVIEW, "ja estava em revisao manual de uma execucao anterior"),
    ],
)
def test_motivos_de_revisao_tem_texto_fixo(motivo, texto):
    assert motivo.value == texto


def test_evidencia_e_imutavel():
    with pytest.raises(dataclasses.FrozenInstanceError):
        SubmissionEvidence(True, True, False, True).click_completed = False


def test_evidencia_so_com_clique_nao_traz_confirmacao_nem_modal_aberto():
    ev = SubmissionEvidence(click_completed=False)
    assert (ev.confirmation_seen, ev.modal_still_open, ev.applied_state_seen) == (False, False, False)


def test_canonicalize_url_e_estatico_tambem_pela_instancia():
    job = Job(url="https://x.com/jobs/1/", platform="p", title="", company="")
    assert job.canonicalize_url("https://x.com/jobs/1234567/?a=1#f") == "https://x.com/jobs/1234567/"


def test_vaga_pendente_pode_virar_already_applied_pela_pagina():
    job = _job(S.PENDING)
    job.mark_already_applied()
    assert (job.status, job.review_reason, job.from_cache) == (S.ALREADY_APPLIED, None, False)


@pytest.mark.parametrize("origem", [S.SUBMITTING, S.APPLIED, S.ERROR, S.MANUAL_REVIEW])
def test_already_applied_so_a_partir_de_pending(origem):
    with pytest.raises(InvalidTransition):
        _job(origem).mark_already_applied()
