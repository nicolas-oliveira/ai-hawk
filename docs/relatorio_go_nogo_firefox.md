# Relatório Go / No-Go — Spike do Motor Firefox (`invisible-playwright`) — Portão A (Bloco 1.1)

**Data da Medição:** 2026-11-03 21:07:01
**Branch:** `feat/2.0-portao-a` (Portão A, Bloco 1.1 — Correções do GO com Condições)
**Pacotes Avaliados:** `invisible-playwright==0.44.1` e `invisible-core==54.49.0` (em `requirements-firefox.txt`)
**Proveniencia do Mutation Score:** `96,1% (689/717, 28 sobreviventes, 0 novos, mutante 140 morto) — medido do zero pelo Claude no commit '81ec6e4'`
**Veredito Final:** **GO**

---

## 1. Tabela dos 6 Critérios Inegociáveis

| # | Critério | Valor Medido (Código Final Bloco 1.1) | Status |
|---|---|---|---|
| 1 | Todos os testes reais (`tests/real/` inteiro) que passam em Chromium passam em Firefox | Chromium: `39/39` PASSED; Firefox (`xvfb`): `39/39`, `39/39`, `39/39` PASSED | **VERDADEIRO** |
| 2 | A PROVA cega (`test_open_sea_prova.py`) passa nos dois motores | Chromium: `6/6 PASSED`; Firefox (`xvfb`): `6/6 PASSED` nas 3 rodadas | **VERDADEIRO** |
| 3 | Suíte rápida e catraca de mutação mantidas (`>= 95,0%` e `<= 29` sobreviventes) | Rápida: `355 PASSED` (0.48s); Mutation: `96,1% (689/717, 28 sobreviventes, 0 novos, mutante 140 morto) — medido do zero pelo Claude no commit '81ec6e4'` | **VERDADEIRO** |
| 4 | Em 3 execuções seguidas da suíte real em Firefox (modo `xvfb`), zero falha intermitente | Rodada 1: `39 PASSED / 0 FAILED`; Rodada 2: `39 PASSED / 0 FAILED`; Rodada 3: `39 PASSED / 0 FAILED` | **VERDADEIRO** |
| 5 | Tempo da suíte real em Firefox de até `2x` o de Chromium | Chromium: `743.37s` (limite `2x` = `1486.74s`); Firefox (`xvfb`) médio: `769.10s` (`1.03x`), máximo: `772.95s` (`1.04x`) | **VERDADEIRO** |
| 6 | `src/domain` e `src/application` intocados pela chave de motor, e Chromium segue padrão e verde | `src/domain` e `src/application` sem acoplamento ao motor; `tests/infrastructure`: `27 PASSED` (7.51s); Chromium padrão (`DEFAULT_VISIBILITY_TIMEOUT_MS = 3000`) verde | **VERDADEIRO** |

---

## 2. Detalhamento das Execuções e Metadados de Runtime por Modo (`tests/real/` Inteiro)

### 2.1. Execuções no Código Final do Bloco 1.1 (`DEFAULT_VISIBILITY_TIMEOUT_MS = 3000`)

