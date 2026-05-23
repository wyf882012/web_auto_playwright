"""
Browser lifecycle manager — Playwright sync-API wrapper.

Handles:
  - Browser / context / page creation
  - Session reuse (shared browser across tests)
  - Headless mode (CLI env var or context config)
  - Tracing / screenshots for Allure
  - Cleanup + slideshow generation
"""

import atexit
import os
import time
from typing import Optional

import allure
from allure_commons.types import AttachmentType
from loguru import logger
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from HAT.config import cfg

# Shared browser state (used when session_reuse=True)
_shared_playwright = None
_shared_browser: Optional[Browser] = None


def _cleanup_shared():
    global _shared_browser, _shared_playwright
    for obj in (_shared_browser, _shared_playwright):
        try:
            if obj:
                obj.close() if hasattr(obj, "close") else obj.stop()
        except Exception:
            pass
    _shared_browser = _shared_playwright = None


atexit.register(_cleanup_shared)


class BrowserManager:
    """Creates and manages the Playwright browser lifecycle."""

    def __init__(self):
        self.playwright = None
        self._browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    # ── setup ──────────────────────────────────────────────────

    def start(self):
        """Initialise browser, page, tracing, and locators. Returns (self, page)."""
        session_reuse = cfg.get("session_reuse")
        global _shared_browser, _shared_playwright

        if session_reuse and _shared_browser is not None:
            self._browser = _shared_browser
            self.playwright = _shared_playwright
        else:
            self.playwright = sync_playwright().start()
            self._browser = self._launch()
            if session_reuse:
                _shared_browser = self._browser
                _shared_playwright = self.playwright

        self.context = self._browser.new_context(viewport=None, locale="zh-CN")
        self.page = self.context.new_page()

        # Start tracing
        try:
            self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        except Exception as e:
            logger.warning(f"Tracing start failed (non-fatal): {e}")

        self._setup_locators()
        return self.page

    def _launch(self) -> Browser:
        """Create and launch a browser instance."""
        import os as _os

        browser_cfg = cfg.get("_browser") or {}
        # CLI env vars override config
        name = (_os.environ.get("HAT_BROWSER")
                or browser_cfg.get("browserName", "chromium")).lower()

        types = {"chromium": self.playwright.chromium,
                 "chrome": self.playwright.chromium,
                 "firefox": self.playwright.firefox,
                 "webkit": self.playwright.webkit,
                 "edge": self.playwright.chromium}
        browser_type = types.get(name, self.playwright.chromium)

        headless = (_os.environ.get("HAT_HEADLESS", "").lower() == "true"
                    or browser_cfg.get("headless", False))
        args = browser_cfg.get("args", [])
        # Filter out the old "headless" string arg style
        args = [a for a in args if a != "headless"]

        return browser_type.launch(headless=headless, args=args or None)

    def _setup_locators(self):
        """Load semantic locators from YAML files + legacy _elements."""
        from HAT.locator import LocatorBuilder

        locators = {}
        # 1. Scan locators/ directory for YAML files
        loc_dir = os.path.join(os.path.dirname(__file__), "locators")
        if os.path.isdir(loc_dir):
            for fn in sorted(os.listdir(loc_dir)):
                if fn.endswith(("_locator.yaml", "_locator.yml")):
                    locators.update(
                        LocatorBuilder.from_yaml(self.page, os.path.join(loc_dir, fn)))

        # 2. Convert legacy _elements if present
        elements = cfg.get("_elements") or {}
        if elements:
            locators.update(LocatorBuilder.from_legacy(self.page, elements))

        cfg.set("_locators", locators)
        logger.debug(f"Locators loaded: {len(locators)} elements")

    # ── teardown ────────────────────────────────────────────────

    def stop(self):
        """Stop tracing, generate slideshow, close browser."""
        # Trace
        trace_path = None
        if self.context:
            try:
                traces_dir = os.path.join(os.getcwd(), "traces")
                os.makedirs(traces_dir, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                name = _safe_filename(cfg.get("_current_case", "test"))
                trace_path = os.path.join(traces_dir, f"{name}_{ts}.zip")
                self.context.tracing.stop(path=trace_path)
                logger.debug(f"Trace saved: {trace_path}")
            except Exception as e:
                logger.warning(f"Trace stop failed: {e}")

        # Slideshow
        screenshots = getattr(self, "_screenshots", [])
        if screenshots:
            try:
                _attach_slideshow(screenshots)
            except Exception as e:
                logger.warning(f"Slideshow failed: {e}")

        # Attach trace
        if trace_path and os.path.exists(trace_path):
            try:
                with open(trace_path, "rb") as f:
                    allure.attach(f.read(), "Playwright Trace",
                                  attachment_type="application/zip")
            except Exception as e:
                logger.warning(f"Trace attach failed: {e}")

        # Cleanup
        if not cfg.get("session_reuse"):
            if self.context:
                self.context.close()
            if self._browser:
                self._browser.close()
            if self.playwright:
                self.playwright.stop()


def _safe_filename(name: str, max_len: int = 50) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(name))[:max_len]


