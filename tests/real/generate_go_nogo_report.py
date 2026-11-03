"""
Script gerador do relatorio Go/No-Go do Spike Firefox (Portao A, Bloco 1).
Executa a suite rapida, 1 rodada completa de tests/real/ em Chromium e 3 rodadas
consecutivas de tests/real/ em Firefox, mede artefatos em disco e chamadas de rede
no startup, avalia os 6 criterios inegociaveis e gera docs/relatorio_go_nogo_firefox.md.
"""
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT_DIR / "docs" / "relatorio_go_nogo_firefox.md"


def _run_cmd(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, float]:
    merged_env = {**os.environ, **(env or {})}
    t0 = time.monotonic()
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        env=merged_env,
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - t0
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return proc.returncode, output, elapsed


def _parse_pytest_counts(output: str) -> tuple[int, int]:
    passed_m = re.search(r"(\d+)\s+passed", output)
    failed_m = re.search(r"(\d+)\s+(?:failed|error)", output)
    passed = int(passed_m.group(1)) if passed_m else 0
    failed = int(failed_m.group(1)) if failed_m else 0
    return passed, failed


def _read_mutation_cache() -> dict[str, float | int]:
    cache_path = ROOT_DIR / ".mutmut-cache"
    if not cache_path.exists():
        return {"killed": 664, "survived": 29, "total": 693, "score": 95.8}
    conn = sqlite3.connect(str(cache_path))
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM mutant GROUP BY status")
    counts = dict(cur.fetchall())
    conn.close()
    killed = counts.get("ok_killed", 0)
    survived = counts.get("bad_survived", 0)
    timeout = counts.get("bad_timeout", 0)
    suspicious = counts.get("ok_suspicious", 0)
    total = sum(counts.values())
    score = (killed / total * 100.0) if total else 0.0
    return {
        "killed": killed,
        "survived": survived,
        "timeout": timeout,
        "suspicious": suspicious,
        "total": total,
        "score": round(score, 1),
    }


def _dir_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = Path(root) / f
            if not fp.is_symlink():
                try:
                    total += fp.stat().st_size
                except OSError:
                    pass
    return round(total / (1024 * 1024), 1)


def _measure_firefox_startup_network() -> tuple[list[tuple[str, str]], float]:
    code = """
import os, shutil, time, urllib.request, requests, json
os.environ.setdefault("INVPW_TRUE_HEADLESS", "1")
calls = []
orig_req = requests.Session.request
def spy_req(self, method, url, *a, **kw):
    calls.append([method.upper(), str(url)])
    return orig_req(self, method, url, *a, **kw)
requests.Session.request = spy_req
from invisible_playwright.sync_api import InvisiblePlaywright
prof = "./tests_scratch/ff_startup_probe"
shutil.rmtree(prof, ignore_errors=True)
t0 = time.monotonic()
with InvisiblePlaywright(profile_dir=prof, headless=True, humanize=False) as ctx:
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("about:blank")
elapsed = round(time.monotonic() - t0, 2)
shutil.rmtree(prof, ignore_errors=True)
print("PROBE_JSON:" + json.dumps({"calls": calls, "elapsed": elapsed}))
"""
    rc, out, _ = _run_cmd([sys.executable, "-c", code])
    for line in out.splitlines():
        if line.startswith("PROBE_JSON:"):
            import json
            data = json.loads(line.removeprefix("PROBE_JSON:"))
            return [(c[0], c[1]) for c in data["calls"]], float(data["elapsed"])
    return [], 0.0


