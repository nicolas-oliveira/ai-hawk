"use client";

export default function UnusualTrafficPage() {
  return (
    <div
      data-aihawk-challenge="unusual_traffic"
      data-testid="unusual-traffic-notice"
      className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6"
    >
      <div className="max-w-lg w-full bg-white rounded-lg shadow-md p-8">
        <h1 className="text-xl font-bold text-gray-900 mb-3">
          Sobre esta página
        </h1>
        <p className="text-sm text-gray-700 mb-4 leading-relaxed">
          Nossos sistemas detectaram tráfego incomum na sua rede de computadores.
          Esta página verifica se é realmente você que está enviando as solicitações,
          e não um robô.
        </p>
        <p className="text-xs text-gray-500 font-mono">
          Endereço IP: 127.0.0.1 | Horário: 2026-11-03T13:00:00Z
        </p>
      </div>
    </div>
  );
}
