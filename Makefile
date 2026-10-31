# Atalhos do AIHawk (equivalente ao "npm run"). Uso: make <alvo>
PY := .venv/bin/python

.PHONY: test test-unit pre-pr demo

# Suite completa: unitarios + infraestrutura + Chromium real + clone Next.js hostil
test:
	$(PY) -m pytest tests/domain tests/application -v
	HEADLESS=true $(PY) -m pytest tests/infrastructure/ tests/real/ -v

# Rapido, sem navegador: apenas testes unitarios de dominio e aplicacao (mocks)
test-unit:
	$(PY) -m pytest tests/domain tests/application -q

# Antes de abrir/atualizar PR: testes reais (Chromium) + borda + suite completa
pre-pr:
	HEADLESS=true $(PY) -m pytest tests/real/ tests/infrastructure/ -v
	HEADLESS=true $(PY) -m pytest -q

# Demo visual: sobe o clone Next.js estilizado (porta 3000), abre o Chromium visivel e roda o robo
demo:
	@$(PY) -c "$$(printf '%s\n' \
		'import os, shutil, subprocess, tempfile, time, urllib.request' \
		'from src.infrastructure.browser_service import BrowserService' \
		'from src.application.app_service import AppService' \
		'from src.application.app_controller import AppController' \
		'from src.application.dtos.search_request import SearchRequest, SELECTOR_PROFILES' \
		'clone_dir = os.path.abspath("tests/real/linkedin_clone")' \
		'url = os.getenv("CLONE_URL", "http://localhost:3000")' \
		'def is_up():' \
		'    try: return urllib.request.urlopen(url, timeout=2).status < 400' \
		'    except Exception: return False' \
		'proc = None if is_up() else subprocess.Popen(["npx", "next", "start", "-p", "3000"], cwd=clone_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)' \
		'deadline = time.time() + 20' \
		'while not is_up() and time.time() < deadline: time.sleep(0.3)' \
		'headless = os.getenv("DEMO_HEADLESS", "false").lower() in ("true", "1", "yes")' \
		'tmp = tempfile.mkdtemp()' \
		'browser = BrowserService(platform="linkedin_clone", headless=headless, channel="chromium", session_root_dir=tmp)' \
		'browser.start_session()' \
		'try:' \
		'    req = SearchRequest(platform="linkedin_clone", static_urls=[url], selectors=SELECTOR_PROFILES["linkedin_clone"], max_applications=2)' \
		'    print(AppController(AppService(browser), reports_dir=os.path.join(tmp, "reports")).execute(req))' \
		'    if not headless: input("\nResultado acima no Clone Next.js. Pressione ENTER para fechar a janela...")' \
		'finally:' \
		'    browser.close()' \
		'    if proc: proc.terminate()' \
		'    shutil.rmtree(tmp, ignore_errors=True)' \
	)"
