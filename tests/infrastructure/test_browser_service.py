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

        # 1. Sem company_selector parametrizado, a empresa volta vazia por contrato
        cards_generic = service.extract_job_cards(".agnostic-card")
        assert len(cards_generic) == 2
        assert cards_generic[0]["url"] == "https://jobs.example.com/view/100"
        assert cards_generic[0]["title"] == "Senior Python Architect"
        assert cards_generic[0]["company"] == ""
        assert cards_generic[1]["company"] == ""

        # 2. Seletores customizados parametrizados extraem corretamente
        cards_custom = service.extract_job_cards(
            ".agnostic-card",
            title_selector=".heading-title, .custom-title",
            company_selector=".company-name, .custom-org",
        )
        assert len(cards_custom) == 2
        assert cards_custom[0]["company"] == "Global Tech"
        assert cards_custom[1]["title"] == "Lead QA Engineer"
        assert cards_custom[1]["company"] == "QualityCorp"

        # 3. Card sem titulo explicito cai para o texto do link, ou vazio (nunca 'Vaga')
        page.set_content("""
        <div class="agnostic-card">
            <a href="https://jobs.example.com/view/102"></a>
        </div>
        """)
        cards_empty = service.extract_job_cards(".agnostic-card")
        assert len(cards_empty) == 1
        assert cards_empty[0]["title"] == ""
        assert cards_empty[0]["company"] == ""
    finally:
        service.close()


def test_main_cli_invalid_platform_raises_error():
    """Valida que o main.py encerra com erro explicito ao receber plataforma desconhecida."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PLATFORM": "plataforma_inexistente_xyz",
            "HEADLESS": "true",
            "SESSION_ROOT_DIR": "./tests_scratch/cli_sessions",
        },
    )
    assert result.returncode != 0
    assert "nao suportada em SELECTOR_PROFILES" in result.stderr or "nao suportada em SELECTOR_PROFILES" in result.stdout


def test_browser_service_get_current_url(temp_session_dir):
    """Valida que get_current_url e current_url reportam a URL exata ativa da pagina."""
    service = BrowserService(
        platform="test_current_url",
        headless=True,
        channel="chromium",
        session_root_dir=temp_session_dir,
    )
    service.start_session()
    try:
        service.navigate("about:blank")
        assert service.get_current_url() == "about:blank"
        assert service.current_url() == "about:blank"
    finally:
        service.close()


def test_browser_engine_default_and_normalization(monkeypatch, temp_session_dir):
    """Valida que BROWSER_ENGINE ausente assume 'chromium' e normaliza strip+lower no parametro e env."""
    from src.infrastructure.browser_service import resolve_browser_engine

    monkeypatch.delenv("BROWSER_ENGINE", raising=False)
    assert resolve_browser_engine() == "chromium"
    service_default = BrowserService(session_root_dir=temp_session_dir)
    assert service_default.engine == "chromium"

    monkeypatch.setenv("BROWSER_ENGINE", "  FIREFOX \n")
    assert resolve_browser_engine() == "firefox"
    service_env = BrowserService(session_root_dir=temp_session_dir)
    assert service_env.engine == "firefox"

    assert resolve_browser_engine("  ChRoMiUm  ") == "chromium"
    assert resolve_browser_engine("  FiReFoX\t") == "firefox"


def test_browser_engine_invalid_value_fails_immediately_with_valid_options(monkeypatch, temp_session_dir):
    """Valida falha imediata para valor invalido de BROWSER_ENGINE listando os valores validos."""
    for invalid in ("webkit", "safari", "chrome_custom", ""):
        with pytest.raises(ValueError) as exc_info:
            BrowserService(engine=invalid, session_root_dir=temp_session_dir)
        msg = str(exc_info.value)
        assert "chromium" in msg
        assert "firefox" in msg

    monkeypatch.setenv("BROWSER_ENGINE", "opera")
    with pytest.raises(ValueError) as exc_env:
        BrowserService(session_root_dir=temp_session_dir)
    assert "chromium" in str(exc_env.value)
    assert "firefox" in str(exc_env.value)


def test_browser_engine_chromium_does_not_import_invisible_playwright(monkeypatch, temp_session_dir):
    """Garante que o caminho padrao chromium funciona mesmo sem invisible_playwright instalado."""
    monkeypatch.setitem(sys.modules, "invisible_playwright", None)
    monkeypatch.setitem(sys.modules, "invisible_playwright.sync_api", None)

    service = BrowserService(engine="chromium", session_root_dir=temp_session_dir)
    assert service.engine == "chromium"

    with pytest.raises(ImportError):
        BrowserService(engine="firefox", session_root_dir=temp_session_dir)


def test_cli_options_rules_1a_and_2a(monkeypatch):
    """Valida regras 1A (envio real exige cache) e 2A (strict_abort ligado por padrao) na CLI."""
    from src.main import resolve_cli_options

    monkeypatch.delenv("SHADOW_MODE", raising=False)
    monkeypatch.delenv("STRICT_ABORT", raising=False)
    monkeypatch.delenv("JOB_CACHE_ENABLED", raising=False)
    monkeypatch.delenv("JOB_CACHE_PATH", raising=False)

    # Padrao: strict_abort=True, shadow_mode=False, cache habilitado
    opts_default = resolve_cli_options([])
    assert opts_default["strict_abort"] is True
    assert opts_default["shadow_mode"] is False
    assert opts_default["cache_enabled"] is True
    assert opts_default["cache_path"].endswith("jobs_history.json")

    # 2A: desligar strict_abort exige flag explicita
    opts_no_strict = resolve_cli_options(["--no-strict-abort"])
    assert opts_no_strict["strict_abort"] is False

    # 1A: envio real sem cache falha na hora
    with pytest.raises(ValueError) as exc_1a:
        resolve_cli_options(["--no-cache"])
    assert "Regra 1A" in str(exc_1a.value)

    # 1A: shadow mode permite rodar sem cache
    opts_shadow = resolve_cli_options(["--shadow-mode", "--no-cache"])
    assert opts_shadow["shadow_mode"] is True
    assert opts_shadow["cache_enabled"] is False
    assert opts_shadow["cache_path"] is None


def test_main_cli_refuses_real_submission_without_cache():
    """Valida que python -m src.main --no-cache falha imediatamente antes de abrir navegador."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--no-cache"],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "HEADLESS": "true",
            "SHADOW_MODE": "false",
        },
    )
    assert result.returncode != 0
    assert "Regra 1A" in (result.stderr + result.stdout)