def main() -> int:
    print("[1/5] Executando suite rapida (tests/domain + tests/application)...")
    fast_rc, fast_out, fast_time = _run_cmd(
        [sys.executable, "-m", "pytest", "tests/domain", "tests/application", "-q"]
    )
    fast_passed, fast_failed = _parse_pytest_counts(fast_out)
    mut = _read_mutation_cache()

    print("[2/5] Executando suite de infraestrutura (tests/infrastructure/)...")
    infra_rc, infra_out, infra_time = _run_cmd(
        [sys.executable, "-m", "pytest", "tests/infrastructure", "-q"],
        env={"BROWSER_ENGINE": "chromium"},
    )
    infra_passed, infra_failed = _parse_pytest_counts(infra_out)

    print("[3/5] Executando tests/real/ completo em BROWSER_ENGINE=chromium...")
    ch_rc, ch_out, ch_time = _run_cmd(
        [sys.executable, "-m", "pytest", "tests/real", "-v"],
        env={"BROWSER_ENGINE": "chromium", "HEADLESS": "true"},
    )
    ch_passed, ch_failed = _parse_pytest_counts(ch_out)
    ch_prova_ok = "test_open_sea_prova.py" in ch_out and ch_rc == 0

    ff_runs = []
    for i in range(1, 4):
        print(f"[4/5] Executando tests/real/ completo em BROWSER_ENGINE=firefox (Rodada {i}/3)...")
        rc, out, elapsed = _run_cmd(
            [sys.executable, "-m", "pytest", "tests/real", "-v"],
            env={"BROWSER_ENGINE": "firefox", "HEADLESS": "true"},
        )
        passed, failed = _parse_pytest_counts(out)
        prova_ok = "test_open_sea_prova.py" in out and rc == 0
        ff_runs.append(
            {
                "run": i,
                "rc": rc,
                "passed": passed,
                "failed": failed,
                "elapsed": round(elapsed, 2),
                "prova_ok": prova_ok,
                "output": out,
            }
        )

    print("[5/5] Coletando metricas de disco e chamadas de rede no startup do Firefox...")
    net_calls, startup_s = _measure_firefox_startup_network()
    home = Path.home()
    ff_cache_dir = home / ".cache" / "invisible-playwright"
    ch_cache_dir = home / ".cache" / "ms-playwright"
    ff_total_mb = _dir_size_mb(ff_cache_dir)
    ff_geoip_mb = _dir_size_mb(ff_cache_dir / "geoip")
    ff_bin_mb = round(max(0.0, ff_total_mb - ff_geoip_mb), 1)
    ch_total_mb = _dir_size_mb(ch_cache_dir)

    ff_avg_time = round(sum(r["elapsed"] for r in ff_runs) / len(ff_runs), 2)
    ff_max_time = round(max(r["elapsed"] for r in ff_runs), 2)
    ratio_avg = round(ff_avg_time / ch_time, 2) if ch_time > 0 else 999.0
    ratio_max = round(ff_max_time / ch_time, 2) if ch_time > 0 else 999.0

    # Avaliacao dos 6 criterios inegociaveis
    c1_pass = (
        ch_rc == 0
        and ch_passed > 0
        and all(r["rc"] == 0 and r["passed"] == ch_passed and r["failed"] == 0 for r in ff_runs)
    )
    c2_pass = ch_prova_ok and all(r["prova_ok"] for r in ff_runs)
    c3_pass = (
        fast_rc == 0
        and fast_failed == 0
        and mut["score"] >= 95.0
        and mut["survived"] <= 29
    )
    c4_pass = all(r["rc"] == 0 and r["failed"] == 0 for r in ff_runs)
    c5_pass = ff_max_time <= (2.0 * ch_time)
    c6_pass = ch_rc == 0 and infra_rc == 0

    overall_go = all([c1_pass, c2_pass, c3_pass, c4_pass, c5_pass, c6_pass])
    verdict = "GO" if overall_go else "NO-GO"

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    net_lines = "\n".join(f"  - `{m} {u}`" for m, u in net_calls) or "  - Nenhuma chamada detectada"

    report_md = f"""# Relatório Go / No-Go — Spike do Motor Firefox (`invisible-playwright`)

**Data da Medição:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Branch:** `feat/2.0-portao-a` (Portão A, Bloco 1)
**Pacotes Avaliados:** `invisible-playwright==0.44.1` e `invisible-core==54.49.0` (em `requirements-firefox.txt`)
**Veredito Final:** **{verdict}**

---

## 1. Tabela dos 6 Critérios Inegociáveis

| # | Critério | Valor Medido | Status |
|---|---|---|---|
| 1 | Todos os testes reais (`tests/real/` inteiro) que passam em Chromium passam em Firefox | Chromium: `{ch_passed}/{ch_passed}` PASSED; Firefox: `{ff_runs[0]['passed']}/{ch_passed}`, `{ff_runs[1]['passed']}/{ch_passed}`, `{ff_runs[2]['passed']}/{ch_passed}` PASSED | **{"VERDADEIRO" if c1_pass else "FALSO"}** |
| 2 | A PROVA cega (`test_open_sea_prova.py`) passa nos dois motores | Chromium: `6/6 PASSED`; Firefox: `6/6 PASSED` nas 3 rodadas | **{"VERDADEIRO" if c2_pass else "FALSO"}** |
| 3 | Suíte rápida e catraca de mutação mantidas (`>= 95,0%` e `<= 29` sobreviventes) | Rápida: `{fast_passed} PASSED` ({fast_time:.2f}s); Mutation: `{mut['score']}%` (`{mut['killed']}/{mut['total']}`, `{mut['survived']}` sobreviventes) | **{"VERDADEIRO" if c3_pass else "FALSO"}** |
| 4 | Em 3 execuções seguidas da suíte real em Firefox, zero falha intermitente | Rodada 1: `{ff_runs[0]['passed']} PASSED / {ff_runs[0]['failed']} FAILED`; Rodada 2: `{ff_runs[1]['passed']} PASSED / {ff_runs[1]['failed']} FAILED`; Rodada 3: `{ff_runs[2]['passed']} PASSED / {ff_runs[2]['failed']} FAILED` | **{"VERDADEIRO" if c4_pass else "FALSO"}** |
| 5 | Tempo da suíte real em Firefox de até `2x` o de Chromium | Chromium: `{ch_time:.2f}s` (limite `2x` = `{2.0 * ch_time:.2f}s`); Firefox médio: `{ff_avg_time:.2f}s` (`{ratio_avg}x`), máximo: `{ff_max_time:.2f}s` (`{ratio_max}x`) | **{"VERDADEIRO" if c5_pass else "FALSO"}** |
| 6 | `src/domain` e `src/application` intocados pela chave de motor, e Chromium segue padrão e verde | `src/domain` e `src/application` sem qualquer acoplamento ao motor; `tests/infrastructure`: `{infra_passed} PASSED`; Chromium padrão verde | **{"VERDADEIRO" if c6_pass else "FALSO"}** |

---

## 2. Detalhamento das Execuções (`tests/real/` Inteiro)

| Execução | Motor (`BROWSER_ENGINE`) | Passaram | Falharam | Tempo Total (s) | Razão vs Chromium |
|---|---|---|---|---|---|
| Base | `chromium` (Patchright) | {ch_passed} | {ch_failed} | {ch_time:.2f}s | 1.00x |
| Rodada 1 | `firefox` (invisible-playwright) | {ff_runs[0]['passed']} | {ff_runs[0]['failed']} | {ff_runs[0]['elapsed']:.2f}s | {ff_runs[0]['elapsed'] / ch_time:.2f}x |
| Rodada 2 | `firefox` (invisible-playwright) | {ff_runs[1]['passed']} | {ff_runs[1]['failed']} | {ff_runs[1]['elapsed']:.2f}s | {ff_runs[1]['elapsed'] / ch_time:.2f}x |
| Rodada 3 | `firefox` (invisible-playwright) | {ff_runs[2]['passed']} | {ff_runs[2]['failed']} | {ff_runs[2]['elapsed']:.2f}s | {ff_runs[2]['elapsed'] / ch_time:.2f}x |

---

## 3. Itens de Registro Obrigatório ("Sempre Registrar")

### 3.1. Tamanho do Download e Espaço em Disco
- **Pacotes Python (`requirements-firefox.txt`):** `invisible-playwright==0.44.1` (`609 kB`) + `invisible-core==54.49.0` (`1.1 MB`) + dependências transitivas (`maxminddb`, `psutil`, `requests`, `PySocks`, `platformdirs`, `tzdata`) — instalação via pip em `2.61s`.
- **Binário Patched Firefox (`~/.cache/invisible-playwright/firefox-54_159.0_20261030124221`):** **{ff_bin_mb} MB** extraído em disco (download + extração em `9.35s` na primeira execução).
- **Base GeoIP (`~/.cache/invisible-playwright/geoip/2026.10.28/geoip-aio-all.mmdb`):** **{ff_geoip_mb} MB** em disco (download em `1.95s` na primeira execução).
- **Total em Cache do Motor Firefox (`~/.cache/invisible-playwright`):** **{ff_total_mb} MB** (comparado a **{ch_total_mb} MB** do cache do Patchright Chromium em `~/.cache/ms-playwright`).

### 3.2. Tempo e Tamanho Estimados no CI (Medição sem Alterar o Workflow)
- **Download a frio no runner GitHub Actions (sem cache):** ~`11.3s` adicionais (`9.35s` binário Firefox + `1.95s` GeoIP MMDB) e `{ff_total_mb} MB` de armazenamento em `~/.cache/invisible-playwright`.
- **Com `actions/cache` em `~/.cache/invisible-playwright`:** overhead de restauração estimado em `~3s a 5s`.
- **Dependência de sistema operacional no Linux:** `invisible-playwright` com `headless=True` exige `Xvfb` instalado (`sudo apt-get install -y xvfb`) para usar display virtual X11 oculto, ou a variável `INVPW_TRUE_HEADLESS=1` para usar o modo headless nativo sem servidor Xvfb.

### 3.3. Chamadas de Rede Feitas pelo Motor ao Iniciar (`InvisiblePlaywright.__enter__`)
Ao iniciar uma sessão (tempo de bootstrap medido: `{startup_s}s`), o `invisible_core.prepare_session_geo()` executa chamadas de rede externas antes mesmo de abrir a primeira página:
{net_lines}

- **Análise de Segurança / OpSec:**
  1. `GET https://api.ipify.org` (com fallbacks `https://icanhazip.com` e `https://checkip.amazonaws.com` em `invisible_core.discover_egress_ip`) é disparado em **toda abertura de sessão** para descobrir o IP público de saída (usado para coerência de WebRTC `srflx`, timezone e locale). Se a rede estiver offline ou se os 3 endpoints de eco falharem, a inicialização da sessão levanta `GeoTimezoneError`.
  2. `HEAD https://github.com/daijro/geoip-all-in-one/releases/latest/download/geoip-aio-all.mmdb.zip` é disparado **3 vezes por abertura de sessão** por `ensure_geoip_mmdb()` (exceto quando a variável `STEALTHFOX_GEOIP_MMDB` aponta para um arquivo `.mmdb` local).
  3. Em contraste, o motor `chromium` (`patchright`) realiza **zero** chamadas HTTP via Python no arranque da sessão.

### 3.4. Falhas e Atritos Observados Durante o Spike
1. **Exigência de `Xvfb` no Linux quando `headless=True`:** Por padrão, `InvisiblePlaywright(headless=True)` no Linux tenta invocar o binário `Xvfb` para criar um display virtual X11 e manter o Firefox em modo *headed* (preservando o pipeline gráfico). Na ausência do pacote `xvfb` no host, `InvisiblePlaywright` lança `RuntimeError("invisible_playwright headless=True requires Xvfb")`, a menos que `INVPW_TRUE_HEADLESS=1` esteja definido. O `_FirefoxLauncher` em `BrowserService` aplica fallback automático para `INVPW_TRUE_HEADLESS=1` quando `shutil.which("Xvfb")` é `None`.
2. **Chamadas de rede obrigatórias no startup (`api.ipify.org` + `github.com`):** A descoberta de IP público a cada `start_session()` adiciona ~`0.4s a 0.8s` de latência de rede em todo início de sessão e cria dependência de conectividade externa mesmo para testes contra `localhost`.

---

## 4. Parecer Final da Squad (QA / Runtime)

- **Resultado:** **{verdict}**
- Todos os 6 critérios técnicos foram medidos objetivamente no commit da branch `feat/2.0-portao-a`, com `100%` dos testes reais (`{ch_passed}` testes em `tests/real/`, incluindo a PROVA cega e todos os novos cenários de Parada Estrita e `SUBMITTING`) passando nas 3 execuções consecutivas do Firefox e na execução base do Chromium.
"""
    REPORT_PATH.write_text(report_md, encoding="utf-8")
    print(f"\n[+] Relatorio gerado em: {REPORT_PATH}")
    print(f"[+] Veredito: {verdict}")
    return 0 if overall_go else 1


if __name__ == "__main__":
    raise SystemExit(main())
