import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Tuple


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
    <h1>Simulacao de Busca de Vagas</h1>
    <div id="container" class="jobs-search-results-list">
        <div class="job-card-container">
            <a class="job-card-link" href="{base_url}/jobs/view/101/?refId=search_ref_1">Vaga 101 - Direta</a>
            <span class="title">Engenheiro Python</span>
            <span class="company">TechCorp</span>
        </div>
        <div class="job-card-container">
            <a class="job-card-link" href="{base_url}/jobs/view/102/?trackingId=track_2">Vaga 102 - CSS Trap</a>
            <span class="title">Backend Developer</span>
            <span class="company">SecureSystems</span>
        </div>
    </div>

    <script>
        // Simulacao de Lazy Loading Real disparado por Scroll
        let loadedMore = false;
        const container = document.getElementById('container');
        container.addEventListener('scroll', () => {
            if (!loadedMore && container.scrollTop > 50) {
                loadedMore = true;
                const card3 = document.createElement('div');
                card3.className = 'job-card-container';
                card3.innerHTML = '<a class="job-card-link" href="{base_url}/jobs/view/103/?refId=lazy_3">Vaga 103 - Complexa</a><span class="title">Data Engineer</span><span class="company">BigData Inc</span>';
                container.appendChild(card3);

                const card4 = document.createElement('div');
                card4.className = 'job-card-container';
                card4.innerHTML = '<a class="job-card-link" href="{base_url}/jobs/view/104/?refId=lazy_4">Vaga 104 - Multi-Step</a><span class="title">DevOps Engineer</span><span class="company">CloudNative</span>';
                container.appendChild(card4);

                const card5 = document.createElement('div');
                card5.className = 'job-card-container';
                card5.innerHTML = '<a class="job-card-link" href="{base_url}/jobs/view/105/">Vaga 105 - Externa</a><span class="title">Frontend Dev</span><span class="company">WebSoft</span>';
                container.appendChild(card5);
            }
        });
    </script>
</body>
</html>
"""

HTML_JOB_101_DIRECT = """<!DOCTYPE html>
<html>
<head><title>Vaga 101 - Direta</title></head>
<body>
    <h2>Senior Python Engineer - TechCorp</h2>
    <button class="jobs-apply-button" id="apply-btn" onclick="openModal()">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none; border: 1px solid black; padding: 20px;">
        <h3>Formulario Direto</h3>
        <input type="text" name="name" required value="Nicolas Oliveira" />
        <button aria-label="Submit application" id="submit-btn" onclick="submitApp()">Enviar Candidatura</button>
        <button aria-label="Dismiss" id="close-btn" onclick="closeModal()">X</button>
    </div>

    <div id="success" style="display: none;">Candidatura Enviada!</div>

    <script>
        function openModal() {
            document.getElementById('modal').style.display = 'block';
        }
        function submitApp() {
            document.getElementById('modal').style.display = 'none';
            document.getElementById('success').style.display = 'block';
        }
        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

HTML_JOB_102_CSS_TRAP = """<!DOCTYPE html>
<html>
<head><title>Vaga 102 - CSS Trap</title></head>
<body>
    <h2>Backend Developer - SecureSystems</h2>
    <button class="jobs-apply-button" onclick="document.getElementById('modal').style.display = 'block'">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none;">
        <h3>Formulario com Trap de CSS</h3>
        <!-- Campo obrigatorio visivel PREENCHIDO -->
        <input type="text" name="email" required value="user@domain.com" />
        
        <!-- Campo obrigatorio porem OCULTO por CSS (Honeypot / Bot Trap) -->
        <input type="text" name="bot_trap" required style="display: none;" value="" />
        <div style="display: none;">
            <input type="text" name="hidden_container_trap" required value="" />
        </div>

        <button aria-label="Submit application" onclick="document.getElementById('modal').style.display = 'none'">Enviar Candidatura</button>
        <button aria-label="Dismiss" onclick="document.getElementById('modal').style.display = 'none'">X</button>
    </div>
</body>
</html>
"""