def test_default_visibility_timeout_is_3000ms_and_constructor_override(monkeypatch, temp_session_dir):
    """
    Passo A1: Garante que o prazo padrao de is_visible / element_exists voltou a 3000 ms
    e que a injecao de visibility_timeout_ms no construtor do BrowserService sobrepoe
    esse valor sem precisar de variavel de ambiente.
    """
    default_service = BrowserService(session_root_dir=temp_session_dir)
    assert default_service.visibility_timeout_ms == 3000

    observed_timeouts = []
    monkeypatch.setattr(
        default_service,
        "_resolve_visible_locator",
        lambda selector, timeout=5000: observed_timeouts.append(timeout) or object(),
    )
    assert default_service.is_visible("#modal") is True
    assert observed_timeouts == [3000]

    custom_service = BrowserService(
        session_root_dir=temp_session_dir,
        visibility_timeout_ms=1000,
    )
    assert custom_service.visibility_timeout_ms == 1000
    custom_observed = []
    monkeypatch.setattr(
        custom_service,
        "_resolve_visible_locator",
        lambda selector, timeout=5000: custom_observed.append(timeout) or object(),
    )
    assert custom_service.element_exists("#modal") is True
    assert custom_observed == [1000]
    assert custom_service.is_visible("#modal", timeout=4500) is True
    assert custom_observed == [1000, 4500]


def test_get_project_root_contains_src_and_notas_md():
    """Passo A2: Valida funcao unica get_project_root apontando para a raiz do repositorio."""
    from src.infrastructure.paths import get_project_root

    root = get_project_root()
    assert root.is_dir()
    assert (root / "src").is_dir()
    assert (root / "NOTAS.md").is_file()


