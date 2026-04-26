# -*- coding: utf-8 -*-
"""
LoginPage —— reelmate.cn 登录页面对象
========================================

封装 reelmate.cn (万兴剧厂) 登录页面的元素定位器和业务操作方法。

页面架构:
  reelmate.cn 是一个 Nuxt.js SPA 应用，登录流程如下:
  1. 首页 https://www.reelmate.cn
     - 点击右上角"登录"按钮
  2. 跳转到 https://accounts.wondershare.cn/login
     - 显示登录表单（用户名/密码/登录按钮）
  3. 登录成功后回跳 https://www.reelmate.cn

业务方法列表:
  - navigate_to_login():           从首页导航到登录页
  - login(username, password):     执行完整登录流程
  - enter_username(username):      仅输入用户名
  - enter_password(password):      仅输入密码
  - clear_username():              清空用户名
  - clear_password():              清空密码
  - click_login_button():          点击登录按钮
  - is_login_page():               检查当前是否在登录页面
  - is_logged_in():                检查是否已登录成功
  - get_error_message():           获取登录错误提示信息
  - verify_login_page_elements():  验证登录页面元素完整性
  - verify_login_success():        验证登录成功（离开登录页）
  - verify_login_failed_stay_on_page(): 验证登录失败（停留在登录页）

使用方式 (YAML 用例):
  - 导航到登录页:
      操作类型: LoginPage.navigate_to_login

  - 执行登录:
      操作类型: LoginPage.login
      username: "{{username}}"
      password: "{{password}}"

  - 验证登录成功:
      操作类型: LoginPage.verify_login_success
      login_url: "https://accounts.wondershare.cn/login"

使用方式 (Excel 用例):
  操作类型: LoginPage.login
  数据内容: username="18318053665" password="qq111111"
"""

from typing import Optional

import allure

from HAT.pages.base_page import BasePage


