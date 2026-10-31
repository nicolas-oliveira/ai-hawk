import pytest
import os
import subprocess
import sys
from src.infrastructure.browser_service import BrowserService


def test_browser_service_initialization(temp_session_dir):
    """Valida configuracoes padrao de inicializacao do BrowserService."""
    service = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    assert service.platform == "linkedin"
    assert service.headless is True
    assert service.channel == "chromium"
    assert service.user_data_dir == os.path.join(temp_session_dir, "linkedin")


def test_browser_service_session_persistence(temp_session_dir):
    """Valida persistencia sincrona real entre sessoes consecutivas."""
    service1 = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )

    # Sessao 1: Gravar dado no localStorage
    service1.start_session()
    page1 = service1.get_page()
    page1.goto("https://example.com", wait_until="domcontentloaded")
    page1.evaluate("localStorage.setItem('session_marker', 'agy_v0.5_shift_left')")
    service1.close()

    # Sessao 2: Ler dado no mesmo perfil
    service2 = BrowserService(
        platform="linkedin",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service2.start_session()
    page2 = service2.get_page()
    page2.goto("https://example.com", wait_until="domcontentloaded")
    val = page2.evaluate("localStorage.getItem('session_marker')")
    service2.close()

    assert val == "agy_v0.5_shift_left"


def test_browser_service_platform_isolation(temp_session_dir):
    """Valida isolamento de diretorios por plataforma (Decisao 2)."""
    service_a = BrowserService(platform="platform_a", session_root_dir=temp_session_dir)
    service_b = BrowserService(platform="platform_b", session_root_dir=temp_session_dir)

    assert service_a.user_data_dir != service_b.user_data_dir
    assert service_a.user_data_dir.endswith("platform_a")
    assert service_b.user_data_dir.endswith("platform_b")


def test_browser_service_navigation_real_dom(temp_session_dir):
    """Valida navegacao sincrona real com sucesso e com timeout/falha."""
    service = BrowserService(
        platform="test_nav",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        success = service.navigate("https://example.com")
        assert success is True

        # Falha esperada para porta fechada/invalida com timeout curto
        fail = service.navigate("http://127.0.0.1:54321/inexistente", timeout=1000)
        assert fail is False
    finally:
        service.close()


def test_browser_service_scroll_container_real_dom(temp_session_dir):
    """Valida o scroll incremental real de um container com overflow (lazy loading)."""
    service = BrowserService(
        platform="test_scroll",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        page = service.get_page()
        # Monta pagina com container de overflow e itens altos
        html = """
        <html>
            <body>
                <div id="scrollable" style="height: 200px; overflow-y: scroll; border: 1px solid black;">
                    <div style="height: 300px;">Item 1</div>
                    <div style="height: 300px;">Item 2</div>
                    <div style="height: 300px;">Item 3</div>
                </div>
            </body>
        </html>
        """
        page.set_content(html)

        # Container inexistente
        assert service.scroll_container("#nao_existe") is False

        # Container existente
        scrolled = service.scroll_container("#scrollable", steps=2, delay=0.1)
        assert scrolled is True

        scroll_pos = page.evaluate("() => document.getElementById('scrollable').scrollTop")
        assert scroll_pos > 0
    finally:
        service.close()


def test_browser_service_extract_links_real_dom(temp_session_dir):
    """Valida extracao sincrona e deduplicacao de links de cards no DOM real."""
    service = BrowserService(
        platform="test_links",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        page = service.get_page()
        html = """
        <html>
            <body>
                <div class="job-card"><a href="https://example.com/job/1">Vaga 1</a></div>
                <div class="job-card"><a href="https://example.com/job/2">Vaga 2</a></div>
                <div class="job-card"><a href="https://example.com/job/1">Vaga 1 Duplicada</a></div>
                <a class="job-card-link" href="https://example.com/job/3">Vaga 3 Direta</a>
            </body>
        </html>
        """
        page.set_content(html)

        # Extracao de links dentro de cards .job-card
        links = service.extract_links(".job-card", "a")
        assert len(links) == 2
        assert links[0] == "https://example.com/job/1"
        assert links[1] == "https://example.com/job/2"

        # Extracao quando o proprio card e a tag <a>
        direct_links = service.extract_links(".job-card-link", "a")
        assert direct_links == ["https://example.com/job/3"]
    finally:
        service.close()


def test_browser_service_has_empty_required_inputs_heuristica_3c(temp_session_dir):
    """
    Valida a Heuristica 3C completa contra cenarios reais de formularios no Chromium:
    - Campos obrigatorios vazios visiveis -> True
    - Campos obrigatorios invisiveis/hidden -> False
    - Checkbox/Radio/Textarea/Select obrigatórios
    - Formulario 100% preenchido -> False
    """
    service = BrowserService(
        platform="test_3c",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        page = service.get_page()

        # Cenario 1: Modal nao existe ou esta invisivel
        page.set_content("<html><body><div id='outro'>Sem modal</div></body></html>")
        assert service.has_empty_required_inputs("#modal") is False

        # Cenario 2: Modal com input text obrigatorio vazio visivel -> DEVE RETORNAR True
        page.set_content("""
        <div id="modal" style="display: block;">
            <input id="name" type="text" required value="" />
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is True

        # Cenario 3: Modal com input text obrigatorio preenchido -> DEVE RETORNAR False
        page.set_content("""
        <div id="modal" style="display: block;">
            <input id="name" type="text" required value="Nicolas Dev" />
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is False

        # Cenario 4: Input obrigatorio porem INVISIVEL (display: none) -> DEVE RETORNAR False
        page.set_content("""
        <div id="modal" style="display: block;">
            <input id="hidden_req" type="text" required style="display: none;" value="" />
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is False

        # Cenario 5: Textarea obrigatorio vazio -> DEVE RETORNAR True
        page.set_content("""
        <div id="modal" style="display: block;">
            <textarea required></textarea>
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is True

        # Cenario 6: Select obrigatorio com option vazia selecionada -> DEVE RETORNAR True
        page.set_content("""
        <div id="modal" style="display: block;">
            <select required>
                <option value="">Selecione...</option>
                <option value="1">Opcao 1</option>
            </select>
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is True

        # Cenario 7: Select obrigatorio com opcao valida selecionada -> DEVE RETORNAR False
        page.set_content("""
        <div id="modal" style="display: block;">
            <select required>
                <option value="1" selected>Opcao 1</option>
            </select>
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is False

        # Cenario 8: Grupo de radio obrigatorio sem selecao -> DEVE RETORNAR True
        page.set_content("""
        <div id="modal" style="display: block;">
            <input type="radio" name="experience" value="yes" required />
            <input type="radio" name="experience" value="no" />
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is True

        # Cenario 9: Grupo de radio obrigatorio com uma opcao selecionada -> DEVE RETORNAR False
        page.set_content("""
        <div id="modal" style="display: block;">
            <input type="radio" name="experience" value="yes" required checked />
            <input type="radio" name="experience" value="no" />
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is False

        # Cenario 10: aria-required="true" vazio -> DEVE RETORNAR True
        page.set_content("""
        <div id="modal" style="display: block;">
            <input type="text" aria-required="true" value="" />
        </div>
        """)
        assert service.has_empty_required_inputs("#modal") is True

    finally:
        service.close()


def test_browser_service_click_and_visibility(temp_session_dir):
    """Valida metodos click_element e is_visible com DOM interativo real."""
    service = BrowserService(
        platform="test_click",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        page = service.get_page()
        html = """
        <html>
            <body>
                <button id="btn" onclick="document.getElementById('status').innerText = 'Clicado';">Enviar</button>
                <div id="status">Aguardando</div>
                <div id="invisivel" style="display: none;">Escondido</div>
            </body>
        </html>
        """
        page.set_content(html)

        # Checagem de visibilidade
        assert service.is_visible("#btn") is True
        assert service.is_visible("#invisivel", timeout=500) is False
        assert service.is_visible("#inexistente", timeout=500) is False

        # Clique funcional
        clicked = service.click_element("#btn")
        assert clicked is True

        status_text = page.locator("#status").inner_text()
        assert status_text == "Clicado"

        # Clique em elemento inexistente
        assert service.click_element("#btn_inexistente", timeout=500) is False
    finally:
        service.close()


def test_main_cli_execution():
    """Valida execucao e integracao do CLI sincrono python -m src.main."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "HEADLESS": "true",
            "BROWSER_CHANNEL": "chromium",
            "SESSION_ROOT_DIR": "./tests_scratch/cli_sessions",
        },
    )
    assert result.returncode == 0
    assert "AIHawk v0.5 - Motor de Candidaturas Easy Apply Seco" in result.stdout
    assert "Sessao encerrada com sucesso." in result.stdout


def test_browser_service_human_delay_stochastic_range(temp_session_dir):
    """Valida geracao de delay estocastico gaussiano com clamping no intervalo."""
    service = BrowserService(
        platform="test_jitter",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    # Testa sem abrir navegador para medicao pura
    d = service.human_delay(0.05, 0.15)
    assert 0.05 <= d <= 0.15


def test_browser_service_modal_signature(temp_session_dir):
    """Valida determinismo e deteccao de mudanca de estado no modal_signature."""
    service = BrowserService(
        platform="test_signature",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        page = service.get_page()
        page.set_content("""
        <div id="modal" style="display: block;">
            <h2>Passo 1</h2>
            <p>Dados Pessoais</p>
        </div>
        """)
        sig1 = service.modal_signature("#modal")
        assert len(sig1) == 64  # SHA-256

        # Conteudo identico -> mesma assinatura
        assert service.modal_signature("#modal") == sig1

        # Conteudo muda -> assinatura diferente
        page.set_content("""
        <div id="modal" style="display: block;">
            <h2>Passo 2</h2>
            <p>Experiencia Profissional</p>
        </div>
        """)
        sig2 = service.modal_signature("#modal")
        assert sig2 != sig1
        assert len(sig2) == 64

        # Modal invisivel ou inexistente
        assert service.modal_signature("#inexistente") == ""
    finally:
        service.close()


def test_browser_service_extract_job_cards_agnostic(temp_session_dir):
    """Valida extracao desacoplada de cards sem seletores exclusivos do LinkedIn."""
    service = BrowserService(
        platform="test_cards",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        page = service.get_page()
        page.set_content("""
        <div class="agnostic-card">
            <a href="https://jobs.example.com/view/100">Candidatura</a>
            <h3 class="custom-title">Senior Python Architect</h3>
            <span class="custom-org">Global Tech</span>
        </div>
        <div class="agnostic-card">
            <a href="https://jobs.example.com/view/101">Candidatura 2</a>
            <div class="heading-title">Lead QA Engineer</div>
            <p class="company-name">QualityCorp</p>
        </div>
        """)

        # 1. Fallback semantico generico
        cards_generic = service.extract_job_cards(".agnostic-card")
        assert len(cards_generic) == 2
        assert cards_generic[0]["url"] == "https://jobs.example.com/view/100"
        assert cards_generic[0]["title"] == "Senior Python Architect"
        assert cards_generic[0]["company"] == "Global Tech"

        # 2. Seletores customizados parametrizados
        cards_custom = service.extract_job_cards(
            ".agnostic-card",
            title_selector=".heading-title, .custom-title",
            company_selector=".company-name, .custom-org",
        )
        assert len(cards_custom) == 2
        assert cards_custom[1]["title"] == "Lead QA Engineer"
        assert cards_custom[1]["company"] == "QualityCorp"
    finally:
        service.close()

