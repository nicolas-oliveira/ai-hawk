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

    // Simula Lazy Loading da lista inicial de vagas (1.2s)
    const jobsTimer = setTimeout(() => {
      setJobs(INITIAL_JOBS);
      setJobsLoading(false);
    }, 1200);

    // Dispara Overlay Intrusivo após 800ms
    const overlayTimer = setTimeout(() => {
      setOverlayVisible(true);
    }, 800);

    return () => {
      clearTimeout(jobsTimer);
      clearTimeout(overlayTimer);
    };
  }, []);

  const triggerHoneypot = (reason) => {
    console.error("HONEYPOT TRIGGERED:", reason);
    setHoneypotTriggered(true);
    setHoneypotReason(reason);
  };

  const handleSelectJob = (job) => {
    setDetailLoading(true);
    setSelectedJob(null);
    setWrapperVariant((prev) => (prev + 1) % 3);
    setTimeout(() => {
      setSelectedJob(job);
      setDetailLoading(false);
    }, 1000);
  };

  const handleOpenModal = () => {
    setStepLoading(true);
    setIsModalOpen(true);
    setModalStep(1);
    setSubmitted(false);
    setWrapperVariant((prev) => (prev + 1) % 3);
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
      setSubmitted(true);
      setStepLoading(false);
    }, 1000);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setModalStep(1);
    setStepLoading(false);
  };

  const handleDismissOverlay = () => {
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
                  <a href="#honeypot-job">Vaga Fantasma Armadilha</a>
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
                        href={`#${job.id}`}
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
            renderMutatedWrapper(
              <div className={"details-content-" + seed}>
                <div className={"border-b pb-4 mb-4 details-header-" + seed}>
                  <h2 className={"text-2xl font-bold text-gray-900"}>{selectedJob.title}</h2>
                  <p className={"text-md text-gray-600 font-medium"}>{selectedJob.company}</p>
                  <p className={"text-sm text-gray-500"}>{selectedJob.location}</p>

                  <div className={"mt-4 flex gap-3 relative action-bar-" + seed}>
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
                  </div>
                </div>

                <div className={"text-gray-800 leading-relaxed description-body-" + seed}>
                  <h4 className={"font-semibold mb-2"}>Sobre a vaga</h4>
                  <p>{selectedJob.description}</p>
                </div>
              </div>,
              "job-detail-mutation"
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
            <form onSubmit={handleSubmitApplication} className={"p-6 modal-body-" + seed}>
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
                <div className={"text-center py-6 success-state-" + seed}>
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
