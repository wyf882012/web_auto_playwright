"""
VideoPage — reelmate.cn video reference generation page object.

Handles the "参考生视频" workflow: mode selection → TGI selection → model verification.
"""

import os
from types import SimpleNamespace

import allure
from playwright.sync_api import expect

from HAT.locators import LocatorBuilder
from HAT.pages.base import BasePage


class VideoPage(BasePage):
    PAGE_NAME = "VideoPage"
    PAGE_URL = "https://www.reelmate.cn/video"

    def __init__(self, keywords):
        super().__init__(keywords)
        yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "locators", "video_page.yaml")
        locators = LocatorBuilder.from_yaml(self.page, yaml_path)
        self.locators = SimpleNamespace(**locators)

    @allure.step("POM: Navigate to video page")
    def navigate_to_video(self):
        self.open(url=self.PAGE_URL, wait_until="domcontentloaded")
        self.page.wait_for_timeout(3000)
        self.kw.screenshot()

    @allure.step("POM: Select reference video tab")
    def select_ref_video(self):
        expect(self.locators.ref_video_tab).to_be_visible(timeout=15000)
        self.click(self.locators.ref_video_tab)
        self.page.wait_for_timeout(2000)

    @allure.step("POM: Select multi-grid mode")
    def select_multi_grid(self):
        expect(self.locators.multi_grid_mode).to_be_visible(timeout=10000)
        self.click(self.locators.multi_grid_mode)
        self.page.wait_for_timeout(1000)

    @allure.step("POM: Select TGI 2")
    def select_tgi2(self):
        expect(self.locators.tgi2_option).to_be_visible(timeout=10000)
        self.click(self.locators.tgi2_option)
        self.page.wait_for_timeout(1000)

    @allure.step("POM: Click video model dropdown")
    def open_video_model_dropdown(self):
        expect(self.locators.video_model_dropdown).to_be_visible(timeout=10000)
        self.click(self.locators.video_model_dropdown)
        self.page.wait_for_timeout(1000)

    @allure.step("POM: Verify Seedance 2.0VIP in dropdown")
    def verify_seedance_option(self) -> bool:
        try:
            expect(self.locators.seedance_option).to_be_visible(timeout=5000)
            self.kw.screenshot()
            return True
        except Exception:
            self.kw.screenshot()
            return False

    @allure.step("POM: Get dropdown options text")
    def get_dropdown_options(self, var_name: str = "dropdown_options"):
        from HAT.core.config import cfg
        self.open_video_model_dropdown()
        loc = self.locators.video_model_dropdown
        options = loc.locator("option").all_text_contents() or loc.locator("[role='option']").all_text_contents()
        cfg.set(var_name, options)
        return options
