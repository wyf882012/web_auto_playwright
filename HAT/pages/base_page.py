# -*- coding: utf-8 -*-
"""
BasePage —— POM 基础页面对象
==============================

所有页面对象（LoginPage、HomePage 等）的抽象基类。
提供:
  - 页面定位器字典管理（_LOCATORS 类属性）
  - 对 Keywords 底层操作方法的引用
  - 通用的 Playwright 选择器构建逻辑（从定位器字典中读取）
  - 常用页面操作方法（open / click / fill / get_text / wait / assert 等）

设计原则:
  - 每个子类定义自己的 _LOCATORS 类属性（页面级元素定位器），
    独立于全局 _WEB页面元素 字典，实现页面级隔离
  - 子类方法通过 self.keywords 访问底层 Playwright 操作
  - 所有方法添加 @allure.step 装饰器，与关键字模式报告保持一致

选择器引擎优先级:
  role > text > placeholder > testid > css > xpath > id > name > class > tag
"""

import time
from typing import Dict, Any, Optional

import allure


class BasePage:
    """
    POM 基础页面对象。

    每个具体页面对象继承此类，并定义自己的元素定位器和业务方法。
    构造函数接收 Keywords 实例以访问底层浏览器操作。

    类属性:
        PAGE_NAME: str    -- 页面名称（用于日志和注册标识）
        PAGE_URL: str     -- 页面 URL（可选，用于导航和验证）
        _LOCATORS: dict   -- 页面元素定位器字典，格式:
            {
                "元素名称": {
                    "定位方式": "text|css|role|placeholder|testid|xpath|id|name|class|tag",
                    "目标对象": "选择器值"
                },
                ...
            }
    """

    PAGE_NAME: str = "BasePage"
    PAGE_URL: str = ""
    _LOCATORS: Dict[str, Dict[str, str]] = {}

    def __init__(self, keywords):
        """
        初始化页面对象。

        :param keywords: Keywords 实例，提供底层的 Playwright 浏览器操作方法。
                         通过 keywords.page 直接访问 Playwright Page 对象，
                         通过 keywords.get_screenshot() 截图并附加到 Allure 报告。
        """
        self.keywords = keywords

    # ───────────────── 定位器辅助方法 ─────────────────

    def get_locator(self, element_name: str) -> Dict[str, str]:
        """
        根据元素名称从页面定位器字典中获取定位信息。

        :param element_name: 元素名称（如 "用户名输入框"）
        :return: {"定位方式": "...", "目标对象": "..."}
        :raises KeyError: 如果元素名称未在 _LOCATORS 中定义
        """
        if element_name not in self._LOCATORS:
            raise KeyError(
                f"页面 [{self.PAGE_NAME}] 中未定义元素 '{element_name}'，"
                f"可用元素: {list(self._LOCATORS.keys())}"
            )
        return self._LOCATORS[element_name]

    def build_selector(self, element_name: str) -> str:
        """
        根据元素名称构建 Playwright 原生选择器字符串。

        支持的选择器类型（优先级从高到低）:
          role        — role=button[name="登录"]
          text        — text=登录
          placeholder — placeholder=请输入邮箱
          testid      — data-testid="submit-btn"
          css         — .btn-primary 或原始 CSS 字符串
          xpath       — xpath=//button
          id          — #elementId（兼容旧版）
          name        — [name="elementName"]（兼容旧版）
          class       — .className（兼容旧版）
          tag         — 原始标签名

        :param element_name: 元素名称
        :return: Playwright 选择器字符串
        """
        loc_data = self.get_locator(element_name)
        loc_type = str(loc_data.get("定位方式", "text")).lower()
        target = loc_data.get("目标对象", "")

        # Playwright 原生选择器引擎映射（与 Keywords._build_selector 保持一致）
        selector_map = {
            "role": target,
            "text": f"text={target}",
            "placeholder": f"[placeholder='{target}']",
            "testid": f"[data-testid='{target}']",
            "id": f"#{target}",
            "name": f'[name="{target}"]',
            "class": f".{target}",
            "css": target,
            "css selector": target,
            "xpath": f"xpath={target}",
            "tag": target,
        }
        return selector_map.get(loc_type, f"text={target}")

    def build_selector_with_index(self, element_name: str, index: int = 0) -> str:
        """
        构建选择器，并处理 INDEX 参数（第几个匹配元素）。

        Playwright 使用 >> nth=N 语法选择第 N 个匹配元素（0-based）。

        :param element_name: 元素名称
        :param index: 匹配元素的索引（0 表示第 1 个，1 表示第 2 个）
        :return: 带 nth 伪选择器的 Playwright 选择器字符串
        """
        selector = self.build_selector(element_name)
        if index > 0:
            selector = f"{selector} >> nth={index}"
        return selector

    # ───────────────── 通用页面操作方法 ─────────────────

    @allure.step("POM: 打开页面")
    def open(self, url: str = None, timeout: int = 30000, wait_until: str = "domcontentloaded"):
        """
        打开当前页面（导航到指定 URL）。

        :param url: 要访问的 URL，默认为类属性 PAGE_URL
        :param timeout: 超时时间（毫秒）
        :param wait_until: 等待策略（load | domcontentloaded | networkidle）
        :raises ValueError: 如果 url 和 PAGE_URL 均为空
        """
        target_url = url or self.PAGE_URL
        if not target_url:
            raise ValueError(f"页面 [{self.PAGE_NAME}] 未定义 PAGE_URL，请传入 url 参数")
        self.keywords.page.goto(target_url, timeout=timeout, wait_until=wait_until)
        self.keywords.get_screenshot()

    @allure.step("POM: 点击元素")
    def click(self, element_name: str, timeout: int = 10000):
        """
        点击指定元素。

        等待元素变为可见状态后执行点击操作。

        :param element_name: 元素名称（在 _LOCATORS 中定义）
        :param timeout: 等待元素可见的超时时间（毫秒）
        """
        selector = self.build_selector(element_name)
        self.keywords.page.wait_for_selector(selector, state="visible", timeout=timeout)
        self.keywords.page.click(selector)
        self.keywords.get_screenshot()

    @allure.step("POM: 输入文本")
    def fill(self, element_name: str, content: str, timeout: int = 10000, clear_first: bool = True):
        """
        在指定输入框中输入文本。

        Playwright 的 fill() 方法会自动清除已有内容后输入，
        如果设置 clear_first=False，则使用 type() 逐字输入。

        :param element_name: 元素名称（在 _LOCATORS 中定义）
        :param content: 要输入的文本内容
        :param timeout: 等待元素可见的超时时间（毫秒）
        :param clear_first: 是否先清空输入框（默认 True）
        """
        selector = self.build_selector(element_name)
        self.keywords.page.wait_for_selector(selector, state="visible", timeout=timeout)
        if clear_first:
            self.keywords.page.fill(selector, "")
        self.keywords.page.fill(selector, str(content))
        self.keywords.get_screenshot()

    @allure.step("POM: 获取元素文本")
    def get_text(self, element_name: str, timeout: int = 10000) -> str:
        """
        获取元素的文本内容。

        :param element_name: 元素名称
        :param timeout: 等待元素可见的超时时间（毫秒）
        :return: 元素的文本内容，如果元素不可见则返回空字符串
        """
        try:
            selector = self.build_selector(element_name)
            self.keywords.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return self.keywords.page.text_content(selector) or ""
        except Exception:
            return ""

    @allure.step("POM: 等待元素可见")
    def wait_for_element(self, element_name: str, timeout: int = 10000):
        """
        等待指定元素变为可见状态。

        :param element_name: 元素名称
        :param timeout: 超时时间（毫秒）
        :raises Exception: 如果超时后元素仍不可见
        """
        selector = self.build_selector(element_name)
        self.keywords.page.wait_for_selector(selector, state="visible", timeout=timeout)

    @allure.step("POM: 断言元素存在")
    def assert_element_visible(self, element_name: str, timeout: int = 10000):
        """
        断言元素存在且可见。

        :param element_name: 元素名称
        :param timeout: 超时时间（毫秒）
        :raises AssertionError: 如果元素不可见或不存在
        """
        try:
            self.wait_for_element(element_name, timeout=timeout)
            self.keywords.get_screenshot()
        except Exception:
            self.keywords.get_screenshot()
            raise AssertionError(f"页面 [{self.PAGE_NAME}] 中元素不存在或不可见: '{element_name}'")

    @allure.step("POM: 获取当前URL")
    def get_current_url(self) -> str:
        """
        获取当前页面的 URL。

        :return: 当前页面的完整 URL 字符串
        """
        return self.keywords.page.url

    @allure.step("POM: 断言 URL 包含")
    def assert_url_contains(self, expected: str, error_message: str = None):
        """
        断言当前 URL 包含指定字符串。

        :param expected: 期望的 URL 子串
        :param error_message: 断言失败时的自定义错误信息
        :raises AssertionError: 如果实际 URL 不包含期望值
        """
        actual_url = self.keywords.page.url
        self.keywords.get_screenshot()
        if expected not in actual_url:
            msg = error_message or f"URL 断言失败! 期望包含: {expected}, 实际: {actual_url}"
            raise AssertionError(msg)

    @allure.step("POM: 强制等待")
    def wait(self, seconds: float = 1.0):
        """
        强制等待指定秒数。

        用于等待页面渲染、动画完成、异步请求响应等场景。
        注意: 优先使用 wait_for_element 等智能等待方法。

        :param seconds: 等待的秒数
        """
        time.sleep(float(seconds))

    @allure.step("POM: 获取页面标题")
    def get_page_title(self) -> str:
        """
        获取当前页面的标题。

        :return: 页面 title 标签的内容
        """
        return self.keywords.page.title()
