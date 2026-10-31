import threading
import shutil
import os
import pytest
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Tuple
from src.infrastructure.browser_service import BrowserService


# ==============================================================================
# SANTUARIO DO PATCHRIGHT - DEFINICAO DO SERVIDOR DE ARMADILHA DO DOM REAL
# ==============================================================================

HTML_SEARCH_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Search Simulation</title>
    <style>
        #container {
            height: 150px;
            overflow-y: scroll;
            border: 2px solid #0a66c2;
            padding: 10px;
        }
        .job-card-container {
            height: 120px;
            margin-bottom: 10px;
            background: #f3f3f3;
            padding: 5px;
        }
    </style>
</head>
<body>
    <h1>Simulacao Real de Busca</h1>
    <div id="container" class="jobs-search-results-list">
        <div class="job-card-container">
            <a class="job-card-link" href="{base_url}/jobs/view/201/?refId=init_1">Vaga 201 - Direta</a>
            <span class="title">Engenheiro Python</span>
            <span class="company">TechCorp</span>
        </div>
        <div class="job-card-container">
            <a class="job-card-link" href="{base_url}/jobs/view/202/?trackingId=init_2">Vaga 202 - CSS Trap</a>
            <span class="title">Backend Developer</span>
            <span class="company">SecureSystems</span>
        </div>
    </div>

    <script>
        // Lazy Loading Real com Scroll
        let loadedMore = false;
        const container = document.getElementById('container');
        container.addEventListener('scroll', () => {
            if (!loadedMore && container.scrollTop > 30) {
                loadedMore = true;
                const card3 = document.createElement('div');
                card3.className = 'job-card-container';
                card3.innerHTML = '<a class="job-card-link" href="{base_url}/jobs/view/203/?refId=lazy_3">Vaga 203 - Complexa</a><span class="title">Data Engineer</span><span class="company">BigData</span>';
                container.appendChild(card3);

                const card4 = document.createElement('div');
                card4.className = 'job-card-container';
                card4.innerHTML = '<a class="job-card-link" href="{base_url}/jobs/view/204/?refId=lazy_4">Vaga 204 - Multi-Step</a><span class="title">DevOps</span><span class="company">CloudNative</span>';
                container.appendChild(card4);

                const card5 = document.createElement('div');
                card5.className = 'job-card-container';
                card5.innerHTML = '<a class="job-card-link" href="{base_url}/jobs/view/205/">Vaga 205 - Externa</a><span class="title">Frontend</span><span class="company">WebSoft</span>';
                container.appendChild(card5);
            }
        });
    </script>
</body>
</html>
"""

HTML_JOB_201_ASYNC_MODAL = """<!DOCTYPE html>
<html>
<head><title>Vaga 201 - Transicao Assincrona</title></head>
<body>
    <h2>Senior Python - TechCorp</h2>
    <button class="jobs-apply-button" id="apply-btn" onclick="openModalWithDelay()">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none; border: 1px solid black; padding: 20px;">
        <h3>Formulario Direto</h3>
        <input type="text" name="name" required value="Nicolas Oliveira" />
        <button aria-label="Submit application" id="submit-btn" onclick="submitApp()">Enviar Candidatura</button>
        <button aria-label="Dismiss" id="close-btn" onclick="closeModal()">X</button>
    </div>

    <script>
        // ARMADILHA REAL: O modal tem animacao/delay de renderizacao de 300ms!
        function openModalWithDelay() {
            setTimeout(() => {
                document.getElementById('modal').style.display = 'block';
            }, 300);
        }
        function submitApp() {
            document.getElementById('modal').style.display = 'none';
        }
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

HTML_JOB_202_ADVANCED_CSS_TRAP = """<!DOCTYPE html>
<html>
<head><title>Vaga 202 - CSS Trap Severo</title></head>
<body>
    <h2>Backend Developer - SecureSystems</h2>
    <button class="jobs-apply-button" onclick="document.getElementById('modal').style.display = 'block'">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none;">
        <h3>Honeypot e Traps de CSS</h3>
        <!-- Campo obrigatorio VISIVEL e PREENCHIDO -->
        <input type="text" name="email" required value="user@domain.com" />
        
        <!-- Trap 1: display: none -->
        <input type="text" name="trap_display" required style="display: none;" value="" />
        
        <!-- Trap 2: visibility: hidden -->
        <input type="text" name="trap_visibility" required style="visibility: hidden;" value="" />

        <!-- Trap 3: Container pai oculto -->
        <div style="display: none;">
            <input type="text" name="trap_parent" required value="" />
            <textarea required></textarea>
            <select required><option value=""></option></select>
        </div>

        <button aria-label="Submit application" onclick="document.getElementById('modal').style.display = 'none'">Enviar Candidatura</button>
        <button aria-label="Dismiss" onclick="document.getElementById('modal').style.display = 'none'">X</button>
    </div>
</body>
</html>
"""

