"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [seed, setSeed] = useState("init");
  const [selectedJob, setSelectedJob] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalStep, setModalStep] = useState(1);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const generatedSeed = Math.random().toString(36).substring(2, 7);
    setSeed(generatedSeed);
    console.log("DOM Seed:", generatedSeed);
  }, []);

  const jobs = [
    {
      id: "job-1",
      title: "Vaga 1",
      company: "Empresa Acme",
      location: "Remoto / São Paulo, SP",
      description: "Oportunidade para engenharia de software na Empresa Acme.",
    },
  ];

  const handleOpenModal = () => {
    setIsModalOpen(true);
    setModalStep(1);
    setSubmitted(false);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setModalStep(1);
  };

  return (
    <main className={"min-h-screen bg-gray-100 p-6 main-container-" + seed}>
      <header className={"mb-6 bg-white p-4 shadow rounded navbar-" + seed}>
        <h1 className={"text-xl font-bold header-title-" + seed}>LinkedIn Mock Portal</h1>
      </header>

      {/* Layout de 2 colunas */}
      <div className={"flex gap-6 layout-grid-" + seed}>
        {/* Painel Esquerdo: Lista de Vagas */}
        <section
          aria-label="Jobs List"
          className={"w-1/3 bg-white p-4 rounded shadow panel-left-" + seed}
        >
          <h2 className={"text-lg font-semibold mb-4 section-title-" + seed}>
            Vagas Recomendadas
          </h2>
          <ul className={"space-y-3 job-list-" + seed}>
            {jobs.map((job) => (
              <li
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className={
                  "cursor-pointer p-4 border rounded hover:border-blue-500 transition " +
                  (selectedJob?.id === job.id ? "border-blue-600 bg-blue-50 " : "border-gray-200 ") +
                  "card-item-" + seed
                }
              >
                <div className={"job-card-wrapper-" + seed}>
                  <h3 className={"font-bold text-blue-700 card-title-" + seed}>{job.title}</h3>
                  <p className={"text-sm text-gray-700 card-company-" + seed}>{job.company}</p>
                  <p className={"text-xs text-gray-500 card-location-" + seed}>{job.location}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Painel Direito: Detalhe da Vaga */}
        <section
          aria-label="Job Details"
          className={"flex-1 bg-white p-6 rounded shadow panel-right-" + seed}
        >
          {selectedJob ? (
            <div className={"details-content-" + seed}>
              <div className={"border-b pb-4 mb-4 details-header-" + seed}>
                <h2 className={"text-2xl font-bold text-gray-900"}>{selectedJob.title}</h2>
                <p className={"text-md text-gray-600 font-medium"}>{selectedJob.company}</p>
                <p className={"text-sm text-gray-500"}>{selectedJob.location}</p>

                <div className={"mt-4 flex gap-3 action-bar-" + seed}>
                  <button
                    type="button"
                    onClick={handleOpenModal}
                    className={"bg-blue-600 text-white px-5 py-2 rounded-full font-semibold hover:bg-blue-700 transition btn-apply-" + seed}
                  >
                    Candidatura Simplificada
                  </button>
                </div>
              </div>

              <div className={"text-gray-800 leading-relaxed description-body-" + seed}>
                <h4 className={"font-semibold mb-2"}>Sobre a vaga</h4>
                <p>{selectedJob.description}</p>
              </div>
            </div>
          ) : (
            <div className={"text-center py-12 text-gray-500 placeholder-" + seed}>
              <p>Selecione uma vaga no painel esquerdo para visualizar os detalhes.</p>
            </div>
          )}
        </section>
      </div>

      {/* Modal Easy Apply com fundo escuro e z-index alto */}
      {isModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className={"fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 modal-backdrop-" + seed}
        >
          <div className={"bg-white rounded-lg shadow-2xl max-w-lg w-full overflow-hidden modal-box-" + seed}>
            {/* Header do Modal com botão Dismiss */}
            <div className={"flex justify-between items-center px-6 py-4 border-b modal-header-" + seed}>
              <h3 className={"text-lg font-bold text-gray-900"}>
                Candidatar-se a {selectedJob?.title}
              </h3>
              <button
                type="button"
                aria-label="Dismiss"
                onClick={handleCloseModal}
                className={"text-gray-500 hover:text-gray-800 text-xl font-bold p-1 btn-dismiss-" + seed}
              >
                ✕
              </button>
            </div>

            {/* Corpo do Modal */}
            <div className={"p-6 modal-body-" + seed}>
              {submitted ? (
                <div className={"text-center py-6 success-state-" + seed}>
                  <p className={"text-green-600 font-bold text-lg mb-2"}>
                    Candidatura enviada com sucesso!
                  </p>
                  <p className={"text-sm text-gray-600"}>Sua aplicação foi submetida à Empresa Acme.</p>
                </div>
              ) : modalStep === 1 ? (
                <div className={"step-one-" + seed}>
                  <p className={"text-sm text-gray-600 mb-4"}>Passo 1 de 2: Informações de Contato</p>
                  <div className={"space-y-4 form-fields-" + seed}>
                    <div>
                      <label className={"block text-sm font-medium text-gray-700"}>Nome Completo</label>
                      <input
                        type="text"
                        defaultValue="Nicolas Candidato"
                        className={"mt-1 block w-full border rounded p-2 text-sm border-gray-300"}
                      />
                    </div>
                    <div>
                      <label className={"block text-sm font-medium text-gray-700"}>E-mail</label>
                      <input
                        type="email"
                        defaultValue="candidato@teste.com"
                        className={"mt-1 block w-full border rounded p-2 text-sm border-gray-300"}
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className={"step-two-" + seed}>
                  <p className={"text-sm text-gray-600 mb-4"}>Passo 2 de 2: Revisão e Envio</p>
                  <div className={"p-4 bg-gray-50 rounded border text-sm text-gray-700 review-box-" + seed}>
                    <p>Confirme o envio da sua candidatura para <strong>{selectedJob?.company}</strong>.</p>
                  </div>
                </div>
              )}
            </div>

            {/* Rodapé do Modal com botões de avanço */}
            <div className={"px-6 py-4 bg-gray-50 border-t flex justify-end gap-3 modal-footer-" + seed}>
              {submitted ? (
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
                  onClick={() => setModalStep(2)}
                  className={"px-5 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 btn-next-" + seed}
                >
                  Avançar
                </button>
              ) : (
                <div className={"flex gap-2 btn-group-" + seed}>
                  <button
                    type="button"
                    onClick={() => setModalStep(1)}
                    className={"px-4 py-2 border border-gray-300 rounded font-medium text-gray-700 hover:bg-gray-100"}
                  >
                    Voltar
                  </button>
                  <button
                    type="button"
                    aria-label="Submit application"
                    onClick={() => setSubmitted(true)}
                    className={"px-5 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 btn-submit-" + seed}
                  >
                    Enviar candidatura
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
