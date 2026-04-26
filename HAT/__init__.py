# -*- coding: utf-8 -*-
"""
HAT (HCTest Automation Tool) 混合型企业级自动化测试框架
=========================================================

基于 Playwright + pytest + Allure 的三层架构自动化测试框架。

架构层次:
  HAT/
  ├── core/         测试核心 —— 全局上下文、用例插件（pytest）、执行器
  ├── context/      浏览器上下文 —— Playwright 生命周期管理
  ├── keywords/     关键字驱动层 —— 50+ 浏览器操作方法
  ├── pages/        POM 页面对象层 —— 页面级封装（v2026.4 新增）
  ├── parse/        用例解析器 —— YAML / Excel 双格式支持
  ├── utils/        工具函数 —— 模板渲染、日志记录
  ├── extend/       扩展模块 —— Allure 报告合并、动态脚本执行
  └── key_dir/      自定义关键字扩展目录

特性:
  - Playwright 原生选择器（text / role / placeholder / testid / css / xpath）
  - 关键字驱动 + POM 页面对象 双模式
  - YAML + Excel 双格式用例
  - 数据驱动（DDT）支持
  - Jinja2 模板变量渲染
  - AI 视觉操作与断言
"""

__version__ = "v2026.4-playwright"
__author__ = "HCTest Team"

