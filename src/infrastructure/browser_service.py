import os
import shutil
import time
import random
import hashlib
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from patchright.sync_api import sync_playwright, BrowserContext, Page, Playwright
from src.infrastructure.paths import get_project_root

load_dotenv()

logger = logging.getLogger(__name__)

VALID_ENGINES = ("chromium", "firefox")
DEFAULT_ENGINE = "chromium"
DEFAULT_VISIBILITY_TIMEOUT_MS = 3000
VALID_FIREFOX_HEADLESS_MODES = ("xvfb", "true_headless")
DEFAULT_FIREFOX_HEADLESS_MODE = "xvfb"
XVFB_MISSING_ERROR_MSG = (
    "Firefox em modo headless exige Xvfb para operacao stealth segura, "
    "mas o executavel 'Xvfb' nao foi encontrado no PATH. "
    "Instale o pacote com 'sudo apt-get install -y xvfb' ou passe explicitamente "
    "firefox_headless_mode='true_headless' (ou FIREFOX_HEADLESS_MODE=true_headless) "
    "apenas para diagnostico."
)


def resolve_firefox_headless_mode(mode: Optional[str] = None) -> str:
    """
    Normaliza e valida o modo headless do Firefox ('xvfb' ou 'true_headless').
    Padrao: 'xvfb'.
    """
    if mode is None:
        raw_env = os.getenv("FIREFOX_HEADLESS_MODE")
        if raw_env is None or not raw_env.strip():
            return DEFAULT_FIREFOX_HEADLESS_MODE
        raw = raw_env
    else:
        raw = mode

    normalized = str(raw).strip().lower()
    if normalized not in VALID_FIREFOX_HEADLESS_MODES:
        valid_str = ", ".join(VALID_FIREFOX_HEADLESS_MODES)
        raise ValueError(
            f"Valor invalido para FIREFOX_HEADLESS_MODE: '{raw}'. "
            f"Valores validos: {valid_str}."
        )
    return normalized


def resolve_browser_engine(engine: Optional[str] = None) -> str:
    """
    Normaliza (strip + lower) e valida o motor do navegador.
    Ausente vale 'chromium'. Qualquer outro valor falha na hora listando os validos.
    """
    if engine is None:
        raw_env = os.getenv("BROWSER_ENGINE")
        if raw_env is None or not raw_env.strip():
            return DEFAULT_ENGINE
        raw = raw_env
    else:
        raw = engine

    normalized = str(raw).strip().lower()
    if normalized not in VALID_ENGINES:
        valid_str = ", ".join(VALID_ENGINES)
        raise ValueError(
            f"Valor invalido para BROWSER_ENGINE: '{raw}'. "
            f"Valores validos: {valid_str}."
        )
    return normalized


class _ChromiumLauncher:
    """Adaptador de inicializacao sincrona para o motor Chromium (Patchright)."""

    def __init__(self) -> None:
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.virtual_display: Any = None
        self.effective_mode: Optional[str] = None
        self.xvfb_path: Optional[str] = None

    def start(
        self,
        user_data_dir: str,
        headless: bool,
        channel: str,
        viewport_width: int,
        viewport_height: int,
        extra_args: Optional[List[str]] = None,
    ) -> BrowserContext:
        import sys
        self.playwright = sync_playwright().start()
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        if extra_args:
            args.extend(extra_args)

        launch_env: Optional[Dict[str, str]] = None
        xvfb_bin = shutil.which("Xvfb")

        # Em Linux: se headless=True (ou BROWSER_HEADLESS_MODE=xvfb) e Xvfb existir,
        # roda com janela real (headless=False) dentro de um display virtual Xvfb isolado.
        if headless and sys.platform.startswith("linux") and xvfb_bin:
            try:
                from invisible_core._headless import _LinuxVirtualDisplay
                self.virtual_display = _LinuxVirtualDisplay(viewport_width, viewport_height)
                self.virtual_display.start()
                launch_env = os.environ.copy()
                for k, v in self.virtual_display.launch_env().items():
                    if v is None:
                        launch_env.pop(k, None)
                    else:
                        launch_env[k] = v
                self.effective_mode = "xvfb"
                self.xvfb_path = xvfb_bin
                actual_headless = False  # Janela real desenhando no display virtual Xvfb
            except Exception as exc:
                logger.warning("Falha ao iniciar Xvfb para Chromium (%s); caindo para headless nativo.", exc)
                self.virtual_display = None
                self.effective_mode = "headless"
                self.xvfb_path = xvfb_bin
                actual_headless = True
        elif headless:
            self.effective_mode = "headless"
            self.xvfb_path = xvfb_bin
            actual_headless = True
        else:
            self.effective_mode = "headed"
            self.xvfb_path = xvfb_bin
            actual_headless = False

        launch_kwargs: Dict[str, Any] = {
            "user_data_dir": user_data_dir,
            "headless": actual_headless,
            "args": args,
            "viewport": {"width": viewport_width, "height": viewport_height},
        }
        if launch_env is not None:
            launch_kwargs["env"] = launch_env
        if channel == "chrome" and shutil.which("google-chrome"):
            launch_kwargs["channel"] = "chrome"

        self.context = self.playwright.chromium.launch_persistent_context(**launch_kwargs)
        return self.context

    def stop(self) -> None:
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
        if self.virtual_display:
            try:
                self.virtual_display.stop()
            except Exception:
                pass
            self.virtual_display = None