| Execução | Motor Pedido (`BROWSER_ENGINE`) | Modo Efetivo | Caminho do `Xvfb` | Versão do Navegador | `navigator.userAgent` Observado | Passaram | Falharam | Tempo (s) | Razão vs Chromium |
|---|---|---|---|---|---|---|---|---|---|
| Base Chromium | `chromium` | `headless` | `/usr/bin/Xvfb` | `153.0.8010.12` | `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/153.0.8010.12 Safari/537.36` | 39 | 0 | 743.37s | 1.00x |
| Firefox Rodada 1 | `firefox` | `xvfb` | `/usr/bin/Xvfb` | `159.0` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:159.0) Gecko/20100101 Firefox/159.0` | 39 | 0 | 772.95s | 1.04x |
| Firefox Rodada 2 | `firefox` | `xvfb` | `/usr/bin/Xvfb` | `159.0` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:159.0) Gecko/20100101 Firefox/159.0` | 39 | 0 | 769.52s | 1.04x |
| Firefox Rodada 3 | `firefox` | `xvfb` | `/usr/bin/Xvfb` | `159.0` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:159.0) Gecko/20100101 Firefox/159.0` | 39 | 0 | 764.84s | 1.03x |

### 2.2. Comparativo por Modo do Firefox (`xvfb` vs `headless-real` do Bloco 1)

| Métrica | Chromium (`headless`) — Bloco 1.1 | Firefox (`xvfb`) — Bloco 1.1 | Firefox (`headless-real`, ref. Bloco 1) |
|---|---|---|---|
| Modo Efetivo | `headless` | `xvfb` | `headless-real` (`INVPW_TRUE_HEADLESS=1`) |
| Binário `Xvfb` | `/usr/bin/Xvfb` | `/usr/bin/Xvfb` | Ausente na medição do Bloco 1 |
| Versão do Motor | `153.0.8010.12` | `159.0` | `159.0` |
| Testes Passando (`tests/real/`) | `39/39` | `39/39` (3/3 rodadas) | `32/32` (3/3 rodadas no Bloco 1) |
| Tempo Médio (`tests/real/`) | `743.37s` | `769.10s` (`1.03x`) | `370.97s` (`1.05x` no Bloco 1) |

---

## 3. Itens de Registro Obrigatório ("Sempre Registrar")

### 3.1. Tamanho do Download e Espaço em Disco
- **Pacotes Python (`requirements-firefox.txt`):** `invisible-playwright==0.44.1` (`609 kB`) + `invisible-core==54.49.0` (`1.1 MB`) + dependências transitivas (`maxminddb`, `psutil`, `requests`, `PySocks`, `platformdirs`, `tzdata`) — instalação via pip em `2.61s`.
- **Binário Patched Firefox (`~/.cache/invisible-playwright/firefox-54_159.0_20261030124221`):** **543.6 MB** extraído em disco (download + extração em `9.35s` na primeira execução).
- **Base GeoIP (`~/.cache/invisible-playwright/geoip/2026.10.28/geoip-aio-all.mmdb`):** **115.0 MB** em disco (download em `1.95s` na primeira execução).
- **Total em Cache do Motor Firefox (`~/.cache/invisible-playwright`):** **658.6 MB** (comparado a **651.2 MB** do cache do Patchright Chromium em `~/.cache/ms-playwright`).

### 3.2. Tempo e Tamanho Estimados no CI (Medição sem Alterar o Workflow)
- **Download a frio no runner GitHub Actions (sem cache):** ~`11.3s` adicionais (`9.35s` binário Firefox + `1.95s` GeoIP MMDB) e `658.6 MB` de armazenamento em `~/.cache/invisible-playwright`.
- **Com `actions/cache` em `~/.cache/invisible-playwright`:** overhead de restauração estimado em `~3s a 5s`.
- **Dependência de sistema operacional no Linux:** `invisible-playwright` com `headless=True` exige `Xvfb` instalado (`sudo apt-get install -y xvfb`, presente em `/usr/bin/Xvfb`) para usar display virtual X11 oculto. Sem `Xvfb`, o `BrowserService` recusa iniciar em modo silencioso e exige `firefox_headless_mode='true_headless'` explícito com aviso no log.

### 3.3. Chamadas de Rede Feitas pelo Motor ao Iniciar (`InvisiblePlaywright.__enter__`)
Ao iniciar uma sessão em modo `xvfb` (tempo de bootstrap medido: `2.8s`), o `invisible_core.prepare_session_geo()` executa chamadas de rede externas antes mesmo de abrir a primeira página:
  - `GET https://api.ipify.org`
  - `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip`
  - `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip`
  - `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip`

- **Análise de Segurança / OpSec:**
  1. `GET https://api.ipify.org` (com fallbacks `https://icanhazip.com` e `https://checkip.amazonaws.com` em `invisible_core.discover_egress_ip`) é disparado em **toda abertura de sessão** para descobrir o IP público de saída (usado para coerência de WebRTC `srflx`, timezone e locale). Se a rede estiver offline ou se os 3 endpoints de eco falharem, a inicialização da sessão levanta `GeoTimezoneError`.
  2. `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip` é disparado **3 vezes por abertura de sessão** por `ensure_geoip_mmdb()` (exceto quando a variável `STEALTHFOX_GEOIP_MMDB` aponta para um arquivo `.mmdb` local).
  3. Em contraste, o motor `chromium` (`patchright`) realiza **zero** chamadas HTTP via Python no arranque da sessão.

