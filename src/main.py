import os
import sys
import json
from dotenv import load_dotenv

# Garante o import limpo da raiz do projeto sem acoplamentos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from src.infrastructure.browser_service import BrowserService


def bootstrap():
    """
    Ponto de entrada do AIHawk CLI (v0.5 - Loop Easy Apply Seco).
    Execucao 100% sincrona, linear e previsivel.
    Instancia a infraestrutura, injeta no AppService / AppController e dispara a orquestracao.
    """
    print("==================================================")
    print("AIHawk v0.5 - Motor de Candidaturas Easy Apply Seco")
    print("==================================================")

    platform = os.getenv("PLATFORM", "linkedin")
    headless_env = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    channel = os.getenv("BROWSER_CHANNEL", "chromium")
    max_apps = int(os.getenv("MAX_APPLICATIONS", "10"))
    
    raw_urls = os.getenv("STATIC_URLS", "https://www.linkedin.com/jobs/search/?f_AL=true&keywords=python")
    if raw_urls.strip().startswith("["):
        try:
            static_urls = json.loads(raw_urls)
        except Exception:
            static_urls = [u.strip() for u in raw_urls.split(",") if u.strip()]
    else:
        static_urls = [u.strip() for u in raw_urls.split(",") if u.strip()]

    browser_service = BrowserService(platform=platform, headless=headless_env, channel=channel)

    print(f"[-] Plataforma: {platform}")
    print(f"[-] Diretorio de Sessao: {browser_service.user_data_dir}")
    print(f"[-] Headless: {browser_service.headless}")
    print(f"[-] Canal: {browser_service.channel}")
    print(f"[-] URLs Alvo: {static_urls}")
    print(f"[-] Max Candidaturas: {max_apps}")

    try:
        browser_service.start_session()

        # Injecao de Dependencias da Arquitetura Limpa
        try:
            from src.application.app_controller import AppController
            from src.application.app_service import AppService
            from src.application.dtos.search_request import SearchRequest, LINKEDIN_DEFAULT_SELECTORS

            # Instancia o servico e o controller com o browser_service real
            app_service = AppService(browser_service=browser_service)
            app_controller = AppController(app_service=app_service)

            request = SearchRequest(
                platform=platform,
                static_urls=static_urls,
                selectors=LINKEDIN_DEFAULT_SELECTORS,
                max_applications=max_apps,
            )

            print("[*] Disparando loop de candidatura atraves do AppController...")
            result = app_controller.run(request)
            print("\n==================================================")
            print(f"[+] Relatorio Final da Execucao:")
            print(f"    - Total Processadas: {getattr(result, 'total_processed', len(getattr(result, 'jobs', [])))}")
            print(f"    - Aplicadas (APPLIED): {getattr(result, 'applied_count', 0)}")
            print(f"    - Ignoradas Complexas (SKIPPED_COMPLEX): {getattr(result, 'skipped_count', 0)}")
            print(f"    - Ja Aplicadas (ALREADY_APPLIED): {getattr(result, 'already_applied_count', 0)}")
            print("==================================================")

        except (ImportError, AttributeError, NotImplementedError, TypeError) as err:
            print(f"[!] Camada de aplicacao (AppController/AppService) em desenvolvimento pelo Claude: {err}")
            print("[*] Executando smoke test basico da infraestrutura síncrona...")
            page = browser_service.get_page()
            page.goto("https://example.com", wait_until="domcontentloaded")
            print(f"[+] Infraestrutura operacional. Pagina ativa: '{page.title()}'")

    except Exception as e:
        print(f"[!] Erro critico durante execucao: {e}")
        raise e
    finally:
        print("[*] Encerrando sessao do navegador e gravando dados de perfil...")
        browser_service.close()
        print("[+] Sessao encerrada com sucesso.")


if __name__ == "__main__":
    bootstrap()
