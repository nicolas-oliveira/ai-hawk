"use client";

export default function CaptchaPage() {
  return (
    <div
      data-aihawk-challenge="captcha"
      data-testid="captcha-challenge"
      className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6"
    >
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          Verificação de Segurança (CAPTCHA)
        </h1>
        <p className="text-sm text-gray-600 mb-6">
          Complete o desafio visual para confirmar que você é um humano.
        </p>
        <div
          data-testid="hcaptcha-container"
          className="border-2 border-dashed border-gray-300 rounded p-6 bg-gray-50"
        >
          <p className="text-xs text-gray-500 font-mono">[CAPTCHA CHALLENGE WIDGET]</p>
        </div>
      </div>
    </div>
  );
}
