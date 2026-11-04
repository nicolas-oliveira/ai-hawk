"use client";

import { useState, useEffect } from "react";

const INITIAL_JOBS = [
  {
    id: "job-1",
    title: "Vaga 1",
    company: "Empresa Acme",
    location: "Remoto / São Paulo, SP",
    description:
      "Oportunidade para engenharia de software sênior na Empresa Acme com foco em sistemas distribuídos.",
    complex: false,
  },
  {
    id: "job-2",
    title: "Vaga 2 (Complexa)",
    company: "Tech Corp",
    location: "Híbrido / Curitiba, PR",
    description:
      "Vaga com formulário extenso exigindo preenchimento manual obrigatório no segundo passo.",
    complex: true,
  },
];

const SCENARIO_JOBS = {
  "job-challenge": {
    id: "job-challenge",
    title: "Vaga Desafio Anti-Bot",
    company: "SecOps Corp",
    location: "Remoto",
    description: "Vaga protegida por desafio de segurança ao abrir os detalhes.",
    complex: false,
    challengeOnDetail: true,
  },
  "job-broken-modal": {
    id: "job-broken-modal",
    title: "Vaga Modal Inoperante",
    company: "NullDialog Corp",
    location: "Remoto",
    description: "Vaga cujo botão de candidatura não abre nenhum diálogo.",
    complex: false,
    brokenModal: true,
  },
  "job-slow-modal": {
    id: "job-slow-modal",
    title: "Vaga Modal Lento",
    company: "Async Corp",
    location: "Remoto",
    description: "Vaga cujo modal abre com atraso dentro do prazo da porta.",
    complex: false,
    slowModal: true,
    slowModalDelayMs: 600,
  },
  "job-very-slow-modal": {
    id: "job-very-slow-modal",
    title: "Vaga Modal Muito Lento",
    company: "Timeout Corp",
    location: "Remoto",
    description: "Vaga cujo modal demora 2500ms para abrir, estourando prazos curtos.",
    complex: false,
    slowModal: true,
    slowModalDelayMs: 2500,
  },
  "job-stuck-submit": {
    id: "job-stuck-submit",
    title: "Vaga Modal Preso no Submit",
    company: "Stuck Corp",
    location: "Remoto",
    description: "Vaga cujo modal não fecha após o clique em Submit.",
    complex: false,
    stuckSubmit: true,
  },
  "job-no-confirm": {
    id: "job-no-confirm",
    title: "Vaga Sem Aviso de Confirmacao",
    company: "Silent Corp",
    location: "Remoto",
    description: "Vaga cujo modal fecha após o Submit sem exibir banner de confirmação.",
    complex: false,
    noConfirmSubmit: true,
  },
  "job-close-on-submit": {
    id: "job-close-on-submit",
    title: "Vaga Fecha Modal no Submit",
    company: "AutoClose Corp",
    location: "Remoto",
    description: "Vaga cujo modal fecha no Submit e exibe confirmação fora do modal.",
    complex: false,
    closeOnSubmit: true,
  },
  "job-already-applied": {
    id: "job-already-applied",
    title: "Vaga Já Candidatada",
    company: "Already Corp",
    location: "Remoto",
    description: "Vaga que o portal já mostra como candidatada ao abrir.",
    complex: false,
    alreadyApplied: true,
  },
  "job-late-applied": {
    id: "job-late-applied",
    title: "Vaga Candidatada com Atraso",
    company: "LateState Corp",
    location: "Remoto",
    description: "Vaga sem botão de candidatura cujo selo de candidatada pinta com 400ms de atraso.",
    complex: false,
    lateApplied: true,
  },
  "job-confirm-no-state": {
    id: "job-confirm-no-state",
    title: "Vaga Confirmação Sem Estado",
    company: "NoState Corp",
    location: "Remoto",
    description: "Vaga onde a confirmação aparece no modal mas o estado na página não muda.",
    complex: false,
    confirmNoState: true,
  },
  "job-state-no-confirm": {
    id: "job-state-no-confirm",
    title: "Vaga Estado Sem Confirmação",
    company: "NoConfirmState Corp",
    location: "Remoto",
    description: "Vaga onde o estado na página muda para candidatada mas a confirmação no modal não aparece.",
    complex: false,
    stateNoConfirm: true,
  },
};

