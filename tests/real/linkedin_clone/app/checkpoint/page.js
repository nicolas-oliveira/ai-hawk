"use client";

export default function Checkpoint() {
  return (
    <div
      data-testid="security-checkpoint"
      className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6"
    >
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          Verificação de Segurança / Security Checkpoint
        </h1>
        <p className="text-sm text-gray-600 mb-6">
          Detectamos atividade incomum a partir de sua rede. Por favor, resolva o
          desafio de segurança para continuar navegando.
        </p>
        <div
          data-testid="captcha-challenge"
          className="border-2 border-dashed border-gray-300 rounded p-6 bg-gray-50 mb-6"
        >
          <p className="text-xs text-gray-500 font-mono">
            [SIMULACAO DE DESAFIO / CAPTCHA INTERATIVO]
          </p>
        </div>
        <button
          type="button"
          disabled
          className="w-full py-2 px-4 bg-gray-300 text-gray-500 font-semibold rounded cursor-not-allowed"
        >
          Verificar Humano
        </button>
      </div>
    </div>
  );
}