class LoginPage(BasePage):
    """
    reelmate.cn 登录页面对象。

    封装登录页面的元素定位和业务操作。
    通过"LoginPage.method"的点分表示法在 YAML/Excel 用例中调用。
    """

    PAGE_NAME = "LoginPage"
    PAGE_URL = "https://www.reelmate.cn"
    LOGIN_URL = "https://accounts.wondershare.cn/login"

    # ───────────────── 页面元素定位器 ─────────────────
    # 所有定位器使用 Playwright 原生选择器语法
    # 优先级: text > role > placeholder > testid > css > xpath
    # 多选择器用逗号分隔，Playwright 按顺序尝试匹配
    _LOCATORS = {
        # === 首页登录入口 ===
        # 使用 text= 定位"登录"文本，最简洁稳定
        "登录入口按钮": {
            "定位方式": "text",
            "目标对象": "登录",
        },

        # === 登录页表单元素 ===
        # 用户名输入框 —— 支持 email 和 text 类型的 input
        "用户名输入框": {
            "定位方式": "css",
            "目标对象": ('input[type="email"], input[type="text"], '
                         'input[name="email"], input[name="username"]'),
        },

        # 密码输入框
        "密码输入框": {
            "定位方式": "css",
            "目标对象": 'input[type="password"]',
        },

        # 登录提交按钮 —— 多种可能的实现方式
        "登录提交按钮": {
            "定位方式": "css",
            "目标对象": ('button[type="submit"], input[type="submit"], '
                         'button:has-text("登录"), button:has-text("登錄")'),
        },

        # 登录错误提示信息
        "登录错误提示": {
            "定位方式": "css",
            "目标对象": '[class*="error"], [class*="alert"], [class*="msg"]',
        },

        # 登录成功后的用户标识元素（头像/昵称等）
        "用户头像或昵称": {
            "定位方式": "css",
            "目标对象": '[class*="avatar"], [class*="user"], [class*="nickname"]',
        },
    }

    # ───────────────── 业务操作方法 ─────────────────

    @allure.step("POM: 导航到登录页面")
    def navigate_to_login(self):
        """
        从首页导航到登录页面。

        流程:
          1. 打开首页 (self.PAGE_URL)
          2. 等待 SPA 页面渲染完成
          3. 点击首页右上角的"登录"入口按钮
          4. 等待跳转到 accounts.wondershare.cn/login

        :raises Exception: 如果登录入口按钮不可见或点击失败
        """
        # 1. 打开首页
        self.open(url=self.PAGE_URL, wait_until="load")
        # 2. 等待 SPA 渲染完成（Nuxt.js 需要额外等待时间）
        self.wait(3)
        # 3. 点击首页"登录"入口按钮
        self.click("登录入口按钮")
        # 4. 等待页面跳转到登录页（accounts.wondershare.cn）
        self.wait(3)

    @allure.step("POM: 执行登录操作")
    def login(self, username: str, password: str):
        """
        执行完整的登录操作。

        前置条件: 当前页面必须是登录页面（accounts.wondershare.cn/login）。

        :param username: 用户名（邮箱或手机号）
        :param password: 登录密码

        流程:
          1. 输入用户名到用户名输入框
          2. 输入密码到密码输入框
          3. 短暂等待（模拟人类操作间隔）
          4. 点击登录提交按钮
          5. 等待服务器响应和页面跳转
        """
        # 1. 输入用户名（fill 方法自动等待元素可见并填充）
        self.fill("用户名输入框", username)
        # 2. 输入密码
        self.fill("密码输入框", password)
        # 3. 模拟真实用户短暂停顿（避免反爬机制）
        self.wait(1)
        # 4. 点击登录提交按钮
        self.click("登录提交按钮")
        # 5. 等待服务器处理 + 页面跳转（登录成功后跳回 reelmate.cn）
        self.wait(5)

    @allure.step("POM: 输入用户名")
    def enter_username(self, username: str):
        """
        仅输入用户名（不清除现有内容）。

        常用于需要分步验证的场景，例如先输入用户名，
        验证某些UI状态，再输入密码。

        :param username: 用户名
        """
        self.fill("用户名输入框", username)

    @allure.step("POM: 输入密码")
    def enter_password(self, password: str):
        """
        仅输入密码。

        :param password: 密码
        """
        self.fill("密码输入框", password)

    @allure.step("POM: 清空用户名")
    def clear_username(self):
        """清空用户名输入框的内容。"""
        self.fill("用户名输入框", "", clear_first=True)

    @allure.step("POM: 清空密码")
    def clear_password(self):
        """清空密码输入框的内容。"""
        self.fill("密码输入框", "", clear_first=True)

    @allure.step("POM: 点击登录按钮")
    def click_login_button(self):
        """
        点击登录提交按钮。

        用于分步登录场景：先输入账号密码，再单独点击登录。
        """
        self.click("登录提交按钮")

    @allure.step("POM: 检查是否在登录页面")
    def is_login_page(self) -> bool:
        """
        检查当前 URL 是否属于登录页面。

        :return: True 如果 URL 包含 "login" 或 "accounts"，否则 False
        """
        current_url = self.get_current_url()
        return "login" in current_url.lower() or "accounts" in current_url.lower()

    @allure.step("POM: 检查是否已登录")
    def is_logged_in(self) -> bool:
        """
        检查当前是否已登录成功。

        判断依据: 页面中是否能找到用户头像或昵称元素。

        :return: True 如果已登录（找到用户标识元素），否则 False
        """
        try:
            self.wait_for_element("用户头像或昵称", timeout=5000)
            return True
        except Exception:
            return False

    @allure.step("POM: 获取登录错误信息")
    def get_error_message(self, timeout: int = 5000) -> Optional[str]:
        """
        获取登录失败时的错误提示文本。

        :param timeout: 等待错误提示元素出现的超时时间（毫秒）
        :return: 错误信息文本字符串，如果未找到则返回 None
        """
        try:
            return self.get_text("登录错误提示", timeout=timeout)
        except Exception:
            return None

    @allure.step("POM: 验证登录页面元素完整性")
    def verify_login_page_elements(self):
        """
        验证登录页面的核心表单元素是否存在且可见。

        检查项:
          - 用户名输入框
          - 密码输入框
          - 登录提交按钮

        :raises AssertionError: 如果任何核心元素不存在或不可见
        """
        # 依次验证三个核心表单元素
        self.assert_element_visible("用户名输入框", timeout=10000)
        self.assert_element_visible("密码输入框", timeout=5000)
        self.assert_element_visible("登录提交按钮", timeout=5000)

    @allure.step("POM: 验证登录成功(离开登录页)")
    def verify_login_success(self, login_url: str = None):
        """
        验证登录是否成功 —— 确认 URL 已离开登录页面。

        登录成功后，浏览器应跳转回 reelmate.cn 首页，
        URL 中不再包含 accounts.wondershare.cn/login。

        :param login_url: 登录页面的 URL（用于对比），默认为 self.LOGIN_URL
        :raises AssertionError: 如果当前 URL 仍包含登录页面 URL
        """
        current_url = self.get_current_url()
        target = login_url or self.LOGIN_URL
        if target in current_url:
            raise AssertionError(
                f"登录失败！URL 仍在登录页面: {current_url}"
            )

    @allure.step("POM: 验证登录失败(停留在登录页)")
    def verify_login_failed_stay_on_page(self, login_url: str = None):
        """
        验证登录失败 —— 确认 URL 仍停留在登录页面（负面测试用）。

        适用于错误密码、空账号等场景的断言。

        :param login_url: 登录页面的 URL（用于对比），默认为 self.LOGIN_URL
        :raises AssertionError: 如果离开了登录页面（即意外登录成功）
        """
        current_url = self.get_current_url()
        target = login_url or self.LOGIN_URL
        if target not in current_url:
            raise AssertionError(
                f"预期登录失败但仍停留在登录页面，但实际已跳转到: {current_url}"
            )
