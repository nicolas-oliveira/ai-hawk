import os
import shutil
from typing import Optional, List
from dotenv import load_dotenv
from patchright.async_api import async_playwright, BrowserContext, Page, Playwright

load_dotenv()


class BrowserService:
    """
    Serviço de Infraestrutura para gerenciamento do navegador via Patchright.
    Totalmente agnóstico de plataforma, gerencia sessões persistentes com stealth nativo.
    """

    def __init__(
        self,
        platform: str = "default",
        headless: Optional[bool] = None,
        channel: Optional[str] = None,
        session_root_dir: Optional[str] = None,
    ):
        self.platform = platform
        
        # Leitura de variáveis de ambiente com fallbacks defensivos
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

    async def start_session(
        self,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        extra_args: Optional[List[str]] = None,
    ) -> BrowserContext:
        """
        Inicializa um contexto de navegador persistente e stealth.
        Cria o diretório de sessão se necessário.
        """
        os.makedirs(self.user_data_dir, exist_ok=True)

        self.playwright = await async_playwright().start()

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

        self.context = await self.playwright.chromium.launch_persistent_context(
            **launch_kwargs
        )
        return self.context

    async def get_page(self) -> Page:
        """
        Retorna a primeira página ativa do contexto persistente ou cria uma nova.
        """
        if not self.context:
            raise RuntimeError(
                "Sessao do navegador nao iniciada. Chame 'start_session()' antes."
            )

        if self.context.pages:
            return self.context.pages[0]
        return await self.context.new_page()

    async def close(self) -> None:
        """
        Encerra com segurança o contexto e o driver do Patchright,
        garantindo a persistência do cache e cookies de sessão.
        """
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
            self.context = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
