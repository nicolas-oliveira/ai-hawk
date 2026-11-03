"""Fakes compartilhados da camada de aplicacao (porta falsa, sem navegador real)."""
from typing import Callable, Dict, List, Optional

from src.application.dtos.search_request import LINKEDIN_DEFAULT_SELECTORS

SEL: Dict[str, str] = dict(LINKEDIN_DEFAULT_SELECTORS)


def cards(*ids: int) -> List[Dict[str, str]]:
    return [{"url": f"https://x.com/jobs/{i}", "title": "t", "company": "c"} for i in ids]


class FakeBrowser:
    """Implementa o BrowserPort. `visible` = seletores visiveis; `exists` (opcional)
    decide dinamicamente e recebe o proprio fake; `on_click` reage a um clique."""

    def __init__(
        self,
        visible=(),
        job_cards: Optional[List[Dict[str, str]]] = None,
        exists: Optional[Callable[["FakeBrowser", str], bool]] = None,
        current_url: Optional[Callable[["FakeBrowser"], str]] = None,
        click_raises=(),
    ) -> None:
        self.visible = set(visible)
        self.job_cards = cards(1, 2) if job_cards is None else job_cards
        self._exists = exists
        self._current_url = current_url
        self.click_raises = set(click_raises)
        self.on_click: Dict[str, Callable[["FakeBrowser"], None]] = {}
        self.clicks: List[str] = []
        self.opened: List[str] = []

    def open_url(self, url): self.opened.append(url)
    def scroll_container_to_end(self, sel): pass
    def extract_job_cards(self, card_selector, title_selector=None, company_selector=None):
        return self.job_cards
    def has_empty_required_inputs(self, sel): return False
    def modal_signature(self, sel): return ""
    def dismiss_overlay_if_present(self, sel, timeout): return False
    def wait_for_loader_to_disappear(self, sel, timeout): return True

    def get_current_url(self):
        if self._current_url:
            return self._current_url(self)
        return self.opened[-1] if self.opened else ""

    def element_exists(self, sel):
        return self._exists(self, sel) if self._exists else sel in self.visible

    def click(self, sel):
        self.clicks.append(sel)
        if sel in self.click_raises:
            raise RuntimeError("timeout")
        if sel in self.on_click:
            self.on_click[sel](self)


class FakeCache:
    """JobCache em memoria. `saved` registra cada put; `events` (opcional, lista
    compartilhada com outros fakes) registra a ordem das chamadas."""

    def __init__(self, remembered=None, events: Optional[List[str]] = None) -> None:
        self.remembered = dict(remembered or {})
        self.saved: List = []
        self.events = events if events is not None else []

    def get(self, job): return self.remembered.get((job.platform, job.url))
    def put(self, job): self.saved.append((job.url, job.status))
