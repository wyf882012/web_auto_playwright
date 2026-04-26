# -*- coding: utf-8 -*-
"""
TestRunner —— 测试执行器（Playwright 版）
=========================================

该类是框架的"导演"，负责根据解析后的用例信息（caseinfo）执行具体的自动化测试步骤。

执行流程:
  1. 读取基础配置，根据用例类型（WebCase）初始化对应上下文和关键字对象
  2. 设置 Allure 报告层级结构（特性 → 故事 → 标题）
  3. 合并全局上下文与数据驱动（DDT）参数
  4. 执行前置脚本（Python 代码字符串）
  5. 逐条执行用例步骤 —— 渲染 Jinja2 模板变量 → 三级解析调用方法
  6. 执行后置脚本
  7. 最终释放资源（关闭浏览器、生成截图回放）

三级解析机制（步骤派发优先级）:
  Level 1 — POM 页面对象方法:  操作类型: "LoginPage.login"   (点分表示法)
  Level 2 — Keywords 内置关键字: 操作类型: "输入内容"          (中文方法名)
  Level 3 — ex_invoke 自定义扩展: 操作类型: "自定义关键字"     (动态加载)

与 Playwright 的集成:
  - WebCaseContext 负责 Playwright 浏览器生命周期管理和 POM 页面对象注册
  - Keywords 封装了所有 Playwright 页面操作方法
  - 测试步骤通过 YAML/Excel 中的"操作类型"字段映射到 Keywords 方法或 POM 方法
"""
import copy
import allure
import pytest
from tqdm import tqdm

from HAT.context.WebCaseContext import WebCaseContext
from HAT.core.globalContext import g_context
from HAT.extend.script import run_script
from HAT.keywords.web_keywords import Keywords
from HAT.parse.ExcelCaseParser import load_excel_files
from HAT.parse.YamlCaseParser import read_yaml, load_context_from_yaml, load_yaml_files, yaml_case_parser
from HAT.utils.VarRender import refresh
from HAT.utils.allure_step_logger import allure_step_with_log