const ALL_JOBS = [...INITIAL_JOBS, ...Object.values(SCENARIO_JOBS)];

function resolveScenarioJobs(scenario) {
  if (scenario === "already-applied") {
    return [SCENARIO_JOBS["job-already-applied"]];
  }
  if (scenario === "late-applied") {
    return [SCENARIO_JOBS["job-late-applied"]];
  }
  if (scenario === "confirm-without-state") {
    return [SCENARIO_JOBS["job-confirm-no-state"], INITIAL_JOBS[0]];
  }
  if (scenario === "state-without-confirm") {
    return [SCENARIO_JOBS["job-state-no-confirm"], INITIAL_JOBS[0]];
  }
  if (scenario === "job-challenge") {
    return [SCENARIO_JOBS["job-challenge"], INITIAL_JOBS[0]];
  }
  if (scenario === "broken-modal") {
    return [SCENARIO_JOBS["job-broken-modal"], INITIAL_JOBS[0]];
  }
  if (scenario === "slow-modal") {
    return [SCENARIO_JOBS["job-slow-modal"]];
  }
  if (scenario === "very-slow-modal") {
    return [SCENARIO_JOBS["job-very-slow-modal"], INITIAL_JOBS[0]];
  }
  if (scenario === "stuck-submit") {
    return [SCENARIO_JOBS["job-stuck-submit"], INITIAL_JOBS[0]];
  }
  if (scenario === "no-confirm") {
    return [SCENARIO_JOBS["job-no-confirm"], INITIAL_JOBS[0]];
  }
  if (scenario === "close-on-submit") {
    return [SCENARIO_JOBS["job-close-on-submit"]];
  }
  return INITIAL_JOBS;
}

