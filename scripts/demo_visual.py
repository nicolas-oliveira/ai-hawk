"""Demo visual: roda o robô com janela aberta contra o servidor local de armadilhas."""
import os, sys, tempfile, threading
from http.server import HTTPServer
sys.path.insert(0, os.getcwd())
from tests.real.conftest import RealStressHTTPHandler
from src.infrastructure.browser_service import BrowserService
from src.application.app_service import AppService
from src.application.app_controller import AppController
from src.application.dtos.search_request import SearchRequest, LINKEDIN_DEFAULT_SELECTORS

server = HTTPServer(("127.0.0.1", 0), RealStressHTTPHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"
headless = os.getenv("DEMO_HEADLESS", "false") == "true"
tmp = tempfile.mkdtemp()
browser = BrowserService(platform="demo", headless=headless, channel="chromium", session_root_dir=tmp)
browser.start_session()
try:
    req = SearchRequest(platform="linkedin", static_urls=[f"{base}/jobs/search"],
                        selectors=LINKEDIN_DEFAULT_SELECTORS, max_applications=2)
    print(AppController(AppService(browser), reports_dir=os.path.join(tmp, "reports")).execute(req))
    if not headless:
        input("\nResultado acima. ENTER para fechar a janela...")
finally:
    browser.close(); server.shutdown()