class _FirefoxLauncher:
    """Adaptador de inicializacao sincrona para o motor Firefox (invisible-playwright)."""

    def __init__(self, firefox_headless_mode: Optional[str] = None) -> None:
        from invisible_playwright.sync_api import InvisiblePlaywright

        self._driver_cls = InvisiblePlaywright
        self._instance: Any = None
        self.context: Optional[BrowserContext] = None
        self.firefox_headless_mode = resolve_firefox_headless_mode(firefox_headless_mode)
        self.effective_mode: Optional[str] = None
        self.xvfb_path: Optional[str] = None
        self._had_prev_invpw_env: bool = False
        self._prev_invpw_env_val: Optional[str] = None
        self._env_modified: bool = False

    def start(
        self,
        user_data_dir: str,
        headless: bool,
        channel: str,
        viewport_width: int,
        viewport_height: int,
        extra_args: Optional[List[str]] = None,
    ) -> BrowserContext:
        self._had_prev_invpw_env = "INVPW_TRUE_HEADLESS" in os.environ
        self._prev_invpw_env_val = os.environ.get("INVPW_TRUE_HEADLESS")
        self._env_modified = False

        if not headless:
            self.effective_mode = "headed"
            self.xvfb_path = shutil.which("Xvfb")
        elif self.firefox_headless_mode == "true_headless":
            logger.warning(
                "[BrowserService] Firefox iniciado em modo 'headless-real' (INVPW_TRUE_HEADLESS=1). "
                "Modo sem Xvfb enfraquece a camuflagem stealth; use apenas em teste/diagnostico."
            )
            os.environ["INVPW_TRUE_HEADLESS"] = "1"
            self._env_modified = True
            self.effective_mode = "headless-real"
            self.xvfb_path = shutil.which("Xvfb")
        else:
            xvfb_bin = shutil.which("Xvfb")
            if not xvfb_bin:
                raise RuntimeError(XVFB_MISSING_ERROR_MSG)
            if "INVPW_TRUE_HEADLESS" in os.environ:
                os.environ.pop("INVPW_TRUE_HEADLESS", None)
                self._env_modified = True
            self.effective_mode = "xvfb"
            self.xvfb_path = xvfb_bin

        self._instance = self._driver_cls(
            profile_dir=user_data_dir,
            headless=headless,
            extra_args=extra_args,
        )
        self.context = self._instance.__enter__()
        return self.context

    def _restore_env(self) -> None:
        if not self._env_modified:
            return
        if self._had_prev_invpw_env and self._prev_invpw_env_val is not None:
            os.environ["INVPW_TRUE_HEADLESS"] = self._prev_invpw_env_val
        else:
            os.environ.pop("INVPW_TRUE_HEADLESS", None)
        self._env_modified = False

    def stop(self) -> None:
        try:
            if self._instance is not None:
                try:
                    self._instance.__exit__(None, None, None)
                except Exception:
                    pass
                self._instance = None
            self.context = None
        finally:
            self._restore_env()


def create_engine_launcher(
    engine: Optional[str] = None,
    firefox_headless_mode: Optional[str] = None,
):
    """Fabrica isolada de motor de navegador."""
    resolved = resolve_browser_engine(engine)
    if resolved == "firefox":
        return _FirefoxLauncher(firefox_headless_mode=firefox_headless_mode)
    return _ChromiumLauncher()


