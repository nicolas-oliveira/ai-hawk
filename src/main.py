import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.browser_service import BrowserService


async def bootstrap():
    print("Iniciando o ecossistema do AIHawk...")
    browser_service = BrowserService()

    try:
        context = await browser_service.start_persistent_session()
        page = await context.new_page()

        print("Acessando o LinkedIn...")
        await page.goto("https://www.linkedin.com/login")

        print("\n--- AÇÃO NECESSÁRIA ---")
        print("1. Faça o login manualmente na janela do navegador que se abriu.")
        print("2. Resolva qualquer desafio de segurança.")
        print("3. Quando visualizar o seu Feed, volte a este terminal.")

        input("Pressione ENTER aqui no terminal para salvar a sessão e desligar o motor...")

    finally:
        await browser_service.close()
        print("Sessão salva. Motor encerrado com sucesso.")


if __name__ == "__main__":
    asyncio.run(bootstrap())