HTML_JOB_203_COMPLEX_WITH_DISCARD_POPUP = """<!DOCTYPE html>
<html>
<head><title>Vaga 203 - Descarte com Confirmacao Real</title></head>
<body>
    <h2>Data Engineer - BigData</h2>
    <button class="jobs-apply-button" onclick="document.getElementById('modal').style.display = 'block'">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none;">
        <h3>Formulario Complexo</h3>
        <label>Pretencao Salarial:</label>
        <input type="number" name="salary" required value="" />

        <button aria-label="Continue to next step">Avancar</button>
        <button aria-label="Submit application">Enviar</button>
        <button aria-label="Dismiss" onclick="openDiscardPopup()">X</button>

        <div id="discard-confirm" style="display: none; background: #eee; padding: 10px;">
            <p>Deseja descartar sua candidatura?</p>
            <button data-control-name="discard_application_confirm_btn" onclick="confirmDiscard()">Descartar</button>
        </div>
    </div>

    <script>
        // ARMADILHA: Popup de confirmacao de descarte com transicao de 200ms
        function openDiscardPopup() {
            setTimeout(() => {
                document.getElementById('discard-confirm').style.display = 'block';
            }, 200);
        }
        function confirmDiscard() {
            document.getElementById('modal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

HTML_JOB_204_MULTI_STEP_DELAYED = """<!DOCTYPE html>
<html>
<head><title>Vaga 204 - Multi-Step Real</title></head>
<body>
    <h2>DevOps - CloudNative</h2>
    <button class="jobs-apply-button" onclick="document.getElementById('modal').style.display = 'block'">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none;">
        <div id="step1">
            <h3>Passo 1: Contato</h3>
            <input type="text" required value="Nicolas Dev" />
            <button aria-label="Continue to next step" onclick="goToStep2WithDelay()">Avancar</button>
        </div>

        <div id="step2" style="display: none;">
            <h3>Passo 2: Revisao Final</h3>
            <input type="text" required value="Curriculo Anexado" />
            <button aria-label="Submit application" onclick="submitMulti()">Enviar Candidatura</button>
        </div>

        <button aria-label="Dismiss" onclick="document.getElementById('modal').style.display = 'none'">X</button>
    </div>

    <script>
        function goToStep2WithDelay() {
            setTimeout(() => {
                document.getElementById('step1').style.display = 'none';
                document.getElementById('step2').style.display = 'block';
            }, 250);
        }
        function submitMulti() {
            document.getElementById('modal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

HTML_JOB_205_EXTERNAL = """<!DOCTYPE html>
<html>
<head><title>Vaga 205 - Externa</title></head>
<body>
    <h2>Frontend - WebSoft</h2>
    <a href="https://external.com" target="_blank">Candidatar-se na empresa</a>
</body>
</html>
"""


class RealStressHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        host = self.headers.get("Host") or f"127.0.0.1:{self.server.server_port}"
        base_url = f"http://{host}"
        path = self.path.split("?")[0]

        routes = {
            "/jobs/search": HTML_SEARCH_PAGE.replace("{base_url}", base_url),
            "/jobs/search/": HTML_SEARCH_PAGE.replace("{base_url}", base_url),
            "/jobs/view/201/": HTML_JOB_201_ASYNC_MODAL,
            "/jobs/view/201": HTML_JOB_201_ASYNC_MODAL,
            "/jobs/view/202/": HTML_JOB_202_ADVANCED_CSS_TRAP,
            "/jobs/view/202": HTML_JOB_202_ADVANCED_CSS_TRAP,
            "/jobs/view/203/": HTML_JOB_203_COMPLEX_WITH_DISCARD_POPUP,
            "/jobs/view/203": HTML_JOB_203_COMPLEX_WITH_DISCARD_POPUP,
            "/jobs/view/204/": HTML_JOB_204_MULTI_STEP_DELAYED,
            "/jobs/view/204": HTML_JOB_204_MULTI_STEP_DELAYED,
            "/jobs/view/205/": HTML_JOB_205_EXTERNAL,
            "/jobs/view/205": HTML_JOB_205_EXTERNAL,
        }

        content = routes.get(path)
        if content:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")


@pytest.fixture(scope="module")
def stress_http_server():
    """Inicia o servidor de armadilha local com portas efemeras."""
    server = HTTPServer(("127.0.0.1", 0), RealStressHTTPHandler)
    port = server.server_port
    base_url = f"http://127.0.0.1:{port}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield base_url
    server.shutdown()


@pytest.fixture
def real_browser_service(temp_session_dir):
    """Instancia autentica do BrowserService no Chromium do Patchright (Zero Mocks)."""
    service = BrowserService(
        platform="sanctuary_real",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    yield service
    service.close()
