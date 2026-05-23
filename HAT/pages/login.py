"""
LoginPage — reelmate.cn login page object.

Loads semantic locators from locators/login_page.yaml at init time.
"""

import os
from types import SimpleNamespace
from typing import Optional

import allure
from playwright.sync_api import expect

from HAT.locator import LocatorBuilder
from HAT.pages.base import BasePage


class LoginPage(BasePage):
    PAGE_NAME = "LoginPage"
    PAGE_URL = "https://www.reelmate.cn"

    def __init__(self, keywords):
        super().__init__(keywords)
        yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "locators", "login_page.yaml")
        locators = LocatorBuilder.from_yaml(self.page, yaml_path)
        self.locators = SimpleNamespace(**locators)

    # ── navigation ─────────────────────────────────────────────

    @allure.step("POM: Navigate to login dialog")
    def navigate_to_login(self):
        """Open home page → click '立即登录' → wait for iframe → switch tab."""
        self.open(url=self.PAGE_URL, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)
        self.click(self.locators.login_entry_btn, timeout=15000)
        expect(self.locators.password_login_tab).to_be_visible(timeout=30000)
        self.click(self.locators.password_login_tab, timeout=10000)
        expect(self.locators.username_input).to_be_visible(timeout=10000)
        expect(self.locators.password_input).to_be_visible(timeout=5000)
        self.kw.screenshot()

    # ── actions ─────────────────────────────────────────────────

    @allure.step("POM: Login")
    def login(self, username: str, password: str):
        """Full login flow: fill form → agree terms → submit."""
        self.click(self.locators.password_login_tab, timeout=10000)
        self.fill(self.locators.username_input, username)
        self.fill(self.locators.password_input, password)
        self.check(self.locators.agreement_checkbox)
        self.click(self.locators.login_submit_btn)
        try:
            self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

    @allure.step("POM: Fill username")
    def enter_username(self, username: str):
        self.fill(self.locators.username_input, username)

    @allure.step("POM: Fill password")
    def enter_password(self, password: str):
        self.fill(self.locators.password_input, password)

    @allure.step("POM: Clear username")
    def clear_username(self):
        self.fill(self.locators.username_input, "")

    @allure.step("POM: Clear password")
    def clear_password(self):
        self.fill(self.locators.password_input, "")

    @allure.step("POM: Click login button")
    def click_login_button(self):
        self.click(self.locators.login_submit_btn)

    @allure.step("POM: Agree to terms")
    def agree_to_terms(self):
        self.check(self.locators.agreement_checkbox)

    # ── assertions ─────────────────────────────────────────────

    @allure.step("POM: Is on login page")
    def is_on_login_page(self) -> bool:
        url = self.get_url().lower()
        if "/login" in url and "accounts" in url:
            return True
        return (self.is_visible(self.locators.password_login_tab)
                and self.is_visible(self.locators.username_input))

    @allure.step("POM: Is logged in")
    def is_logged_in(self) -> bool:
        try:
            marker = self.page.locator(
                '[class*="avatar"], [class*="user"], [class*="nickname"]').first
            expect(marker).to_be_visible(timeout=5000)
            return True
        except Exception:
            pass
        url = self.get_url().lower()
        if self.is_on_login_page():
            return False
        return "login" not in url and "accounts" not in url

    @allure.step("POM: Get error message")
    def get_error_message(self, timeout: int = 5000) -> Optional[str]:
        try:
            err = self.page.locator(
                '[class*="error"], [class*="alert"], [class*="msg"]').first
            expect(err).to_be_visible(timeout=timeout)
            return (err.text_content() or "").strip() or None
        except Exception:
            return None

    @allure.step("POM: Verify login page elements")
    def verify_login_page_elements(self):
        expect(self.locators.password_login_tab).to_be_visible(timeout=10000)
        self.click(self.locators.password_login_tab, timeout=10000)
        expect(self.locators.username_input).to_be_visible(timeout=10000)
        expect(self.locators.password_input).to_be_visible(timeout=5000)
        expect(self.locators.login_submit_btn).to_be_visible(timeout=5000)

    @allure.step("POM: Verify login success")
    def verify_login_success(self, login_url: str = ""):
        if not self.is_on_login_page():
            return
        current = self.get_url()
        target = (login_url or self.PAGE_URL).lower()
        if self.is_on_login_page() or target in current.lower():
            raise AssertionError(
                f"Login failed — still on login page: {current}")

    @allure.step("POM: Verify login failure (stay on page)")
    def verify_login_failed(self, login_url: str = ""):
        current = self.get_url()
        target = (login_url or self.PAGE_URL).lower()
        if not self.is_on_login_page() and target not in current.lower():
            raise AssertionError(
                f"Expected to stay on login page but navigated to: {current}")