class BrowserService:
    """
    Servico de Infraestrutura para gerenciamento do navegador (Chromium/Firefox).
    Totalmente agnostico de plataforma, linear, com sessoes persistentes e stealth nativo.
    """

    def __init__(
        self,
        platform: str = "default",
        headless: Optional[bool] = None,
        channel: Optional[str] = None,
        session_root_dir: Optional[str] = None,
        engine: Optional[str] = None,
        visibility_timeout_ms: int = DEFAULT_VISIBILITY_TIMEOUT_MS,
        firefox_headless_mode: Optional[str] = None,
    ):
        self.platform = platform
        self.engine = resolve_browser_engine(engine)
        self.firefox_headless_mode = (
            resolve_firefox_headless_mode(firefox_headless_mode)
            if self.engine == "firefox"
            else DEFAULT_FIREFOX_HEADLESS_MODE
        )
        self._launcher = create_engine_launcher(
            self.engine,
            firefox_headless_mode=self.firefox_headless_mode,
        )
        self.visibility_timeout_ms = visibility_timeout_ms

        if headless is None:
            env_headless = os.getenv("HEADLESS", "false").lower()
            self.headless = env_headless in ("true", "1", "yes")
        else:
            self.headless = headless

        self.channel = channel or os.getenv("BROWSER_CHANNEL", "chromium")

        explicit_root = session_root_dir if session_root_dir is not None else os.getenv("SESSION_ROOT_DIR")
        if explicit_root is not None and explicit_root.strip():
            root_dir = os.path.abspath(explicit_root.strip())
        else:
            root_dir = str(get_project_root() / "sessions")
        profile_folder = self.platform if self.engine == "chromium" else f"{self.platform}-{self.engine}"
        self.user_data_dir = os.path.abspath(os.path.join(root_dir, profile_folder))
        print(f"[BrowserService] Diretorio de perfil de sessao: {self.user_data_dir}")

        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None

    def start_session(
        self,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        extra_args: Optional[List[str]] = None,
    ) -> BrowserContext:
        """
        Inicializa um contexto de navegador persistente e stealth de forma sincrona.
        Cria o diretorio de sessao se necessario.
        """
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.context = self._launcher.start(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            channel=self.channel,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            extra_args=extra_args,
        )
        self.playwright = getattr(self._launcher, "playwright", None)
        return self.context

    def get_page(self) -> Page:
        """
        Retorna a primeira pagina ativa do contexto persistente ou cria uma nova (sincrono).
        """
        if not self.context:
            raise RuntimeError(
                "Sessao do navegador nao iniciada. Chame 'start_session()' antes."
            )

        if self.context.pages:
            return self.context.pages[0]
        return self.context.new_page()

    def close(self) -> None:
        """
        Encerra com seguranca o contexto e o driver do motor ativo (sincrono),
        garantindo a persistencia do cache e cookies de sessao.
        """
        self._launcher.stop()
        self.context = None
        self.playwright = None

    def get_runtime_metadata(self) -> Dict[str, Any]:
        """
        Retorna metadados auditaveis da sessao ativa nos dois motores (Chromium e Firefox):
        - engine: 'chromium' ou 'firefox'
        - effective_mode: 'xvfb' | 'headless' | 'headed' (Chromium) ou 'xvfb' | 'headless-real' | 'headed' (Firefox)
        - xvfb_path: caminho do binario Xvfb se disponivel
        - browser_version: versao real do motor ou extraida do userAgent
        - user_agent: string navigator.userAgent observada na pagina ativa
        - webdriver: valor booleano de navigator.webdriver
        - plugins_length: contagem de navigator.plugins.length
        """
        if self.engine == "firefox":
            effective_mode = getattr(self._launcher, "effective_mode", None) or (
                "headed" if not self.headless else (
                    "headless-real" if self.firefox_headless_mode == "true_headless" else "xvfb"
                )
            )
            xvfb_path = getattr(self._launcher, "xvfb_path", None) or shutil.which("Xvfb")
        else:
            effective_mode = getattr(self._launcher, "effective_mode", None) or (
                "headless" if self.headless else "headed"
            )
            xvfb_path = getattr(self._launcher, "xvfb_path", None) or shutil.which("Xvfb")

        user_agent: Optional[str] = None
        browser_version: Optional[str] = None
        webdriver: Optional[bool] = None
        plugins_length: Optional[int] = None
        if self.context is not None:
            try:
                page = self.get_page()
                user_agent = page.evaluate("() => navigator.userAgent")
                webdriver = page.evaluate("() => navigator.webdriver")
                plugins_length = page.evaluate("() => navigator.plugins ? navigator.plugins.length : 0")
            except Exception:
                pass
            try:
                browser_obj = getattr(self.context, "browser", None)
                if browser_obj is not None and hasattr(browser_obj, "version"):
                    ver = browser_obj.version
                    browser_version = ver() if callable(ver) else str(ver)
            except Exception:
                browser_version = None

        if not browser_version and user_agent:
            for token in ("Firefox/", "Chrome/", "HeadlessChrome/"):
                if token in user_agent:
                    browser_version = user_agent.split(token, 1)[1].split(" ", 1)[0].strip()
                    break

        return {
            "engine": self.engine,
            "effective_mode": effective_mode,
            "xvfb_path": xvfb_path,
            "browser_version": browser_version,
            "user_agent": user_agent,
            "webdriver": webdriver,
            "plugins_length": plugins_length,
        }

    def verify_runtime_identity(self, target_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Trava de Identidade antes de qualquer sessao real (A1 e Decisao 2A):
        Para qualquer alvo que nao seja o clone local (host != 'localhost' e != '127.0.0.1'):
        O bot so inicia com janela real dentro de Xvfb e RECUSA iniciar se qualquer sinal
        verificavel denunciar automacao:
        - effective_mode deve ser estritamente 'xvfb';
        - /usr/bin/Xvfb deve estar presente;
        - 'HeadlessChrome' e proibido no user_agent;
        - user_agent deve ser consistente com o motor configurado;
        - navigator.webdriver deve ser False;
        - navigator.plugins.length deve ser maior que 0.
        Nenhuma variavel de ambiente desliga a trava. O clone local permanece livre.
        """
        meta = self.get_runtime_metadata()
        host = ""
        if target_url:
            from urllib.parse import urlsplit
            host = urlsplit(target_url).netloc.split(":")[0].strip().lower()

        is_local = host in ("localhost", "127.0.0.1", "")
        if is_local:
            logger.info(
                "Trava de Identidade (clone local: %s): engine=%s, effective_mode=%s, xvfb=%s, ua=%s, webdriver=%s",
                host or "default",
                meta["engine"],
                meta["effective_mode"],
                meta["xvfb_path"],
                meta["user_agent"],
                meta["webdriver"],
            )
            return meta

        engine = meta.get("engine")
        if engine not in VALID_ENGINES:
            raise RuntimeError(f"Trava de Identidade: Motor de navegador nao reconhecido: '{engine}'.")

        xvfb_path = meta.get("xvfb_path")
        if not xvfb_path or not shutil.which("Xvfb"):
            raise RuntimeError(
                "Trava de Identidade violada: Executavel 'Xvfb' ausente no PATH. Alvo externo exige janela real em Xvfb."
            )

        effective_mode = meta.get("effective_mode")
        if effective_mode != "xvfb":
            raise RuntimeError(
                f"Trava de Identidade violada: Alvo externo exige janela real dentro de Xvfb (effective_mode='xvfb'). "
                f"Modo detectado: '{effective_mode}'. Proibido modo headless ou janela sem Xvfb em alvos reais."
            )

        ua = meta.get("user_agent") or ""
        if "HeadlessChrome" in ua:
            raise RuntimeError(
                f"Trava de Identidade violada: Assinatura 'HeadlessChrome' detectada no User-Agent: '{ua}'."
            )

        if engine == "firefox" and "Firefox" not in ua:
            raise RuntimeError(
                f"Trava de Identidade violada: Motor configurado e 'firefox', mas User-Agent nao contem 'Firefox': '{ua}'."
            )
        if engine == "chromium" and "Chrome" not in ua:
            raise RuntimeError(
                f"Trava de Identidade violada: Motor configurado e 'chromium', mas User-Agent nao contem 'Chrome': '{ua}'."
            )

        if meta.get("webdriver") is True:
            raise RuntimeError("Trava de Identidade violada: navigator.webdriver verdadeiro detectado.")

        if meta.get("plugins_length") == 0:
            raise RuntimeError("Trava de Identidade violada: navigator.plugins vazio (length=0) denuncia automacao.")

        logger.info(
            "Trava de Identidade APROVADA para alvo externo (%s): engine=%s, effective_mode=%s, xvfb=%s, ua=%s, webdriver=%s, plugins=%s",
            host,
            meta["engine"],
            meta["effective_mode"],
            meta["xvfb_path"],
            meta["user_agent"],
            meta["webdriver"],
            meta["plugins_length"],
        )
        return meta

    def navigate(self, url: str, timeout: int = 30000, wait_until: str = "load") -> bool:
        """
        Navega de forma sincrona para a URL especificada utilizando a pagina ativa.
        Verifica a trava de identidade antes de qualquer navegacao externa.
        Retorna True em caso de sucesso ou False em caso de falha/timeout.
        """
        try:
            self.verify_runtime_identity(target_url=url)
            page = self.get_page()
            page.goto(url, timeout=timeout, wait_until=wait_until)
            return True
        except RuntimeError:
            raise
        except Exception as e:
            print(f"[BrowserService.navigate] Falha ao navegar para {url}: {e}")
            return False

    def get_current_url(self) -> str:
        """
        Retorna a URL corrente ativa da pagina no navegador.
        Permite a camada de aplicacao detectar desvios de dominio ou checkpoints.
        """
        try:
            return self.get_page().url
        except Exception:
            return ""

    def human_delay(self, min_s: float = 0.25, max_s: float = 0.65) -> float:
        """
        Aplica um atraso estocastico imitando a variancia de tempo de reacao humana
        utilizando distribuicao normal (gaussiana) truncada no intervalo [min_s, max_s].
        Elimina assinaturas de metronomo temporal nos logs de navegacao.
        """
        mean = (min_s + max_s) / 2.0
        std = (max_s - min_s) / 6.0
        delay = random.gauss(mean, std)
        delay = max(min_s, min(max_s, delay))
        time.sleep(delay)
        return delay

    def scroll_container(self, container_selector: str, steps: int = 5, delay: float = 0.5) -> bool:
        """
        Executa scroll incremental dentro de um container com overflow (para lazy loading de vagas).
        Elimina assinatura de metronomo variando os deltas de deslocamento e os intervalos com jitter estocastico.
        Retorna True se o container existir e for rolado; False caso contrario.
        """
        try:
            page = self.get_page()
            locator = page.locator(container_selector).first
            if locator.count() == 0 or not locator.is_visible():
                return False

            for _ in range(steps):
                jitter_factor = random.uniform(0.75, 1.15)
                locator.evaluate(
                    """
                    (el, factor) => {
                        const isDoc = el === document.body || el === document.documentElement;
                        const delta = (isDoc ? window.innerHeight : (el.clientHeight || 500)) * factor;
                        if (isDoc) {
                            window.scrollBy(0, delta);
                        } else {
                            el.scrollTop += delta;
                            el.dispatchEvent(new Event('scroll', { bubbles: true }));
                        }
                    }
                    """,
                    jitter_factor,
                )
                step_delay = delay * random.uniform(0.70, 1.30)
                page.wait_for_timeout(int(step_delay * 1000))
            return True
        except Exception as e:
            print(f"[BrowserService.scroll_container] Erro ao rolar container {container_selector}: {e}")
            return False

    def scroll_container_to_end(self, container_selector: str, steps: int = 5, delay: float = 0.5) -> None:
        """
        Rola o container ate o final (implementacao exigida pelo BrowserPort do Claude).
        """
        self.scroll_container(container_selector, steps=steps, delay=delay)

    def extract_links(self, card_selector: str, link_selector: str = "a") -> List[str]:
        """
        Extrai URLs unicas (absolutas) dos cards de vagas presentes no DOM atual.
        Preserva a ordem de aparicao e remove duplicadas.
        """
        try:
            page = self.get_page()
            raw_links = page.evaluate(
                """
                ({ cardSel, linkSel }) => {
                    const cards = document.querySelectorAll(cardSel);
                    const links = [];
                    cards.forEach(card => {
                        // Se o proprio card e um link com href
                        if (card.matches(linkSel) && card.href) {
                            links.push(card.href);
                            return;
                        }
                        // Busca o elemento de link interno
                        const linkEl = card.querySelector(linkSel);
                        if (linkEl && linkEl.href) {
                            links.push(linkEl.href);
                        }
                    });
                    return links;
                }
                """,
                {"cardSel": card_selector, "linkSel": link_selector},
            )

            seen = set()
            unique_links: List[str] = []
            for link in raw_links:
                cleaned = str(link).strip()
                if cleaned and cleaned not in seen:
                    seen.add(cleaned)
                    unique_links.append(cleaned)

            return unique_links
        except Exception as e:
            print(f"[BrowserService.extract_links] Erro ao extrair links com {card_selector}: {e}")
            return []

    def extract_job_cards(
        self,
        card_selector: str,
        title_selector: Optional[str] = None,
        company_selector: Optional[str] = None,
        link_selector: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Extrai cards completos com url, title e company conforme exigido pelo BrowserPort.
        Completamente agnostico: recebe seletores semanticos por parametro ou adota fallbacks
        estruturais genericos (classes que contem title/company, headings h1-h4, links).
        Nenhum seletor exclusivo do LinkedIn permanece fixo no motor.
        """
        try:
            self.wait_for_loader_to_disappear()
            page = self.get_page()
            cards_data = page.evaluate(
                """
                ({ cardSel, titleSel, compSel, linkSel }) => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        if (el.checkVisibility) {
                            return el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true });
                        }
                        const style = window.getComputedStyle(el);
                        return (
                            el.offsetParent !== null &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            style.opacity !== '0'
                        );
                    };

                    const cards = document.querySelectorAll(cardSel);
                    const result = [];
                    cards.forEach(card => {
                        if (!isVisible(card)) return;
                        const lSel = linkSel || 'a';
                        const linkEl = card.matches(lSel) ? card : card.querySelector(lSel);
                        const url = linkEl ? linkEl.href : '';

                        const tSel = titleSel || '[class*="title"], h1, h2, h3, h4, .title';
                        const titleEl = card.querySelector(tSel);
                        const title = titleEl ? titleEl.innerText.trim() : (linkEl ? linkEl.innerText.trim() : '');

                        let company = '';
                        if (compSel) {
                            const companyEl = card.querySelector(compSel);
                            company = companyEl ? companyEl.innerText.trim() : '';
                        }

                        if (url) {
                            result.push({ url, title, company });
                        }
                    });
                    return result;
                }
                """,
                {
                    "cardSel": card_selector,
                    "titleSel": title_selector,
                    "compSel": company_selector,
                    "linkSel": link_selector,
                },
            )
            return cards_data or []
        except Exception as e:
            print(f"[BrowserService.extract_job_cards] Erro ao extrair cards: {e}")
            return []

    def has_empty_required_inputs(self, modal_selector: str) -> bool:
        """
        Heuristica 3C (Inspetor Previo de Inputs no DOM):
        Inspeciona no container do modal APENAS elementos visiveis procurando:
        - input[required] ou [aria-required="true"] vazio (exceto radio/checkbox/submit/button/hidden)
        - input[type="checkbox"] obrigatorio nao marcado
        - grupos de input[type="radio"] obrigatorios sem nenhuma opcao :checked
        - textarea[required] ou [aria-required="true"] vazio
        - select[required] ou [aria-required="true"] sem opcao valida selecionada

        Retorna True se detectar QUALQUER campo obrigatorio vazio (complexidade alta); False caso contrario.
        """
        try:
            self.wait_for_loader_to_disappear()
            page = self.get_page()
            modal_locator = page.locator(modal_selector).first
            if modal_locator.count() == 0 or not modal_locator.is_visible():
                return False

            has_empty = modal_locator.evaluate(
                """
                (modal) => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        if (el.checkVisibility && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) {
                            return false;
                        }
                        const style = window.getComputedStyle(el);
                        if (
                            el.offsetParent === null ||
                            style.display === 'none' ||
                            style.visibility === 'hidden' ||
                            parseFloat(style.opacity) === 0
                        ) {
                            return false;
                        }
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0 && rect.right > 0 && rect.bottom > 0;
                    };

                    // 1. Text inputs, email, tel, number, url, search, password
                    const textInputs = modal.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="radio"]):not([type="checkbox"])');
                    for (const inp of textInputs) {
                        const isRequired = inp.hasAttribute('required') || inp.getAttribute('aria-required') === 'true';
                        if (isRequired && isVisible(inp)) {
                            if (!inp.value || inp.value.trim() === '') {
                                return true;
                            }
                        }
                    }

                    // 2. Checkboxes obrigatorios
                    const checkboxes = modal.querySelectorAll('input[type="checkbox"]');
                    for (const cb of checkboxes) {
                        const isRequired = cb.hasAttribute('required') || cb.getAttribute('aria-required') === 'true';
                        if (isRequired && isVisible(cb) && !cb.checked) {
                            return true;
                        }
                    }

                    // 3. Grupos de Radio obrigatorios
                    const radios = modal.querySelectorAll('input[type="radio"]');
                    const radioGroups = new Map();
                    for (const rd of radios) {
                        const name = rd.getAttribute('name') || 'unnamed';
                        if (!radioGroups.has(name)) {
                            radioGroups.set(name, []);
                        }
                        radioGroups.get(name).push(rd);
                    }

                    for (const [name, group] of radioGroups.entries()) {
                        const isGroupRequired = group.some(rd => rd.hasAttribute('required') || rd.getAttribute('aria-required') === 'true');
                        const anyVisible = group.some(rd => isVisible(rd));
                        if (isGroupRequired && anyVisible) {
                            const anyChecked = group.some(rd => rd.checked);
                            if (!anyChecked) {
                                return true;
                            }
                        }
                    }

                    // 4. Textareas
                    const textareas = modal.querySelectorAll('textarea');
                    for (const ta of textareas) {
                        const isRequired = ta.hasAttribute('required') || ta.getAttribute('aria-required') === 'true';
                        if (isRequired && isVisible(ta)) {
                            if (!ta.value || ta.value.trim() === '') {
                                return true;
                            }
                        }
                    }

                    // 5. Selects
                    const selects = modal.querySelectorAll('select');
                    for (const sel of selects) {
                        const isRequired = sel.hasAttribute('required') || sel.getAttribute('aria-required') === 'true';
                        if (isRequired && isVisible(sel)) {
                            if (sel.selectedIndex === -1 || !sel.value || sel.value.trim() === '') {
                                return true;
                            }
                        }
                    }

                    return false;
                }
                """
            )
            return bool(has_empty)
        except Exception as e:
            print(f"[BrowserService.has_empty_required_inputs] Erro ao inspecionar modal {modal_selector}: {e}")
            return False

    def _resolve_visible_locator(self, selector: str, timeout: int = 5000):
        """
        Resolve o primeiro locator genuinamente visivel para um humano (filtrando honeypots com
        display:none, visibility:hidden, opacity:0, pointer-events:none ou posicionados off-screen).
        """
        self.wait_for_loader_to_disappear()
        self.dismiss_overlay_if_present()
        page = self.get_page()
        group = page.locator(selector)
        deadline = time.time() + (timeout / 1000.0)
        while time.time() < deadline:
            count = group.count()
            for i in range(count):
                candidate = group.nth(i)
                try:
                    is_human_vis = candidate.evaluate(
                        """(el) => {
                            if (!el) return false;
                            if (el.checkVisibility && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) {
                                return false;
                            }
                            const style = window.getComputedStyle(el);
                            if (
                                el.offsetParent === null && style.position !== 'fixed' ||
                                style.display === 'none' ||
                                style.visibility === 'hidden' ||
                                parseFloat(style.opacity) === 0 ||
                                style.pointerEvents === 'none'
                            ) {
                                return false;
                            }
                            const rect = el.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0 && rect.right > 0 && rect.bottom > 0;
                        }"""
                    )
                    if is_human_vis:
                        return candidate
                except Exception:
                    continue
            page.wait_for_timeout(100)
        return None

    def click_element(self, selector: str, timeout: int = 5000, humanized: bool = True) -> bool:
        """
        Clica em um elemento aplicando cinematica humana:
        1. Aguarda que o elemento fique genuinamente visivel (ignorando honeypots).
        2. Aplica atraso estocastico de reacao humana (200ms a 450ms).
        3. Obtem o bounding box e seleciona uma coordenada com desvio estocastico seguro (20% a 80%).
        4. Move o mouse suavemente em multiplos passos (steps) para evitar teletransporte.
        5. Aplica hold-time realista entre mouse.down() e mouse.up() (60ms a 120ms).
        Retorna True se clicou com sucesso; False em caso de timeout ou erro.
        """
        try:
            page = self.get_page()
            locator = self._resolve_visible_locator(selector, timeout=timeout)
            if locator is None:
                return False

            if humanized:
                self.human_delay(0.20, 0.45)
                box = locator.bounding_box()
                if box and box.get("width", 0) > 0 and box.get("height", 0) > 0:
                    target_x = box["x"] + box["width"] * random.uniform(0.20, 0.80)
                    target_y = box["y"] + box["height"] * random.uniform(0.20, 0.80)

                    steps = random.randint(3, 8)
                    page.mouse.move(target_x, target_y, steps=steps)

                    page.mouse.down()
                    time.sleep(random.uniform(0.06, 0.12))
                    page.mouse.up()
                    return True

            locator.click(timeout=timeout)
            return True
        except Exception as e:
            print(f"[BrowserService.click_element] Nao foi possivel clicar em {selector}: {e}")
            return False

    def modal_signature(self, container_selector: str) -> str:
        """
        Calcula um hash deterministico SHA-256 do conteudo visivel do container (v0.8).
        Permite a camada de aplicacao detectar ausência de transicao de estado no modal.
        """
        try:
            self.wait_for_loader_to_disappear()
            page = self.get_page()
            locator = page.locator(container_selector).first
            if locator.count() == 0 or not locator.is_visible():
                return ""
            text = locator.inner_text()
            return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
        except Exception as e:
            print(f"[BrowserService.modal_signature] Erro ao obter assinatura do modal {container_selector}: {e}")
            return ""

    def is_visible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Verifica se um seletor esta genuinamente visivel na pagina dentro do timeout estipulado.
        """
        effective_timeout = self.visibility_timeout_ms if timeout is None else timeout
        try:
            locator = self._resolve_visible_locator(selector, timeout=effective_timeout)
            return locator is not None
        except Exception:
            return False

    def wait_until_hidden(
        self, selector: str = '[role="status"]', timeout: int = 15000
    ) -> bool:
        """
        Espera deterministica (sem sleep) pelo sumico/descarte de um elemento ou transicao assincrona.
        True se o elemento nao existia ou sumiu antes de `timeout` ms; False se continuou visivel.
        """
        try:
            page = self.get_page()
            locator = page.locator(selector).first
            if locator.count() == 0 or not locator.is_visible():
                return True
            locator.wait_for(state="detached", timeout=timeout)
            return True
        except Exception:
            # Fallback caso fique hidden em vez de detached
            try:
                locator.wait_for(state="hidden", timeout=min(timeout, 1000))
                return True
            except Exception:
                return False

    wait_for_loader_to_disappear = wait_until_hidden

    def job_shows_applied(self, selector: str, timeout: int = 0) -> bool:
        """
        Porta para inspecionar se a pagina mostra a vaga como JA CANDIDATADA (C2/A3).
        - timeout <= 0: leitura instantanea sem espera por visibilidade (usado ao abrir a vaga).
        - timeout > 0: espera pela visibilidade ate o prazo (usado apos envio ou sem apply button).
        - Falha de protocolo/pagina fechada/navegacao propaga excecao (nao devolve False).
        """
        if not selector or not str(selector).strip():
            return False

        page = self.get_page()
        locator = page.locator(selector).first

        if timeout <= 0:
            if locator.count() == 0:
                return False
            try:
                return bool(
                    locator.evaluate(
                        """(el) => {
                            if (!el) return false;
                            if (el.checkVisibility) {
                                return el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true });
                            }
                            const style = window.getComputedStyle(el);
                            return (
                                el.offsetParent !== null &&
                                style.display !== 'none' &&
                                style.visibility !== 'hidden' &&
                                parseFloat(style.opacity) !== 0
                            );
                        }"""
                    )
                )
            except Exception as exc:
                err_msg = str(exc).lower()
                if "target page" in err_msg or "closed" in err_msg or "destroyed" in err_msg or "navigation" in err_msg:
                    raise
                return False

        # timeout > 0: espera dinamica pelo surgimento/visibilidade do seletor
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception as exc:
            err_msg = str(exc).lower()
            if "timeout" in err_msg:
                return False
            if "target page" in err_msg or "closed" in err_msg or "destroyed" in err_msg or "navigation" in err_msg:
                raise
            return False

    def dismiss_overlay_if_present(
        self, dismiss_selector: str = '[aria-label="Dismiss overlay"]', timeout: int = 2000
    ) -> bool:
        """
        Detecta e descarta overlays intrusivos de alto z-index (ex: banners de cookies/privacidade)
        que bloqueiam interacoes no viewport principal.
        """
        try:
            page = self.get_page()
            locator = page.locator(dismiss_selector).first
            if locator.count() > 0 and locator.is_visible():
                locator.click(timeout=timeout)
                return True
            return False
        except Exception:
            return False

    # Aliases de conveniencia para maxima interoperabilidade com AppService / BrowserPort
    open_url = navigate
    element_exists = is_visible
    click = click_element
    current_url = get_current_url
