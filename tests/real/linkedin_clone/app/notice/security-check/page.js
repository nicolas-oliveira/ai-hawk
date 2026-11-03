"use client";

export default function MarkerOnlyChallenge() {
  return (
    <div
      data-aihawk-challenge="checkpoint"
      data-testid="security-checkpoint"
      className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6"
    >
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          Aviso de Proteção de Conta (URL Neutra)
        </h1>
        <p className="text-sm text-gray-600">
          Esta rota possui URL neutra (/notice/security-check) e aciona parada estrita pelo elemento visível [data-aihawk-challenge].
        </p>
      </div>
    </div>
  );
}
