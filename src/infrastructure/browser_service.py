import os
import shutil
import time
import random
import hashlib
from typing import Optional, List, Dict, Any
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

    def navigate(self, url: str, timeout: int = 30000, wait_until: str = "load") -> bool:
        """
        Navega de forma sincrona para a URL especificada utilizando a pagina ativa.
        Retorna True em caso de sucesso ou False em caso de falha/timeout.
        """
        try:
            page = self.get_page()
            page.goto(url, timeout=timeout, wait_until=wait_until)
            return True
        except Exception as e:
            print(f"[BrowserService.navigate] Falha ao navegar para {url}: {e}")
            return False

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
                        const delta = (el.clientHeight || 500) * factor;
                        el.scrollTop += delta;
                        el.dispatchEvent(new Event('scroll', { bubbles: true }));
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
            page = self.get_page()
            cards_data = page.evaluate(
                """
                ({ cardSel, titleSel, compSel, linkSel }) => {
                    const cards = document.querySelectorAll(cardSel);
                    const result = [];
                    cards.forEach(card => {
                        const lSel = linkSel || 'a';
                        const linkEl = card.matches(lSel) ? card : card.querySelector(lSel);
                        const url = linkEl ? linkEl.href : '';

                        const tSel = titleSel || '[class*="title"], h1, h2, h3, h4, .title';
                        const titleEl = card.querySelector(tSel);
                        const title = titleEl ? titleEl.innerText.trim() : (linkEl ? linkEl.innerText.trim() : 'Vaga');

                        const cSel = compSel || '[class*="company"], [class*="subtitle"], [class*="description"], .company, .subtitle, p, span';
                        const companyEl = card.querySelector(cSel);
                        const company = companyEl ? companyEl.innerText.trim() : 'Empresa';

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
            page = self.get_page()
            modal_locator = page.locator(modal_selector).first
            if modal_locator.count() == 0 or not modal_locator.is_visible():
                return False

            has_empty = modal_locator.evaluate(
                """
                (modal) => {
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

    def click_element(self, selector: str, timeout: int = 5000, humanized: bool = True) -> bool:
        """
        Clica em um elemento aplicando cinematica humana:
        1. Aguarda que o elemento fique visivel.
        2. Aplica atraso estocastico de reacao humana (200ms a 450ms).
        3. Obtem o bounding box e seleciona uma coordenada com desvio estocastico seguro (20% a 80%).
        4. Move o mouse suavemente em multiplos passos (steps) para evitar teletransporte.
        5. Aplica hold-time realista entre mouse.down() e mouse.up() (60ms a 120ms).
        Retorna True se clicou com sucesso; False em caso de timeout ou erro.
        """
        try:
            page = self.get_page()
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)

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
            page = self.get_page()
            locator = page.locator(container_selector).first
            if locator.count() == 0 or not locator.is_visible():
                return ""
            text = locator.inner_text()
            return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
        except Exception as e:
            print(f"[BrowserService.modal_signature] Erro ao obter assinatura do modal {container_selector}: {e}")
            return ""

    def is_visible(self, selector: str, timeout: int = 3000) -> bool:
        """
        Verifica se um seletor esta visivel na pagina dentro do timeout estipulado.
        """
        try:
            page = self.get_page()
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for_loader_to_disappear(
        self, loader_selector: str = '[role="status"]', timeout: int = 15000
    ) -> bool:
        """
        Espera deterministica por descarte/sumico de loaders e transicoes assincronas.
        Elimina 'Flaky Tests' causados por variacoes de latencia ou carga de CPU sem usar time.sleep().
        Retorna True se o loader nao existir ou sumir antes do timeout; False se continuar visivel.
        """
        try:
            page = self.get_page()
            locator = page.locator(loader_selector).first
            if locator.count() == 0 or not locator.is_visible():
                return True
            locator.wait_for(state="detached", timeout=timeout)
            return True
        except Exception:
            # Fallback caso fique hidden em vez de detached
            try:
                locator.wait_for(state="hidden", timeout=1000)
                return True
            except Exception:
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
                return self.click_element(dismiss_selector, timeout=timeout, humanized=False)
            return False
        except Exception:
            return False

    # Aliases de conveniencia para maxima interoperabilidade com AppService / BrowserPort
    open_url = navigate
    element_exists = is_visible
    click = click_element
