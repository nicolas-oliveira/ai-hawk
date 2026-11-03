import os
import sys
import json
import argparse
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Garante o import limpo da raiz do projeto sem acoplamentos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from src.infrastructure.browser_service import BrowserService
from src.infrastructure.paths import get_project_root

DEFAULT_CACHE_PATH = str(get_project_root() / ".cache" / "jobs_history.json")


def resolve_cli_options(argv: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Resolve opcoes de seguranca da CLI (Regras 1A e 2A):
    - 1A: Envio real (shadow_mode=False) recusa rodar sem cache de historico.
    - 2A: strict_abort ligado por padrao; desligar exige opcao explicita (--no-strict-abort ou STRICT_ABORT=false).
    """
    parser = argparse.ArgumentParser(description="AIHawk CLI", add_help=False)
    parser.add_argument("--shadow-mode", action="store_true", help="Ativa modo simulacao sem envio real")
    parser.add_argument("--no-strict-abort", action="store_true", help="Desliga parada estrita explicitamente")
    parser.add_argument("--no-cache", action="store_true", help="Desativa cache de historico (permitido apenas em shadow mode)")
    parser.add_argument("--cache-path", type=str, default=None, help="Caminho para o JSON de cache de historico")
    args, _ = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    env_shadow = os.getenv("SHADOW_MODE", "false").strip().lower() in ("true", "1", "yes")
    shadow_mode = bool(args.shadow_mode or env_shadow)

    env_strict_raw = os.getenv("STRICT_ABORT", "true").strip().lower()
    env_strict_disabled = env_strict_raw in ("false", "0", "no")
    strict_abort = not (args.no_strict_abort or env_strict_disabled)

    env_cache_enabled = os.getenv("JOB_CACHE_ENABLED", "true").strip().lower() not in ("false", "0", "no")
    explicit_cache = args.cache_path if args.cache_path is not None else os.getenv("JOB_CACHE_PATH")
    if explicit_cache is not None and explicit_cache.strip():
        resolved_cache = os.path.abspath(explicit_cache.strip())
    else:
        resolved_cache = str(get_project_root() / ".cache" / "jobs_history.json")
    cache_enabled = bool(env_cache_enabled and not args.no_cache and resolved_cache)

    if not shadow_mode and not cache_enabled:
        raise ValueError(
            "Regra 1A violada: Envio real recusa rodar sem cache de historico. "
            "Mantenha o cache ativo ou execute com --shadow-mode."
        )

    return {
        "shadow_mode": shadow_mode,
        "strict_abort": strict_abort,
        "cache_enabled": cache_enabled,
        "cache_path": resolved_cache if cache_enabled else None,
    }


def resolve_selector_profile(platform: str) -> Dict[str, str]:
    """
    Busca o dicionario de seletores da plataforma no SELECTOR_PROFILES exportado pelo DTO.
    Se a plataforma nao for suportada, levanta ValueError explicito.
    """
    from src.application.dtos import search_request as sr_module

    normalized = (platform or "").strip().lower()
    profiles = getattr(sr_module, "SELECTOR_PROFILES", None)
    if not isinstance(profiles, dict):
        default_linkedin = getattr(sr_module, "LINKEDIN_DEFAULT_SELECTORS", None)
        profiles = {"linkedin": default_linkedin} if isinstance(default_linkedin, dict) else {}

    if normalized not in profiles:
        available = ", ".join(sorted(profiles.keys())) or "nenhum"
        raise ValueError(
            f"Plataforma '{platform}' nao suportada em SELECTOR_PROFILES. "
            f"Perfis disponiveis: {available}."
        )
    return profiles[normalized]


def bootstrap():
    """
    Ponto de entrada do AIHawk CLI.
    Execucao 100% sincrona, linear e previsivel.
    Instancia a infraestrutura, resolve o perfil de seletores por PLATFORM,
    injeta no AppService / AppController e dispara a orquestracao.
    """
    print("==================================================")
    print("AIHawk v0.5 - Motor de Candidaturas Easy Apply Seco")
    print("==================================================")

    platform = os.getenv("PLATFORM", "linkedin").strip().lower()
    headless_env = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    channel = os.getenv("BROWSER_CHANNEL", "chromium")
    max_apps = int(os.getenv("MAX_APPLICATIONS", "10"))

    raw_urls = os.getenv(
        "STATIC_URLS",
        "https://www.linkedin.com/jobs/search/?f_AL=true&keywords=python",
    )
    if raw_urls.strip().startswith("["):
        try:
            static_urls = json.loads(raw_urls)
        except Exception:
            static_urls = [u.strip() for u in raw_urls.split(",") if u.strip()]
    else:
        static_urls = [u.strip() for u in raw_urls.split(",") if u.strip()]

    # Valida opcoes 1A (cache obrigatorio em envio real) e 2A (strict_abort padrao)
    cli_opts = resolve_cli_options()

    # Valida e resolve o perfil de seletores da plataforma antes de subir o navegador
    selectors = resolve_selector_profile(platform)

    browser_service = BrowserService(platform=platform, headless=headless_env, channel=channel)

    print(f"[-] Plataforma: {platform}")
    print(f"[-] Motor: {browser_service.engine}")
    print(f"[-] Diretorio de Sessao: {browser_service.user_data_dir}")
    print(f"[-] Headless: {browser_service.headless}")
    print(f"[-] Canal: {browser_service.channel}")
    print(f"[-] Strict Abort (2A): {cli_opts['strict_abort']}")
    print(f"[-] Shadow Mode: {cli_opts['shadow_mode']}")
    print(f"[-] Cache de Historico (1A): {cli_opts['cache_path'] or 'DESATIVADO (Shadow Mode)'}")
    print(f"[-] URLs Alvo: {static_urls}")
    print(f"[-] Max Candidaturas: {max_apps}")

    try:
        browser_service.start_session()

        # Injecao de Dependencias da Arquitetura Limpa
        try:
            from src.application.app_controller import AppController
            from src.application.app_service import AppService, JsonJobCache
            from src.application.dtos.search_request import SearchRequest

            job_cache = JsonJobCache(cli_opts["cache_path"]) if cli_opts["cache_enabled"] else None
            app_service = AppService(browser_service, cache=job_cache)
            app_controller = AppController(app_service=app_service)

            request = SearchRequest(
                platform=platform,
                static_urls=static_urls,
                selectors=selectors,
                max_applications=max_apps,
                strict_abort=cli_opts["strict_abort"],
                shadow_mode=cli_opts["shadow_mode"],
            )

            print("[*] Disparando loop de candidatura atraves do AppController...")
            if hasattr(app_controller, "execute"):
                summary = app_controller.execute(request)
                print(f"\n{summary}")
            else:
                result = app_controller.run(request)
                print("\n==================================================")
                print("[+] Relatorio Final da Execucao:")
                print(f"    - Total Processadas: {getattr(result, 'total_processed', len(getattr(result, 'jobs', [])))}")
                print(f"    - Aplicadas (APPLIED): {getattr(result, 'applied_count', 0)}")
                print(f"    - Ignoradas Complexas (SKIPPED_COMPLEX): {getattr(result, 'skipped_count', 0)}")
                print(f"    - Ja Aplicadas (ALREADY_APPLIED): {getattr(result, 'already_applied_count', 0)}")
                print("==================================================")

        except (ImportError, AttributeError, NotImplementedError, TypeError) as err:
            print(f"[!] Camada de aplicacao (AppController/AppService) em desenvolvimento pelo Claude: {err}")
            print("[*] Executando smoke test basico da infraestrutura sincrona...")
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
