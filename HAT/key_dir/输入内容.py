# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : 输入内容.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
import allure

from HAT.keywords.web_keywords import Keywords


class 输入内容(Keywords):
    """
    自定义关键字示例：输入内容。
    
    该类继承自内置的 Keywords 类，演示了如何扩展框架功能。
    用户可以在 key_dir 目录下创建类似的 Python 文件来定义自己的业务逻辑。
    """
    @allure.step("输入内容")
    def 输入内容(self, **kwargs):
        """
        重写或自定义输入逻辑。
        
        :param kwargs: 包含 '数据内容' 和 '_页面元素' 等键的字典
        """
        self.show_log("输入数据显示出来", kwargs)
        eles_list = self.find_element(**kwargs)
        eles_list.send_keys(kwargs['数据内容'])
        self.get_screenshot()

