# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : 输入内容.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
import allure

from HAT.keywords.web_keywords import Keywords


class 输入内容(Keywords):
    @allure.step("输入内容")
    def 输入内容(self, **kwargs):
        self.show_log("输入数据显示出来", kwargs)
        eles_list = self.find_element(**kwargs)
        eles_list.send_keys(kwargs['数据内容'])
        self.get_screenshot()