def _attach_slideshow(images: list, title="Screenshot Replay"):
    """Attach an HTML slideshow of screenshots to the Allure report."""
    if not images:
        return
    import json
    slides_json = json.dumps(images, ensure_ascii=False)
    html = f"""<div class="video-like-slideshow" style="max-width:800px;margin:20px auto;position:relative;overflow:hidden;height:550px;background:#000;border-radius:8px;">
        <div id="slideshow-container" style="position:relative;height:calc(100% - 80px);"></div>
        <div id="caption-container" style="position:absolute;bottom:40px;left:0;right:0;text-align:center;color:#fff;padding:0 20px;z-index:10;"></div>
        <div style="position:absolute;bottom:0;left:0;right:0;height:3px;background:rgba(255,255,255,.2);z-index:5;">
            <div id="progress-bar" style="height:100%;width:0;background:#ff4757;transition:width .1s linear;"></div>
        </div>
    </div>
    <style>
        .slide{{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:contain;opacity:0;transition:opacity 1.2s;will-change:opacity;z-index:1;background:#000;}}
        .slide.active{{opacity:1;z-index:2;}}
        .caption{{position:absolute;width:100%;opacity:0;transition:opacity .5s;font-size:18px;text-shadow:1px 1px 3px rgba(0,0,0,.8);}}
        .caption.active{{opacity:1;}}
    </style>
    <script>
        const slidesData = {slides_json};
        const container = document.getElementById('slideshow-container');
        const captionContainer = document.getElementById('caption-container');
        const progressBar = document.getElementById('progress-bar');
        let currentIndex = 0, slides = [], captions = [], intervalId, progressId, elapsed = 0;
        const DUR = 3000;
        function init() {{
            slidesData.forEach((d,i)=>{{
                const s = document.createElement('img'); s.className='slide'; s.src=d.image; container.appendChild(s); slides.push(s);
                const c = document.createElement('div'); c.className='caption'; c.textContent=d.caption; captionContainer.appendChild(c); captions.push(c);
                if(i===0){{s.classList.add('active');c.classList.add('active');}}
            }});
            intervalId = setInterval(next, DUR);
            progressId = setInterval(()=>{{elapsed+=100;progressBar.style.width=(elapsed%(slidesData.length*DUR))/(slidesData.length*DUR)*100+'%';}},100);
        }}
        function next(){{slides[currentIndex].classList.remove('active');captions[currentIndex].classList.remove('active');currentIndex=(currentIndex+1)%slidesData.length;slides[currentIndex].classList.add('active');captions[currentIndex].classList.add('active');}}
        window.addEventListener('DOMContentLoaded', init);
    </script>"""
    allure.attach(html, name=title, attachment_type=AttachmentType.HTML)
