# Relatório Go / No-Go — Spike do Motor Firefox (`invisible-playwright`)

**Data da Medição:** 2026-11-03 14:11:05
**Branch:** `feat/2.0-portao-a` (Portão A, Bloco 1)
**Pacotes Avaliados:** `invisible-playwright==0.44.1` e `invisible-core==54.49.0` (em `requirements-firefox.txt`)
**Veredito Final:** **GO**

---

## 1. Tabela dos 6 Critérios Inegociáveis

| # | Critério | Valor Medido | Status |
|---|---|---|---|
| 1 | Todos os testes reais (`tests/real/` inteiro) que passam em Chromium passam em Firefox | Chromium: `32/32` PASSED; Firefox: `32/32`, `32/32`, `32/32` PASSED | **VERDADEIRO** |
| 2 | A PROVA cega (`test_open_sea_prova.py`) passa nos dois motores | Chromium: `6/6 PASSED`; Firefox: `6/6 PASSED` nas 3 rodadas | **VERDADEIRO** |
| 3 | Suíte rápida e catraca de mutação mantidas (`>= 95,0%` e `<= 29` sobreviventes) | Rápida: `341 PASSED` (0.44s); Mutation: `95.8%` (`664/693`, `29` sobreviventes) | **VERDADEIRO** |
| 4 | Em 3 execuções seguidas da suíte real em Firefox, zero falha intermitente | Rodada 1: `32 PASSED / 0 FAILED`; Rodada 2: `32 PASSED / 0 FAILED`; Rodada 3: `32 PASSED / 0 FAILED` | **VERDADEIRO** |
| 5 | Tempo da suíte real em Firefox de até `2x` o de Chromium | Chromium: `352.82s` (limite `2x` = `705.64s`); Firefox médio: `370.97s` (`1.05x`), máximo: `372.18s` (`1.05x`) | **VERDADEIRO** |
| 6 | `src/domain` e `src/application` intocados pela chave de motor, e Chromium segue padrão e verde | `src/domain` e `src/application` sem qualquer acoplamento ao motor; `tests/infrastructure`: `19 PASSED`; Chromium padrão verde | **VERDADEIRO** |

---

## 2. Detalhamento das Execuções (`tests/real/` Inteiro)

| Execução | Motor (`BROWSER_ENGINE`) | Passaram | Falharam | Tempo Total (s) | Razão vs Chromium |
|---|---|---|---|---|---|
| Base | `chromium` (Patchright) | 32 | 0 | 352.82s | 1.00x |
| Rodada 1 | `firefox` (invisible-playwright) | 32 | 0 | 372.02s | 1.05x |
| Rodada 2 | `firefox` (invisible-playwright) | 32 | 0 | 372.18s | 1.05x |
| Rodada 3 | `firefox` (invisible-playwright) | 32 | 0 | 368.72s | 1.05x |

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
- **Dependência de sistema operacional no Linux:** `invisible-playwright` com `headless=True` exige `Xvfb` instalado (`sudo apt-get install -y xvfb`) para usar display virtual X11 oculto, ou a variável `INVPW_TRUE_HEADLESS=1` para usar o modo headless nativo sem servidor Xvfb.

### 3.3. Chamadas de Rede Feitas pelo Motor ao Iniciar (`InvisiblePlaywright.__enter__`)
Ao iniciar uma sessão (tempo de bootstrap medido: `2.97s`), o `invisible_core.prepare_session_geo()` executa chamadas de rede externas antes mesmo de abrir a primeira página:
  - `GET https://api.ipify.org`
  - `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip`
  - `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip`
  - `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip`

- **Análise de Segurança / OpSec:**
  1. `GET https://api.ipify.org` (com fallbacks `https://icanhazip.com` e `https://checkip.amazonaws.com` em `invisible_core.discover_egress_ip`) é disparado em **toda abertura de sessão** para descobrir o IP público de saída (usado para coerência de WebRTC `srflx`, timezone e locale). Se a rede estiver offline ou se os 3 endpoints de eco falharem, a inicialização da sessão levanta `GeoTimezoneError`.
  2. `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip` é disparado **3 vezes por abertura de sessão** por `ensure_geoip_mmdb()` (exceto quando a variável `STEALTHFOX_GEOIP_MMDB` aponta para um arquivo `.mmdb` local).
  3. Em contraste, o motor `chromium` (`patchright`) realiza **zero** chamadas HTTP via Python no arranque da sessão.

### 3.4. Falhas e Atritos Observados Durante o Spike
1. **Exigência de `Xvfb` no Linux quando `headless=True`:** Por padrão, `InvisiblePlaywright(headless=True)` no Linux tenta invocar o binário `Xvfb` para criar um display virtual X11 e manter o Firefox em modo *headed* (preservando o pipeline gráfico). Na ausência do pacote `xvfb` no host, `InvisiblePlaywright` lança `RuntimeError("invisible_playwright headless=True requires Xvfb")`, a menos que `INVPW_TRUE_HEADLESS=1` esteja definido. O `_FirefoxLauncher` em `BrowserService` aplica fallback automático para `INVPW_TRUE_HEADLESS=1` quando `shutil.which("Xvfb")` é `None`.
2. **Chamadas de rede obrigatórias no startup (`api.ipify.org` + `github.com`):** A descoberta de IP público a cada `start_session()` adiciona ~`0.4s a 0.8s` de latência de rede em todo início de sessão e cria dependência de conectividade externa mesmo para testes contra `localhost`.

---

## 4. Parecer Final da Squad (QA / Runtime)

- **Resultado:** **GO**
- Todos os 6 critérios técnicos foram medidos objetivamente no commit da branch `feat/2.0-portao-a`, com `100%` dos testes reais (`32` testes em `tests/real/`, incluindo a PROVA cega e todos os novos cenários de Parada Estrita e `SUBMITTING`) passando nas 3 execuções consecutivas do Firefox e na execução base do Chromium.