def test_default_cache_and_profile_anchored_at_project_root_under_chdir(monkeypatch, tmp_path):
    """
    Passo A2:
    1. Mesmo quando os.getcwd() muda para tmp_path, os caminhos padrao do cache de historico
       e do perfil de sessao continuam ancorados em get_project_root().
    2. Quando um caminho relativo explicito e passado por CLI (--cache-path) ou env
       (JOB_CACHE_PATH, SESSION_ROOT_DIR), ele resolve em relacao ao cwd atual (tmp_path).
    """
    from src.infrastructure.paths import get_project_root
    from src.main import resolve_cli_options

    project_root = get_project_root()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JOB_CACHE_PATH", raising=False)
    monkeypatch.delenv("SESSION_ROOT_DIR", raising=False)

    opts_default = resolve_cli_options([])
    assert opts_default["cache_path"] == str(project_root / ".cache" / "jobs_history.json")

    service_default = BrowserService(platform="linkedin", engine="chromium")
    assert service_default.user_data_dir.startswith(str(project_root / "sessions"))

    opts_cli_rel = resolve_cli_options(["--cache-path", "./local_dir/custom.json"])
    assert opts_cli_rel["cache_path"] == str((tmp_path / "local_dir" / "custom.json").resolve())

    monkeypatch.setenv("JOB_CACHE_PATH", "./env_dir/env_cache.json")
    opts_env_rel = resolve_cli_options([])
    assert opts_env_rel["cache_path"] == str((tmp_path / "env_dir" / "env_cache.json").resolve())

    monkeypatch.setenv("SESSION_ROOT_DIR", "./env_sessions")
    service_env_rel = BrowserService(platform="linkedin", engine="chromium")
    assert service_env_rel.user_data_dir.startswith(str((tmp_path / "env_sessions").resolve()))


def test_profile_directory_is_separated_by_engine_as_sibling(tmp_path):
    """
    Passo A3: Mesma plataforma e motores diferentes usam diretorios de perfil irmaos
    (<root>/<platform> para chromium e <root>/<platform>-firefox para firefox),
    evitando corrupcao de perfil e preservando sessoes existentes de Chromium.
    """
    chromium_service = BrowserService(
        platform="linkedin",
        engine="chromium",
        session_root_dir=str(tmp_path),
    )
    firefox_service = BrowserService(
        platform="linkedin",
        engine="firefox",
        session_root_dir=str(tmp_path),
    )

    assert chromium_service.user_data_dir == str((tmp_path / "linkedin").resolve())
    assert firefox_service.user_data_dir == str((tmp_path / "linkedin-firefox").resolve())
    assert chromium_service.user_data_dir != firefox_service.user_data_dir


def test_firefox_headless_without_xvfb_raises_clear_runtime_error(monkeypatch, tmp_path):
    """
    Passo A4: Em Firefox com headless=True e modo padrao ('xvfb'), se shutil.which('Xvfb')
    retornar None, falha na hora com RuntimeError instruindo instalar o pacote xvfb
    ou passar firefox_headless_mode='true_headless' explicitamente.
    """
    import shutil
    from src.infrastructure.browser_service import XVFB_MISSING_ERROR_MSG

    monkeypatch.delenv("FIREFOX_HEADLESS_MODE", raising=False)
    monkeypatch.delenv("INVPW_TRUE_HEADLESS", raising=False)
    monkeypatch.setattr(shutil, "which", lambda cmd: None if cmd == "Xvfb" else "/usr/bin/" + cmd)

    service = BrowserService(
        platform="test_ff_noxvfb",
        headless=True,
        engine="firefox",
        session_root_dir=str(tmp_path),
    )
    with pytest.raises(RuntimeError) as exc_info:
        service.start_session()

    msg = str(exc_info.value)
    assert msg == XVFB_MISSING_ERROR_MSG
    assert "sudo apt-get install -y xvfb" in msg
    assert "true_headless" in msg
    assert "INVPW_TRUE_HEADLESS" not in os.environ


