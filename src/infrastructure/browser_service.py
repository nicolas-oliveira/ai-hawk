import os
from patchright.async_api import async_playwright


class BrowserService:
    def __init__(self):
        self.user_data_dir = "./linkedin_session"
        self.playwright = None
        self.browser = None

    async def start_persistent_session(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=False,
            channel="chrome",  # Aponta para o Chrome local do Ubuntu
            args=["--disable-blink-features=AutomationControlled"]
        )
        return self.browser

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()