export default function Home() {
  const [seed, setSeed] = useState("init");
  const [wrapperVariant, setWrapperVariant] = useState(0);

  // 1. Lazy Loading states
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Modal & Step Lazy Loading states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalStep, setModalStep] = useState(1);
  const [stepLoading, setStepLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [jobApplied, setJobApplied] = useState(false);

  // 2. Intrusive Overlay / Cookie / Promo Banner state
  const [overlayVisible, setOverlayVisible] = useState(false);
  const [overlayDismissed, setOverlayDismissed] = useState(false);

  // 3. Honeypot Trap state
  const [honeypotTriggered, setHoneypotTriggered] = useState(false);
  const [honeypotReason, setHoneypotReason] = useState("");

  useEffect(() => {
    const generatedSeed = Math.random().toString(36).substring(2, 7);
    const variant = Math.floor(Math.random() * 3);
    setSeed(generatedSeed);
    setWrapperVariant(variant);
    console.log("DOM Seed:", generatedSeed, "Variant:", variant);

    // Restaura estado de armadilha Honeypot se tiver sido violado em navegacao anterior da sessao
    const savedTrap = window.sessionStorage.getItem("honeypot_compromised");
    if (savedTrap) {
      setHoneypotTriggered(true);
      setHoneypotReason(savedTrap);
    }

    // Simula Lazy Loading da lista inicial de vagas (1.2s)
    const jobsTimer = setTimeout(() => {
      const params = new URLSearchParams(window.location.search);
      const scenarioParam = params.get("scenario");
      const activeJobs = resolveScenarioJobs(scenarioParam);
      setJobs(activeJobs);
      setJobsLoading(false);
      const jobIdParam = params.get("jobId");
      if (jobIdParam) {
        if (jobIdParam === "honeypot-job") {
          triggerHoneypot("Navegou diretamente para a URL da vaga Honeypot oculta");
        } else {
          const matched = ALL_JOBS.find((j) => j.id === jobIdParam);
          if (matched) {
            setSelectedJob(matched);
            if (matched.alreadyApplied) {
              setJobApplied(true);
            }
            if (matched.lateApplied) {
              setTimeout(() => setJobApplied(true), 400);
            }
          }
        }
      }
    }, 1200);

    // Dispara Overlay Intrusivo após 800ms (se ainda nao descartado na sessao)
    const overlayDismissedSession = window.sessionStorage.getItem("overlay_dismissed") === "true";
    if (overlayDismissedSession) {
      setOverlayDismissed(true);
    }
    const overlayTimer = setTimeout(() => {
      if (!overlayDismissedSession) {
        setOverlayVisible(true);
      }
    }, 800);

    return () => {
      clearTimeout(jobsTimer);
      clearTimeout(overlayTimer);
    };
  }, []);

  const triggerHoneypot = (reason) => {
    console.error("HONEYPOT TRIGGERED:", reason);
    window.sessionStorage.setItem("honeypot_compromised", reason);
    setHoneypotTriggered(true);
    setHoneypotReason(reason);
  };

  const handleSelectJob = (job) => {
    if (overlayVisible && !overlayDismissed) {
      triggerHoneypot("Tentou selecionar vaga com Overlay Intrusivo ativo (bypass de z-index)");
      return;
    }
    setDetailLoading(true);
    setSelectedJob(null);
    setJobApplied(Boolean(job.alreadyApplied));
    setWrapperVariant((prev) => (prev + 1) % 3);
    setTimeout(() => {
      setSelectedJob(job);
      setDetailLoading(false);
      if (job.alreadyApplied) {
        setJobApplied(true);
      }
      if (job.lateApplied) {
        setJobApplied(false);
        setTimeout(() => setJobApplied(true), 400);
      }
    }, 1000);
  };

  const handleOpenModal = () => {
    if (overlayVisible && !overlayDismissed) {
      triggerHoneypot("Tentou abrir modal com Overlay Intrusivo ativo (bypass de z-index)");
      return;
    }
    if (selectedJob?.brokenModal) {
      return;
    }
    setModalStep(1);
    setSubmitted(false);
    setWrapperVariant((prev) => (prev + 1) % 3);
    if (selectedJob?.slowModal) {
      const modalDelayMs = selectedJob?.slowModalDelayMs || 600;
      setTimeout(() => {
        setStepLoading(true);
        setIsModalOpen(true);
        setTimeout(() => {
          setStepLoading(false);
        }, 400);
      }, modalDelayMs);
      return;
    }
    setStepLoading(true);
    setIsModalOpen(true);
    setTimeout(() => {
      setStepLoading(false);
    }, 1100);
  };

  const handleNextStep = () => {
    setStepLoading(true);
    setWrapperVariant((prev) => (prev + 1) % 3);
    setTimeout(() => {
      setModalStep(2);
      setStepLoading(false);
    }, 1300);
  };

  const handleSubmitApplication = (e) => {
    if (e) e.preventDefault();
    setStepLoading(true);
    setTimeout(() => {
      setStepLoading(false);
      if (selectedJob?.stuckSubmit) {
        return;
      }
      if (selectedJob?.confirmNoState) {
        setSubmitted(true);
        setJobApplied(false);
        return;
      }
      if (selectedJob?.stateNoConfirm) {
        setIsModalOpen(false);
        setSubmitted(false);
        setJobApplied(true);
        return;
      }
      if (selectedJob?.noConfirmSubmit) {
        setIsModalOpen(false);
        setSubmitted(false);
        setJobApplied(true);
        return;
      }
      if (selectedJob?.closeOnSubmit) {
        setIsModalOpen(false);
        setSubmitted(true);
        setJobApplied(true);
        window.sessionStorage.setItem(
          "modal_submission_success",
          "Candidatura enviada com sucesso!"
        );
        return;
      }
      // Fluxo base da v1.5 (sem ?scenario=): modal permanece aberto com
      // [data-testid="modal-submission-success"] dentro do dialogo e pagina ganha [data-testid="job-applied"].
      setSubmitted(true);
      setJobApplied(true);
      window.sessionStorage.setItem(
        "modal_submission_success",
        "Candidatura enviada com sucesso!"
      );
    }, 1000);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setModalStep(1);
    setStepLoading(false);
  };

  const handleDismissOverlay = () => {
    window.sessionStorage.setItem("overlay_dismissed", "true");
    setOverlayVisible(false);
    setOverlayDismissed(true);
  };

  // 4. Mutação Hostil: Wrappers dinâmicos que alteram a profundidade da árvore DOM
  const renderMutatedWrapper = (children, label) => {
    if (wrapperVariant === 0) {
      return (
        <div id={`wrap-a-${seed}`} className={`mut-v0-${seed}`}>
          {children}
        </div>
      );
    }
    if (wrapperVariant === 1) {
      return (
        <div id={`wrap-b1-${seed}`} className={`mut-v1-outer-${seed}`}>
          <div className={`mut-v1-inner-${seed}`}>
            <span className="hidden" aria-hidden="true">{label}</span>
            {children}
          </div>
        </div>
      );
    }
    return (
      <section id={`wrap-c1-${seed}`} className={`mut-v2-sec-${seed}`}>
        <div className={`mut-v2-box-${seed}`}>
          <div className={`mut-v2-deep-${seed}`}>{children}</div>
        </div>
      </section>
    );
  };

  return (
    <main
      id={`app-root-${seed}`}
      data-seed={seed}
      className={"min-h-screen bg-gray-100 p-6 main-container-" + seed}
    >
      {/* Alerta caso o robô caia em alguma armadilha Honeypot */}
      {honeypotTriggered && (
        <div
          role="alert"
          data-testid="honeypot-compromised"
          className="mb-4 bg-red-700 text-white p-4 rounded shadow-lg font-bold"
        >
          BOT DETECTADO (HONEYPOT ATIVADO): {honeypotReason}
        </div>
      )}

      <header id={`hdr-${seed}`} className={"mb-6 bg-white p-4 shadow rounded navbar-" + seed}>
        <h1 className={"text-xl font-bold header-title-" + seed}>
          LinkedIn Mock Portal (SPA Hostil)
        </h1>
      </header>

      {/* 2. OVERLAY / INTERCEPTAÇÃO DE ALTO Z-INDEX */}
      {overlayVisible && !overlayDismissed && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Cookie and Premium Interception"
          id={`intrusive-overlay-${seed}`}
          className={"fixed inset-0 bg-black/75 z-[90] flex items-center justify-center p-4 overlay-trap-" + seed}
        >
          <div className={"bg-white p-6 rounded-xl shadow-2xl max-w-md w-full border-2 border-amber-500 overlay-box-" + seed}>
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              Aviso de Privacidade e Assinatura Premium
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Este portal utiliza cookies analíticos. Aceite ou feche este aviso para interagir com as vagas disponíveis.
            </p>
            {/* Botão Honeypot invisível dentro do overlay */}
            <button
              type="button"
              style={{ opacity: 0, position: "absolute", left: "-9999px" }}
              tabIndex={-1}
              onClick={() => triggerHoneypot("Clicou no botão fantasma do Overlay")}
            >
              Aceitar Tudo (Honeypot)
            </button>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                aria-label="Dismiss overlay"
                onClick={handleDismissOverlay}
                className={"px-4 py-2 bg-amber-600 text-white rounded font-semibold hover:bg-amber-700 btn-close-overlay-" + seed}
              >
                Aceitar Cookies e Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Layout de 2 colunas com mutação estrutural */}
      <div className={"flex gap-6 layout-grid-" + seed}>
        {/* Painel Esquerdo: Lista de Vagas com Lazy Loading */}
        <section
          aria-label="Jobs List"
          id={`left-pane-${seed}`}
          className={"w-1/3 bg-white p-4 rounded shadow max-h-[75vh] overflow-y-auto panel-left-" + seed}
        >
          <h2 className={"text-lg font-semibold mb-4 section-title-" + seed}>
            Vagas Recomendadas
          </h2>

          {jobsLoading ? (
            <div
              role="status"
              aria-live="polite"
              className={"py-8 text-center text-gray-500 animate-pulse loader-jobs-" + seed}
            >
              Carregando lista de vagas...
            </div>
          ) : (
            renderMutatedWrapper(
              <ul className={"space-y-3 job-list-" + seed}>
                {/* Card Honeypot oculto via display:none */}
                <li
                  style={{ display: "none" }}
                  onClick={() => triggerHoneypot("Clicou em card de vaga oculto (display:none)")}
                  className={"card-honeypot-" + seed}
                >
                  <a href="/?jobId=honeypot-job">Vaga Fantasma Armadilha</a>
                  <h3>Vaga Armadilha</h3>
                  <p>Empresa Honeypot</p>
                </li>

                {jobs.map((job) => (
                  <li
                    key={job.id}
                    id={`card-${job.id}-${seed}`}
                    onClick={() => handleSelectJob(job)}
                    className={
                      "cursor-pointer p-4 border rounded hover:border-blue-500 transition " +
                      (selectedJob?.id === job.id
                        ? "border-blue-600 bg-blue-50 "
                        : "border-gray-200 ") +
                      "card-item-" +
                      seed
                    }
                  >
                    <div className={"job-card-wrapper-" + seed}>
                      <a
                        href={`/?jobId=${job.id}`}
                        onClick={(e) => e.preventDefault()}
                        className={"font-bold text-blue-700 block card-title-" + seed}
                      >
                        <h3>{job.title}</h3>
                      </a>
                      <p className={"text-sm text-gray-700 card-company-" + seed}>
                        {job.company}
                      </p>
                      <p className={"text-xs text-gray-500 card-location-" + seed}>
                        {job.location}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>,
              "jobs-list-mutation"
            )
          )}
        </section>

        {/* Painel Direito: Detalhe da Vaga com Lazy Loading e Honeypots */}
        <section
          aria-label="Job Details"
          id={`right-pane-${seed}`}
          className={"flex-1 bg-white p-6 rounded shadow panel-right-" + seed}
        >
          {detailLoading ? (
            <div
              role="status"
              aria-live="polite"
              className={"py-12 text-center text-gray-500 animate-pulse loader-detail-" + seed}
            >
              Carregando detalhes da vaga...
            </div>
          ) : selectedJob ? (
            selectedJob.challengeOnDetail ? (
              <div
                data-aihawk-challenge="captcha"
                data-testid="captcha-challenge"
                className="p-8 border-2 border-red-400 bg-red-50 rounded text-center"
              >
                <h2 className="text-xl font-bold text-red-800 mb-2">
                  Verificação de Segurança na Vaga
                </h2>
                <p className="text-sm text-red-700">
                  Desafio anti-bot ativado ao acessar o detalhe desta vaga.
                </p>
              </div>
            ) : (
              renderMutatedWrapper(
                <div className={"details-content-" + seed}>
                  {submitted && (
                    <div
                      data-testid="modal-submission-success"
                      className={"mb-4 p-4 bg-green-50 border border-green-400 rounded text-center success-state-" + seed}
                    >
                      <p className={"text-green-700 font-bold text-lg mb-1"}>
                        Candidatura enviada com sucesso!
                      </p>
                      <p className={"text-sm text-gray-600"}>
                        Sua aplicação foi submetida à {selectedJob?.company}.
                      </p>
                    </div>
                  )}
                  <div className={"border-b pb-4 mb-4 details-header-" + seed}>
                    <h2 className={"text-2xl font-bold text-gray-900"}>{selectedJob.title}</h2>
                    <p className={"text-md text-gray-600 font-medium"}>{selectedJob.company}</p>
                    <p className={"text-sm text-gray-500"}>{selectedJob.location}</p>

                    <div className={"mt-4 flex gap-3 items-center relative action-bar-" + seed}>
                      {jobApplied ? (
                        <div
                          data-testid="job-applied"
                          className="px-4 py-2 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded-full font-semibold text-sm flex items-center gap-2"
                        >
                          <span aria-hidden="true">✓</span> Candidatura enviada
                        </div>
                      ) : selectedJob.lateApplied && !jobApplied ? null : (
                        <>
                          {/* 3. HONEYPOT: Botão de candidatura falso fora da tela */}
                          <button
                            type="button"
                            style={{
                              opacity: 0,
                              position: "absolute",
                              left: "-9999px",
                              pointerEvents: "none",
                            }}
                            tabIndex={-1}
                            aria-hidden="true"
                            onClick={() =>
                              triggerHoneypot("Clicou no botão Candidatura Simplificada oculto (left: -9999px)")
                            }
                            className={"btn-apply-trap-" + seed}
                          >
                            Candidatura Simplificada
                          </button>

                          {/* Botão Real */}
                          <button
                            type="button"
                            id={`btn-apply-${seed}`}
                            onClick={handleOpenModal}
                            className={
                              "bg-blue-600 text-white px-5 py-2 rounded-full font-semibold hover:bg-blue-700 transition btn-apply-" +
                              seed
                            }
                          >
                            Candidatura Simplificada
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  <div className={"text-gray-800 leading-relaxed description-body-" + seed}>
                    <h4 className={"font-semibold mb-2"}>Sobre a vaga</h4>
                    <p>{selectedJob.description}</p>
                  </div>
                </div>,
                "job-detail-mutation"
              )
            )
          ) : (
            <div className={"text-center py-12 text-gray-500 placeholder-" + seed}>
              <p>Selecione uma vaga no painel esquerdo para visualizar os detalhes.</p>
            </div>
          )}
        </section>
      </div>

      {/* Modal Easy Apply com Lazy Loading entre passos e Honeypots no formulário */}
      {isModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Easy Apply Modal"
          id={`modal-backdrop-${seed}`}
          className={
            "fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 modal-backdrop-" +
            seed
          }
        >
          <div
            id={`modal-container-${seed}`}
            className={
              "bg-white rounded-lg shadow-2xl max-w-lg w-full overflow-hidden modal-box-" + seed
            }
          >
            {/* Header do Modal com botão Dismiss */}
            <div className={"flex justify-between items-center px-6 py-4 border-b modal-header-" + seed}>
              <h3 className={"text-lg font-bold text-gray-900"}>
                Candidatar-se a {selectedJob?.title}
              </h3>
              <button
                type="button"
                aria-label="Dismiss"
                id={`btn-dismiss-${seed}`}
                onClick={handleCloseModal}
                className={"text-gray-500 hover:text-gray-800 text-xl font-bold p-1 btn-dismiss-" + seed}
              >
                ✕
              </button>
            </div>

            {/* Corpo do Modal */}
            <form noValidate onSubmit={handleSubmitApplication} className={"p-6 modal-body-" + seed}>
              {/* 3. HONEYPOTS DE FORMULÁRIO: Inputs required ocultos que o Inspetor 3C DEVE ignorar */}
              <input
                type="text"
                name="bot_trap_display_none"
                required
                defaultValue=""
                style={{ display: "none" }}
                tabIndex={-1}
                onChange={() => triggerHoneypot("Preencheu input honeypot display:none")}
              />
              <input
                type="text"
                name="bot_trap_offscreen"
                required
                defaultValue=""
                style={{ opacity: 0, position: "absolute", left: "-9999px", height: 0, width: 0 }}
                tabIndex={-1}
                onChange={() => triggerHoneypot("Preencheu input honeypot opacity:0/offscreen")}
              />

              {stepLoading ? (
                <div
                  role="status"
                  aria-live="polite"
                  className={"py-10 text-center text-gray-500 animate-pulse loader-modal-" + seed}
                >
                  Processando etapa da candidatura...
                </div>
              ) : submitted ? (
                <div
                  data-testid="modal-submission-success"
                  className={"text-center py-6 success-state-" + seed}
                >
                  <p className={"text-green-600 font-bold text-lg mb-2"}>
                    Candidatura enviada com sucesso!
                  </p>
                  <p className={"text-sm text-gray-600"}>
                    Sua aplicação foi submetida à {selectedJob?.company}.
                  </p>
                </div>
              ) : modalStep === 1 ? (
                renderMutatedWrapper(
                  <div className={"step-one-" + seed}>
                    <p className={"text-sm text-gray-600 mb-4"}>
                      Passo 1 de 2: Informações de Contato
                    </p>
                    <div className={"space-y-4 form-fields-" + seed}>
                      <div>
                        <label className={"block text-sm font-medium text-gray-700"}>
                          Nome Completo
                        </label>
                        <input
                          type="text"
                          required
                          defaultValue="Nicolas Candidato"
                          className={"mt-1 block w-full border rounded p-2 text-sm border-gray-300"}
                        />
                      </div>
                      <div>
                        <label className={"block text-sm font-medium text-gray-700"}>
                          E-mail
                        </label>
                        <input
                          type="email"
                          required
                          defaultValue="candidato@teste.com"
                          className={"mt-1 block w-full border rounded p-2 text-sm border-gray-300"}
                        />
                      </div>
                    </div>
                  </div>,
                  "step-1-mutation"
                )
              ) : (
                renderMutatedWrapper(
                  <div className={"step-two-" + seed}>
                    <p className={"text-sm text-gray-600 mb-4"}>
                      Passo 2 de 2: Revisão e Perguntas Adicionais
                    </p>
                    {selectedJob?.complex ? (
                      <div className={"space-y-3 complex-fields-" + seed}>
                        <label className={"block text-sm font-medium text-red-700"}>
                          Resumo de Arquitetura (Obrigatório) *
                        </label>
                        <textarea
                          required
                          aria-required="true"
                          defaultValue=""
                          placeholder="Descreva sua experiência..."
                          className={"mt-1 block w-full border rounded p-2 text-sm border-red-400"}
                        />
                      </div>
                    ) : (
                      <div
                        className={
                          "p-4 bg-gray-50 rounded border text-sm text-gray-700 review-box-" + seed
                        }
                      >
                        <p>
                          Tudo pronto! Confirme o envio da sua candidatura para{" "}
                          <strong>{selectedJob?.company}</strong>.
                        </p>
                      </div>
                    )}
                  </div>,
                  "step-2-mutation"
                )
              )}

              {/* Rodapé do Modal com botões de avanço e contrato ARIA inviolável */}
              <div
                className={
                  "mt-6 pt-4 bg-gray-50 border-t flex justify-end gap-3 modal-footer-" + seed
                }
              >
                {/* Botão Avançar Honeypot oculto */}
                <button
                  type="button"
                  style={{ display: "none" }}
                  tabIndex={-1}
                  onClick={() => triggerHoneypot("Clicou no botão Avançar honeypot oculto")}
                >
                  Avançar
                </button>

                {stepLoading ? (
                  <span className="text-xs text-gray-400 italic">Aguarde o carregamento...</span>
                ) : submitted ? (
                  <button
                    type="button"
                    aria-label="Dismiss"
                    onClick={handleCloseModal}
                    className={"px-4 py-2 bg-gray-600 text-white rounded font-medium hover:bg-gray-700"}
                  >
                    Concluir
                  </button>
                ) : modalStep === 1 ? (
                  <button
                    type="button"
                    aria-label="Continue to next step"
                    id={`btn-next-${seed}`}
                    onClick={handleNextStep}
                    className={
                      "px-5 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 btn-next-" +
                      seed
                    }
                  >
                    Avançar
                  </button>
                ) : (
                  <div className={"flex gap-2 btn-group-" + seed}>
                    <button
                      type="button"
                      onClick={() => setModalStep(1)}
                      className={
                        "px-4 py-2 border border-gray-300 rounded font-medium text-gray-700 hover:bg-gray-100"
                      }
                    >
                      Voltar
                    </button>
                    <button
                      type="submit"
                      aria-label="Submit application"
                      id={`btn-submit-${seed}`}
                      className={
                        "px-5 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 btn-submit-" +
                        seed
                      }
                    >
                      Enviar candidatura
                    </button>
                  </div>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
