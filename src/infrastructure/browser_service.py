import os
import shutil
from typing import Optional, List
from dotenv import load_dotenv
from patchright.sync_api import sync_playwright, BrowserContext, Page, Playwright

load_dotenv()


class BrowserService:
    """
    Servico de Infraestrutura para gerenciamento do navegador via Patchright (API Sincrona).
    Totalmente agnostico de plataforma, linear, com sessoes persistentes e stealth nativo.
    """

    def __init__(
        self,
        platform: str = "default",
        headless: Optional[bool] = None,
        channel: Optional[str] = None,
        session_root_dir: Optional[str] = None,
    ):
        self.platform = platform

        # Leitura de variaveis de ambiente com fallbacks defensivos
        if headless is None:
            env_headless = os.getenv("HEADLESS", "false").lower()
            self.headless = env_headless in ("true", "1", "yes")
        else:
            self.headless = headless

        self.channel = channel or os.getenv("BROWSER_CHANNEL", "chromium")

        root_dir = session_root_dir or os.getenv("SESSION_ROOT_DIR", "./sessions")
        self.user_data_dir = os.path.abspath(os.path.join(root_dir, self.platform))

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

        self.playwright = sync_playwright().start()

        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        if extra_args:
            args.extend(extra_args)

        launch_kwargs = {
            "user_data_dir": self.user_data_dir,
            "headless": self.headless,
            "args": args,
            "viewport": {"width": viewport_width, "height": viewport_height},
        }

        # Se channel for 'chrome', tenta usar o canal Chrome nativo do sistema
        if self.channel == "chrome" and shutil.which("google-chrome"):
            launch_kwargs["channel"] = "chrome"

        self.context = self.playwright.chromium.launch_persistent_context(
            **launch_kwargs
        )
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
        Encerra com seguranca o contexto e o driver do Patchright (sincrono),
        garantindo a persistencia do cache e cookies de sessao.
        """
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
