# -*- coding: utf-8 -*-
"""
HAT POM (Page Object Model) 层
===============================

此包提供页面对象模式支持。每个页面对象继承自 BasePage，
封装了该页面的元素定位器和业务操作方法。

POM 方法的调用方式采用"PageClass.method"点分表示法，
例如在 YAML/Excel 用例中:
    操作类型: LoginPage.login

与关键字驱动的对比:
  - 关键字模式: 操作类型: 输入内容    → Keywords.输入内容()
  - POM 模式:   操作类型: LoginPage.login  → LoginPage实例.login()
  - 两者可混合使用，向后完全兼容

使用方式:
  # Excel 用例中
  操作类型: LoginPage.navigate_to_login
  操作类型: LoginPage.login
  操作类型: LoginPage.verify_login_success

  # YAML 用例中
  操作类型: LoginPage.login
  username: "{{username}}"
  password: "{{password}}"
"""
from HAT.pages.base_page import BasePage
from HAT.pages.login_page import LoginPage

__all__ = ["BasePage", "LoginPage"]