def test_firefox_explicit_true_headless_logs_warning_and_restores_environ(monkeypatch, tmp_path, caplog):
    """
    Passo A4: Somente quando firefox_headless_mode='true_headless' (ou FIREFOX_HEADLESS_MODE=true_headless)
    for passado explicitamente, registra WARNING, liga INVPW_TRUE_HEADLESS=1 apenas durante a sessao
    e restaura os.environ ao encerrar em close().
    """
    monkeypatch.delenv("INVPW_TRUE_HEADLESS", raising=False)

    service = BrowserService(
        platform="test_ff_true_headless",
        headless=True,
        engine="firefox",
        firefox_headless_mode="true_headless",
        session_root_dir=str(tmp_path),
    )

    observed_env_during_launch = {}

    class _FakeInstance:
        def __init__(self, **kwargs):
            observed_env_during_launch["val"] = os.environ.get("INVPW_TRUE_HEADLESS")

        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(service._launcher, "_driver_cls", _FakeInstance)

    with caplog.at_level("WARNING"):
        service.start_session()
        meta = service.get_runtime_metadata()
        assert meta["engine"] == "firefox"
        assert meta["effective_mode"] == "headless-real"
        assert observed_env_during_launch["val"] == "1"
        assert os.environ.get("INVPW_TRUE_HEADLESS") == "1"

    assert any("headless-real" in rec.message for rec in caplog.records)

    service.close()
    assert "INVPW_TRUE_HEADLESS" not in os.environ


def test_firefox_xvfb_mode_and_runtime_metadata_both_engines(monkeypatch, tmp_path):
    """
    Passo A4 (Ajuste c): Valida modo 'xvfb' quando Xvfb esta presente no PATH e
    confere get_runtime_metadata() para Chromium e Firefox.
    """
    import shutil

    monkeypatch.delenv("INVPW_TRUE_HEADLESS", raising=False)
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/Xvfb" if cmd == "Xvfb" else None)

    ff_service = BrowserService(
        platform="test_ff_xvfb",
        headless=True,
        engine="firefox",
        session_root_dir=str(tmp_path),
    )

    class _FakeFFInstance:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(ff_service._launcher, "_driver_cls", _FakeFFInstance)
    ff_service.start_session()
    ff_meta = ff_service.get_runtime_metadata()
    assert ff_meta["engine"] == "firefox"
    assert ff_meta["effective_mode"] == "xvfb"
    assert ff_meta["xvfb_path"] == "/usr/bin/Xvfb"
    assert "INVPW_TRUE_HEADLESS" not in os.environ
    ff_service.close()

    cr_service = BrowserService(
        platform="test_cr_meta",
        headless=True,
        engine="chromium",
        session_root_dir=str(tmp_path),
    )
    cr_meta = cr_service.get_runtime_metadata()
    assert cr_meta["engine"] == "chromium"
    assert cr_meta["effective_mode"] == "headless"
    assert cr_meta["xvfb_path"] == "/usr/bin/Xvfb"


def test_browser_service_default_channel_is_chromium(monkeypatch, tmp_path):
    """
    Passo A6: Prova que BrowserService().channel ja tem 'chromium' como padrao
    sem precisar chumbar channel='chromium' nas fixtures dos testes reais.
    """
    monkeypatch.delenv("BROWSER_CHANNEL", raising=False)
    service = BrowserService(session_root_dir=str(tmp_path))
    assert service.channel == "chromium"


def test_identity_guard_allows_local_targets(monkeypatch, tmp_path):
    """
    Passo A1: Trava de identidade em modo permissivo para clone local (localhost / 127.0.0.1).
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    meta1 = service.verify_runtime_identity(target_url="http://127.0.0.1:3000/jobs")
    meta2 = service.verify_runtime_identity(target_url="http://localhost:3000")
    meta3 = service.verify_runtime_identity(target_url="")
    assert meta1["engine"] == "chromium"
    assert meta2["engine"] == "chromium"
    assert meta3["engine"] == "chromium"


def test_identity_guard_refuses_when_not_xvfb_on_external_target(monkeypatch, tmp_path):
    """
    Passo A1 (Ajuste b): Bloqueia imediatamente se effective_mode != 'xvfb' em alvo externo.
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "chromium",
            "effective_mode": "headless",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36",
            "webdriver": False,
            "plugins_length": 5,
        },
    )
    with pytest.raises(RuntimeError, match="Trava de Identidade violada: Alvo externo exige janela real dentro de Xvfb"):
        service.verify_runtime_identity(target_url="https://www.linkedin.com/jobs")


