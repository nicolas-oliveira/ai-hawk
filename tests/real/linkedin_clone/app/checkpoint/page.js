"use client";

export default function Checkpoint() {
  return (
    <div
      data-aihawk-challenge="checkpoint"
      data-testid="security-checkpoint"
      className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6"
    >
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
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
            [SIMULACAO DE DESAFIO / CHECKPOINT DE SEGURANCA]
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