### 3.4. Falhas e Atritos Observados e Endurecimentos Aplicados no Bloco 1.1
1. **Exigência Estrita de `Xvfb` no Linux quando `headless=True` (Passo A4):** O fallback silencioso para `INVPW_TRUE_HEADLESS=1` foi removido. Agora, se `headless=True` no Firefox e `/usr/bin/Xvfb` não estiver instalado, o `BrowserService` falha imediatamente com `RuntimeError` instruindo a instalar `xvfb` ou habilitar `firefox_headless_mode='true_headless'` explicitamente (que emite `WARNING` e restaura `os.environ` ao fechar).
2. **Isolamento de Perfil por Motor (Passo A3) e Ancoragem na Raiz (Passo A2):** Perfis de sessão de `chromium` (`<root>/<platform>`) e `firefox` (`<root>/<platform>-firefox`) ficam em diretórios irmãos ancorados em `get_project_root()`, impedindo colisão de artefatos SQLite/LevelDB entre motores.
3. **Guarda de Identidade do Motor nas Fixtures Reais (Passo A6):** As fixtures reais leem `navigator.userAgent` na abertura da sessão e falham alto se `BROWSER_ENGINE` não corresponder ao motor efetivamente carregado (`"Firefox"` vs `"Chrome"`).

---

## 4. Parecer Final da Squad (QA / Runtime)

- **Resultado:** **GO**
- Todos os 6 critérios técnicos foram medidos objetivamente no código final do Bloco 1.1 (`feat/2.0-portao-a`), com `100%` dos testes reais (`39` testes em `tests/real/`, incluindo a PROVA cega e todos os cenários `C1` a `C4` de envio, `SUBMITTING`, `MANUAL_REVIEW` e Parada Estrita) passando na execução em `chromium` e nas 3 execuções consecutivas em `firefox` sob `Xvfb` (`/usr/bin/Xvfb`).

---

## 5. Linha de Base A/B Consolidada — Portão A (Bloco 2 — 47 Testes Reais sob Xvfb)

**Data da Medição:** 2026-11-04  
**Branch:** `feat/2.0-portao-a` (Portão A, Bloco 2)  
**Ambiente:** Ubuntu 24.04.5 LTS, Python 3.14.4, `/usr/bin/Xvfb` (:99), clone Next.js hostil em `:3000`

### 5.1. Comparativo de Desempenho e Cobertura E2E (`tests/real/` Inteiro — 47 Testes)

| Motor Avaliado | Modo Efetivo | Display Virtual | Testes Coletados | Passaram | Falharam | Tempo Total | Razão vs Chromium | Status Linha de Base |
|---|---|---|---|---|---|---|---|---|
| **Chromium** (`patchright`) | `headless=True` (`channel="chrome"`) | Xvfb (`:99`) | 47 | 47 | 0 | **1059.48s** (17m 39s) | **1.00x** | **BASELINE DEFINIDA** |
| **Firefox** (`invisible-playwright`) | `headless=True` (`xvfb`) | Xvfb (`:99`) | 47 | 47 | 0 | **938.86s** (15m 38s) | **0.89x** (<= 2.0x) | **BASELINE DEFINIDA** |

### 5.2. Novos Cenários Validados nos Dois Motores (Bloco 2)
1. **Verificação de Estado Aplicado Instantâneo (`job_shows_applied`):** Ignora modal e marca `ALREADY_APPLIED` sem abrir candidatura em ambos os motores.
2. **Confirmação Dupla de Envio (`C1` e `C2`):**
   - Modal fecha com confirmação E container marca aplicado -> `APPLIED`.
   - Confirmação emitida mas container NÃO marca aplicado -> `MANUAL_REVIEW` (`CONFIRMATION_WITHOUT_STATE`).
   - Container marca aplicado sem confirmação do modal -> `MANUAL_REVIEW` (`STATE_WITHOUT_CONFIRMATION`).
3. **Trava de Identidade (`A1`):** Validação real de bloqueio imediato para destinos externos em modo sem display real ou proibido.
4. **PROVA Cega (6/6 Testes):** 100% verde em Chromium e 100% verde em Firefox.
5. **Conclusão:** Paridade comportamental estrita mantida entre os dois motores sob Xvfb. A suíte real está homologada e pronta como linha de base A/B para o Portão B.

