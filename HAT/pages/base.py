"""
BasePage — abstract base for all POM page objects.

Encapsulates common Playwright Locator operations so page subclasses
stay focused on business logic.

Usage in subclasses:
  class MyPage(BasePage):
      PAGE_URL = "https://example.com"

      def __init__(self, keywords):
          super().__init__(keywords)
          # self.locators is a SimpleNamespace from YAML/dict
"""

import time
from types import SimpleNamespace

import allure
from playwright.sync_api import expect


class BasePage:
    PAGE_NAME: str = "BasePage"
    PAGE_URL: str = ""

    def __init__(self, keywords):
        self.kw = keywords          # Keywords instance (page, context, browser)
        self.page = keywords.page   # Playwright Page shortcut
        self.locators = None        # Set by subclass (SimpleNamespace of Locators)

    # ── locator helpers ────────────────────────────────────────

    def click(self, locator, timeout: int = 10000):
        locator.click(timeout=timeout)
        self.kw.screenshot()

    def fill(self, locator, text: str, timeout: int = 10000, clear: bool = True):
        if clear:
            locator.clear()
        locator.fill(str(text), timeout=timeout)
        self.kw.screenshot()

    def check(self, locator, timeout: int = 10000):
        """Check a checkbox (click-compatible for custom-styled checkboxes)."""
        locator.click(timeout=timeout)
        self.kw.screenshot()

    def get_text(self, locator, timeout: int = 10000) -> str:
        try:
            expect(locator).to_be_visible(timeout=timeout)
            return locator.text_content() or ""
        except Exception:
            return ""

    def is_visible(self, locator, timeout: int = 3000) -> bool:
        try:
            expect(locator).to_be_visible(timeout=timeout)
            return True
        except Exception:
            return False

    def assert_visible(self, locator, timeout: int = 10000):
        try:
            expect(locator).to_be_visible(timeout=timeout)
            self.kw.screenshot()
        except Exception:
            self.kw.screenshot()
            raise AssertionError(f"[{self.PAGE_NAME}] element not visible")

    # ── page-level helpers ─────────────────────────────────────

    @allure.step("POM: Open page")
    def open(self, url: str = "", timeout: int = 30000,
             wait_until: str = "domcontentloaded"):
        target = url or self.PAGE_URL
        if not target:
            raise ValueError(f"[{self.PAGE_NAME}] PAGE_URL not set")
        self.page.goto(target, timeout=timeout, wait_until=wait_until)
        self.kw.screenshot()

    @allure.step("POM: Get URL")
    def get_url(self) -> str:
        return self.page.url

    @allure.step("POM: Assert URL contains")
    def assert_url_contains(self, expected: str, msg: str = ""):
        actual = self.page.url
        self.kw.screenshot()
        if expected not in actual:
            raise AssertionError(msg or f"URL mismatch: '{expected}' not in '{actual}'")

    @allure.step("POM: Get page title")
    def get_title(self) -> str:
        return self.page.title()

    def wait(self, seconds: float = 1.0):
        time.sleep(float(seconds))