def test_identity_guard_refuses_when_user_agent_has_headless_chrome(monkeypatch, tmp_path):
    """
    Passo A1 (Ajuste b): Bloqueia se o User-Agent contiver 'HeadlessChrome' em alvo externo.
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "chromium",
            "effective_mode": "xvfb",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 HeadlessChrome/153.0.8010.12 Safari/537.36",
            "webdriver": False,
            "plugins_length": 5,
        },
    )
    with pytest.raises(RuntimeError, match="Assinatura 'HeadlessChrome' detectada no User-Agent"):
        service.verify_runtime_identity(target_url="https://www.linkedin.com/jobs")


def test_identity_guard_refuses_when_webdriver_is_true(monkeypatch, tmp_path):
    """
    Passo A1 (Ajuste b): Bloqueia se navigator.webdriver for True em alvo externo.
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "chromium",
            "effective_mode": "xvfb",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36",
            "webdriver": True,
            "plugins_length": 5,
        },
    )
    with pytest.raises(RuntimeError, match="navigator.webdriver verdadeiro detectado"):
        service.verify_runtime_identity(target_url="https://www.linkedin.com/jobs")


def test_identity_guard_refuses_when_xvfb_missing(monkeypatch, tmp_path):
    """
    Passo A1 (Ajuste b): Bloqueia se /usr/bin/Xvfb estiver ausente no PATH.
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "chromium",
            "effective_mode": "xvfb",
            "xvfb_path": None,
            "user_agent": "Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36",
            "webdriver": False,
            "plugins_length": 5,
        },
    )
    with pytest.raises(RuntimeError, match="Executavel 'Xvfb' ausente no PATH"):
        service.verify_runtime_identity(target_url="https://www.linkedin.com/jobs")


def test_identity_guard_refuses_when_plugins_length_is_zero(monkeypatch, tmp_path):
    """
    Passo A1 (Ajuste b): Bloqueia se navigator.plugins.length == 0 em alvo externo.
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "chromium",
            "effective_mode": "xvfb",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36",
            "webdriver": False,
            "plugins_length": 0,
        },
    )
    with pytest.raises(RuntimeError, match="navigator.plugins vazio"):
        service.verify_runtime_identity(target_url="https://www.linkedin.com/jobs")


def test_identity_guard_refuses_when_engine_unknown_or_mismatched(monkeypatch, tmp_path):
    """
    Passo A1 (Ajuste b): Bloqueia se o motor for desconhecido ou UA contradisser o motor.
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "safari",
            "effective_mode": "xvfb",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 Safari/605",
            "webdriver": False,
            "plugins_length": 5,
        },
    )
    with pytest.raises(RuntimeError, match="Motor de navegador nao reconhecido"):
        service.verify_runtime_identity(target_url="https://www.linkedin.com/jobs")

    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "firefox",
            "effective_mode": "xvfb",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36",
            "webdriver": False,
            "plugins_length": 5,
        },
    )
    with pytest.raises(RuntimeError, match="Motor configurado e 'firefox', mas User-Agent nao contem 'Firefox'"):
        service.verify_runtime_identity(target_url="https://www.linkedin.com/jobs")


def test_navigate_enforces_identity_guard_on_external_target(monkeypatch, tmp_path):
    """
    Passo A1: navigate() propaga a recusa da trava de identidade em URL externa.
    """
    service = BrowserService(session_root_dir=str(tmp_path))
    monkeypatch.setattr(
        service,
        "get_runtime_metadata",
        lambda: {
            "engine": "chromium",
            "effective_mode": "headless",
            "xvfb_path": "/usr/bin/Xvfb",
            "user_agent": "Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36",
            "webdriver": False,
            "plugins_length": 5,
        },
    )
    with pytest.raises(RuntimeError, match="Trava de Identidade violada"):
        service.navigate("https://remote-job-portal.com/jobs/1")









