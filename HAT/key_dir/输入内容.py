# -*- coding: utf-8 -*-
# 自定义关键字示例 - Playwright 版
import allure

from HAT.keywords.web_keywords import Keywords


class 输入内容(Keywords):
    """
    自定义关键字示例：输入内容。

    该类继承自内置的 Keywords 类，演示了如何扩展框架功能。
    用户可以在 key_dir 目录下创建类似的 Python 文件来定义自己的业务逻辑。
    构造函数接收 (page, context, browser) 三个 Playwright 对象。
    """

    def __init__(self, page, context, browser):
        super().__init__(page, context, browser)

    @allure.step("输入内容")
    def 输入内容(self, **kwargs):
        """
        重写或自定义输入逻辑。

        :param kwargs: 包含 '数据内容' 和 '_页面元素' 等键的字典
        """
        self.show_log("输入数据显示出来", kwargs)
        selector = self._get_selector_with_index(**kwargs)
        content = str(kwargs.get("数据内容", ""))
        self.page.wait_for_selector(selector, state="visible")
        self.page.fill(selector, content)
        self.get_screenshot()
