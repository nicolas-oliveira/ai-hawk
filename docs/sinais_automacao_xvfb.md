# Levantamento de Sinais de Automação do Navegador sob Xvfb

Data: 2026-11-04  
Responsável: Antigravity (Agy — QA, Runtime & Infraestrutura)  
Escopo: Portão A, Bloco 2 (Passo A1)  
Ambiente: Ubuntu 24.04.5 LTS, `/usr/bin/Xvfb` instalado, Python 3.12 / 3.14  
Motores avaliados: Chromium (Patchright) e Firefox (`invisible-playwright`) em janela real sob display virtual Xvfb vs Clone Local (`127.0.0.1:3000`).

---

## 1. Tabela Comparativa de Sinais Medidos no DOM / Runtime

| Sinal Inspecionado | Chromium (`effective_mode='xvfb'`) | Firefox (`effective_mode='xvfb'`) | Veredito | Verificável na Trava de Identidade? |
|---|---|---|---|---|
| `effective_mode` | `xvfb` (janela real em display virtual) | `xvfb` (janela real em display virtual) | Não denuncia | **Sim**: modo diferente de `xvfb` em alvo externo bloqueia o bot na hora. |
| Presença de `/usr/bin/Xvfb` | Presente (`/usr/bin/Xvfb`) | Presente (`/usr/bin/Xvfb`) | Não denuncia | **Sim**: ausência do binário recusa a inicialização para alvos externos. |
| `navigator.webdriver` | `False` (Patchright patch C++) | `False` (`invisible-playwright` patch) | Não denuncia | **Sim**: se retornar `True`, recusa imediata. |
| `navigator.userAgent` | `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:159.0) Gecko/20100101 Firefox/159.0` | Não denuncia | **Sim**: presença de `HeadlessChrome` ou contradição de motor recusa na hora. |
| `navigator.plugins.length` | `5` (plugins reais de Chrome headed) | `5` (plugins reais de Firefox headed) | Não denuncia | **Sim**: `length == 0` (típico de headless padrão) recusa na hora. |
| `navigator.languages` | `['pt-BR', 'pt', 'en-US', 'en']` | `['pt-BR', 'pt', 'en-US', 'en']` | Não denuncia | Não (varia por localidade/perfil, não binário). |
| Geometria de Janela (`outerWidth` x `outerHeight`) | `1288 x 851` (borda e toolbar reais) | `2575 x 1407` (geometria real simulada) | Não denuncia | Indireto (medido e logado; em headless padrão fica 0 ou igual ao inner). |
| Globais de automação (`cdc_*`, `__playwright`, etc.) | `[]` (vazio) | `[]` (vazio) | Não denuncia | Verificável em runtime. |
| WebGL (`UNMASKED_RENDERER_WEBGL`) | `None` / Software Mesa (sem GPU física) | `ANGLE (AMD, Radeon HD 3200 Graphics Direct3D11 vs_5_0 ps_5_0)` | **Atenção (Achado)** | Documentado abaixo para decisão do PO no Portão B. |

---

## 2. Achado para Decisão do Nicolas (Decisão 3 do PO — Tolerância Zero para Defeitos de Produto)

* **Achado no WebGL do Chromium sob Xvfb:**
  * O motor Firefox (`invisible-playwright`) spooferiza programaticamente uma GPU física realista (`ANGLE (AMD, Radeon HD 3200 Graphics...)`).
  * O motor Chromium (Patchright), ao rodar sob Xvfb puro em servidor sem placa de vídeo dedicada (GPU física), reporta `None` ou renderizador de software (`llvmpipe` / `software rasterizer`).
  * *Impacto comercial:* Sistemas anti-bot de nível 3 (DataDome avançado / Cloudflare Turnstile) consultam a extensão `WEBGL_debug_renderer_info`. Um renderizador `None` ou `llvmpipe` denuncia execução em servidor cloud / VPS.
  * *Encaminhamento:* Este achado não impede a trava do Portão A (que opera contra o clone local), mas fica registrado formalmente para a Diretoria/Nicolas definir a inclusão de flags de emulação de GPU ANGLE (`--use-gl=angle`, `--use-angle=swiftshader`) no Spike do Portão B.

---

## 3. Sinais que NÃO Puderam ser Medidos Sem Rede Externa (Reserva para o Portão B)

Conforme determinado pela regra do Bloco 2, os seguintes sinais só se manifestam ou só podem ser medidos com tráfego externo e servidor remoto, ficando categoricamente reservados para o 1º passo do Portão B:

1. **TLS Fingerprint (JA3 / JA4):** A ordem das cifras, extensões TLS (SNI, ALPN, elliptic curves) e padding só é observada no handshake TLS pelo servidor de destino.
2. **HTTP/2 SETTINGS Frames:** Parâmetros de frames HTTP/2 (`SETTINGS_HEADER_TABLE_SIZE`, `SETTINGS_INITIAL_WINDOW_SIZE`, `PRIORITY`) entregues pelo stack de rede.
3. **Vazamento de IP / WebRTC STUN (srflx leak):** Validação de que o IP reportado pelo navegador bate exatamente com o IP do proxy de saída, sem vazar o IP real do host via candidatos WebRTC STUN/TURN.
4. **Chamadas de Rede de Boot do Driver:** Requisições de inicialização automática feitas por bibliotecas em background (ex: consultas de IP em `ipify`, checagens de versão no GitHub).

---

## 4. Regras da Trava de Identidade (`BrowserService.verify_runtime_identity`)

1. **Clone local (`localhost` e `127.0.0.1`):** Modo permissivo para testes unitários e de integração locais. Registra o relatório de identidade em log e libera a execução.
2. **Alvo externo (`target_url` com host remoto):**
   * Bloqueia (`RuntimeError`) se `effective_mode != 'xvfb'`.
   * Bloqueia (`RuntimeError`) se `/usr/bin/Xvfb` não existir.
   * Bloqueia (`RuntimeError`) se `HeadlessChrome` estiver presente no User-Agent.
   * Bloqueia (`RuntimeError`) se `navigator.webdriver` for verdadeiro.
   * Bloqueia (`RuntimeError`) se `navigator.plugins.length == 0`.
   * Bloqueia (`RuntimeError`) se o motor não for reconhecido ou o User-Agent contradisser o motor configurado.
   * Nenhuma variável de ambiente (`.env`) é capaz de desabilitar ou enfraquecer essa trava.