class TestRunner:
    """
    测试执行器类。

    作为 pytest 测试函数的宿主，`test_case_execute` 方法会被 pytest 参数化调用，
    每个 caseinfo 字典对应一个独立的测试用例实例。

    步骤派发采用三级解析机制:
      1. POM 点分表示法 — "LoginPage.login" → 页面对象方法
      2. Keywords 内置关键字 — "输入内容"    → Keywords 类方法
      3. ex_invoke 自定义扩展 — "自定义关键字" → 动态加载模块
    """

    def _invoke_pom_method(self, key: str, step_value: dict):
        """
        解析并调用 POM 页面对象方法。

        点分表示法格式: "PageClassName.methodName"
        例如:
          - "LoginPage.login"                    → LoginPage 实例的 login() 方法
          - "LoginPage.enter_username"           → LoginPage 实例的 enter_username() 方法
          - "LoginPage.navigate_to_login"        → LoginPage 实例的 navigate_to_login() 方法
          - "LoginPage.verify_login_page_elements" → LoginPage 实例的 verify_login_page_elements() 方法

        工作流程:
          1. 根据 "." 拆分类名和方法名
          2. 从 g_context 的 _POM_PAGES 字典中查找对应的页面对象实例
          3. 通过 getattr 获取方法并调用

        :param key: "PageClass.method" 格式的字符串
        :param step_value: 步骤参数字典（解包为 **kwargs 传递给 POM 方法）
        :raises KeyError: 如果页面类未在 _POM_PAGES 中注册
        :raises AttributeError: 如果指定的方法在页面对象上不存在
        """
        from HAT.core.globalContext import g_context

        # 1. 拆分类名和方法名
        #    例如: "LoginPage.login" → class_name="LoginPage", method_name="login"
        dot_index = key.index(".")
        class_name = key[:dot_index]
        method_name = key[dot_index + 1:]

        # 2. 从全局上下文中查找已注册的页面对象
        pom_pages = g_context().get_dict("_POM_PAGES") or {}
        if class_name not in pom_pages:
            available = list(pom_pages.keys())
            raise KeyError(
                f"未找到注册的页面对象: '{class_name}'，"
                f"已注册的页面对象: {available}，"
                f"请确认页面对象已在 WebCaseContext._init_page_objects() 中注册"
            )

        # 3. 获取页面对象实例并调用其方法
        page_obj = pom_pages[class_name]
        try:
            pom_method = getattr(page_obj, method_name)
        except AttributeError:
            methods = [m for m in dir(page_obj)
                       if not m.startswith('_') and callable(getattr(page_obj, m))]
            raise AttributeError(
                f"页面对象 '{class_name}' 中未找到方法: '{method_name}'，"
                f"可用方法: {methods}"
            )

        # 4. 准备调用参数 —— 移除内部元数据键（操作类型），只保留业务参数
        call_params = {k: v for k, v in step_value.items()
                       if k not in ("操作类型", "_页面元素", "INDEX")}

        # 5. 调用 POM 方法，将业务参数作为关键字参数传入
        pom_method(**call_params)

    def test_case_execute(self, caseinfo):
        """
        执行单个测试用例的核心方法。

        :param caseinfo: 包含以下字段的字典:
            - 基础配置: 用例类型、一级模块、二级模块、用例标题
            - 用例步骤: 步骤列表，每步包含 {步骤名称: {操作类型, ...}}
            - 数据驱动: (可选) DDT 参数数组
            - 前置脚本: (可选) Python 代码字符串
            - 后置脚本: (可选) Python 代码字符串
            - local_context: (内部) DDT 注入的本地变量
        """
        caseContext = None
        try:
            # ── 1. 获取基础配置，初始化 Allure 报告 ──
            base_info = caseinfo.get("基础配置", {})
            case_type = base_info.get("用例类型")

            # ── 2. 根据用例类型初始化上下文和关键字 ──
            if case_type == "WebCase":
                caseContext = WebCaseContext()
                keywords = caseContext.init_keywords()

            # 设置 Allure 报告的层级结构
            allure.dynamic.parameter("caseinfo", "")
            allure.dynamic.feature(base_info.get("一级模块", "默认模块"))
            allure.dynamic.story(base_info.get("二级模块", "默认模块"))
            allure.dynamic.title(base_info.get("用例标题", "默认标题"))

            # ── 3. 准备上下文变量 ──
            # local_context 来自数据驱动的每组参数
            local_context = caseinfo.get("local_context", {})
            context = copy.deepcopy(g_context().show_dict())
            context.update(local_context)

            # ── 4. 执行前置脚本 ──
            # 前置脚本可以是 Python 代码字符串列表，用于动态生成测试数据
            pre_script = refresh(caseinfo.get("前置脚本", None), context)
            if pre_script:
                for script in eval(pre_script):
                    run_script.exec_script(script, g_context().show_dict())

            # ── 5. 循环执行用例步骤 ──
            steps = caseinfo.get("用例步骤", [])
            with tqdm(total=len(steps), desc="执行进度") as pbar:
                for step in steps:
                    step_name = list(step.keys())[0]  # 步骤名称（如"输入用户名"）
                    step_value = list(step.values())[0]  # 步骤参数（字典）

                    print(f"  [{step_name}] {step_value}")
                    pbar.set_description(f'{base_info.get("用例标题")} - 当前: {step_name}')
                    pbar.update(1)

                    # 渲染模板变量（将 {{username}} 替换为实际值）
                    context = copy.deepcopy(g_context().show_dict())
                    context.update(local_context)
                    step_value = eval(refresh(step_value, context))

                    # 执行步骤 —— 用 Allure 步骤包装并记录日志
                    with allure_step_with_log(step_name):
                        key = step_value["操作类型"]  # 关键字名称（如"输入内容"、"LoginPage.login"）

                        # ── 三级解析机制 ──
                        # Level 1: POM 点分表示法 → "LoginPage.login"
                        # Level 2: Keywords 内置关键字 → "输入内容"、"点击元素" 等
                        # Level 3: ex_invoke 自定义扩展 → 从 key_dir 动态加载
                        try:
                            if "." in key:
                                # ── POM 模式: "LoginPage.login" 点分表示法 ──
                                self._invoke_pom_method(key, step_value)
                            else:
                                # ── 关键字模式（保持向后兼容）──
                                try:
                                    # 从 Keywords 类中查找匹配的方法
                                    key_func = keywords.__getattribute__(key)
                                    key_func(**step_value)
                                except AttributeError:
                                    # 内置关键字不存在时，尝试从用户自定义的关键字目录加载
                                    if g_context().get_dict("key_dir") is not None:
                                        keywords.ex_invoke(key=key, step_value=step_value)
                                    else:
                                        raise AttributeError(
                                            f"未找到关键字方法: '{key}'，"
                                            f"请检查操作类型名称是否正确，"
                                            f"或确认 key_dir 路径是否已配置"
                                        )
                        except Exception as e:
                            print(f"执行步骤 '{step_name}' 时出错: {e}")
                            raise

            # ── 6. 执行后置脚本 ──
            local_context = caseinfo.get("local_context", {})
            context = copy.deepcopy(g_context().show_dict())
            context.update(local_context)
            post_script = refresh(caseinfo.get("后置脚本", None), context)
            if post_script:
                for script in eval(post_script):
                    run_script.exec_script(script, g_context().show_dict())

        finally:
            # ── 7. 释放资源 ──
            # 无论测试成功与否，都要关闭浏览器和生成截图回放
            if caseContext is not None:
                caseContext.release()