HTML_JOB_103_COMPLEX = """<!DOCTYPE html>
<html>
<head><title>Vaga 103 - Complexa</title></head>
<body>
    <h2>Data Engineer - BigData Inc</h2>
    <button class="jobs-apply-button" onclick="document.getElementById('modal').style.display = 'block'">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none;">
        <h3>Formulario Complexo com Campos Vazios</h3>
        <!-- Campo obrigatorio VISIVEL VAZIO -->
        <label>Anos de experiencia:</label>
        <input type="number" name="experience" required value="" />

        <button aria-label="Continue to next step">Avancar</button>
        <button aria-label="Submit application">Enviar</button>
        <button aria-label="Dismiss" onclick="document.getElementById('discard-confirm').style.display = 'block'">X</button>

        <div id="discard-confirm" style="display: none; background: #eee; padding: 10px;">
            <p>Deseja descartar sua candidatura?</p>
            <button data-control-name="discard_application_confirm_btn" onclick="document.getElementById('modal').style.display = 'none'">Descartar</button>
        </div>
    </div>
</body>
</html>
"""

HTML_JOB_104_MULTI_STEP = """<!DOCTYPE html>
<html>
<head><title>Vaga 104 - Multi-Step</title></head>
<body>
    <h2>DevOps Engineer - CloudNative</h2>
    <button class="jobs-apply-button" onclick="document.getElementById('modal').style.display = 'block'">Candidatura Simplificada</button>

    <div class="jobs-easy-apply-modal" id="modal" style="display: none;">
        <!-- Passo 1 -->
        <div id="step1">
            <h3>Passo 1: Contato</h3>
            <input type="text" required value="Nicolas Dev" />
            <button aria-label="Continue to next step" onclick="goToStep2()">Avancar</button>
        </div>

        <!-- Passo 2 -->
        <div id="step2" style="display: none;">
            <h3>Passo 2: Revisao Final</h3>
            <input type="text" required value="Curriculo Anexado" />
            <button aria-label="Submit application" onclick="submitMulti()">Enviar Candidatura</button>
        </div>

        <button aria-label="Dismiss" onclick="document.getElementById('modal').style.display = 'none'">X</button>
    </div>

    <script>
        function goToStep2() {
            document.getElementById('step1').style.display = 'none';
            document.getElementById('step2').style.display = 'block';
        }
        function submitMulti() {
            document.getElementById('modal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

HTML_JOB_105_EXTERNAL = """<!DOCTYPE html>
<html>
<head><title>Vaga 105 - Externa</title></head>
<body>
    <h2>Frontend Dev - WebSoft</h2>
    <!-- Sem botao jobs-apply-button, apenas redirecionamento externo -->
    <a href="https://external-company.com/apply" target="_blank" class="external-apply-link">Candidatar-se no site da empresa</a>
</body>
</html>
"""


class RealPlatformHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silencia logs de requisicoes no terminal durante o pytest
        pass

    def do_GET(self):
        host = self.headers.get("Host") or f"127.0.0.1:{self.server.server_port}"
        base_url = f"http://{host}"

        path = self.path.split("?")[0]

        routes = {
            "/jobs/search": HTML_SEARCH_PAGE.replace("{base_url}", base_url),
            "/jobs/search/": HTML_SEARCH_PAGE.replace("{base_url}", base_url),
            "/jobs/view/101/": HTML_JOB_101_DIRECT,
            "/jobs/view/101": HTML_JOB_101_DIRECT,
            "/jobs/view/102/": HTML_JOB_102_CSS_TRAP,
            "/jobs/view/102": HTML_JOB_102_CSS_TRAP,
            "/jobs/view/103/": HTML_JOB_103_COMPLEX,
            "/jobs/view/103": HTML_JOB_103_COMPLEX,
            "/jobs/view/104/": HTML_JOB_104_MULTI_STEP,
            "/jobs/view/104": HTML_JOB_104_MULTI_STEP,
            "/jobs/view/105/": HTML_JOB_105_EXTERNAL,
            "/jobs/view/105": HTML_JOB_105_EXTERNAL,
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


def start_local_server() -> Tuple[HTTPServer, str]:
    """Inicia um servidor HTTP real local em porta efemera numa thread daemon."""
    server = HTTPServer(("127.0.0.1", 0), RealPlatformHTTPHandler)
    port = server.server_port
    base_url = f"http://127.0.0.1:{port}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, base_url
