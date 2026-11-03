"use client";

export default function VerifyPhonePage() {
  return (
    <div
      data-aihawk-challenge="phone_verification"
      data-testid="phone-verification-challenge"
      className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6"
    >
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          Verificação de Telefone Obrigatória
        </h1>
        <p className="text-sm text-gray-600 mb-6">
          Para proteger sua conta, insira seu número de celular para receber um código via SMS.
        </p>
      </div>
    </div>
  );
}
