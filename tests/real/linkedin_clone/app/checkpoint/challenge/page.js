"use client";

export default function CheckpointChallenge() {
  return (
    <div
      data-aihawk-challenge="checkpoint"
      data-testid="security-checkpoint"
      className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6"
    >
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          Security Checkpoint Challenge
        </h1>
        <p className="text-sm text-gray-600 mb-6">
          Confirme sua identidade antes de prosseguir com a sessão.
        </p>
      </div>
    </div>
  );
}
