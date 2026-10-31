import asyncio
import os
import sys

# Garante o import limpo da raiz do projeto sem acoplamentos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.browser_service import BrowserService


async def bootstrap():
    """
    Ponto de entrada do AIHawk CLI (v0.1 - Foundation & Stealth Engine).
    Valida inicialização, persistência de sessão e fechamento seguro da infraestrutura.
    """
    print("==================================================")
    print("AIHawk v0.1 - Inicializando Infraestrutura Stealth")
    print("==================================================")

    # Instancia com a plataforma de teste e configurações lidas do .env
    browser_service = BrowserService(platform="test_session")

    print(f"[-] Diretorio de Sessao: {browser_service.user_data_dir}")
    print(f"[-] Headless: {browser_service.headless}")
    print(f"[-] Canal: {browser_service.channel}")

    try:
        print("[*] Iniciando contexto persistente...")
        context = await browser_service.start_session()
        page = await browser_service.get_page()

        test_url = "https://example.com"
        print(f"[*] Navegando para {test_url}...")
        await page.goto(test_url, wait_until="domcontentloaded")

        title = await page.title()
        print(f"[+] Pagina carregada com sucesso! Titulo: '{title}'")

        # Injeta um valor no localStorage para atestar persistencia
        await page.evaluate("localStorage.setItem('aihawk_probe', 'v0.1_persistence_verified')")
        probe_val = await page.evaluate("localStorage.getItem('aihawk_probe')")
        print(f"[+] Verificacao de Storage: probe_val='{probe_val}'")

    except Exception as e:
        print(f"[!] Erro durante execucao: {e}")
        raise e
    finally:
        print("[*] Encerrando sessao do navegador e gravando dados de perfil...")
        await browser_service.close()
        print("[+] Sessao encerrada com sucesso.")


if __name__ == "__main__":
    asyncio.run(bootstrap())
