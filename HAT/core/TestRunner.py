# -*- coding: utf-8 -*-
# @Author  : wyf
# @File    : TestRunner.py

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
from selenium import webdriver

from HAT.utils.VarRender import refresh
from HAT.utils.allure_step_logger import allure_step_with_log


class TestRunner:
    """
    测试执行器类。
    
    该类负责根据解析后的用例信息（caseinfo）执行具体的自动化测试步骤。
    它充当了“导演”的角色，协调浏览器上下文、关键字操作以及前后置脚本的执行。
    """
    def test_case_execute(self, caseinfo):
        """
        执行单个测试用例的核心方法。
        
        :param caseinfo: 包含用例基础配置、步骤、前后置脚本等信息的字典。
        """
        caseContext = None
        try:
            # 1. 获取基础配置并初始化 Allure 报告信息
            base_info = caseinfo.get("基础配置", None)
            case_type = base_info.get('用例类型')
            
            # 2. 根据用例类型初始化上下文和关键字对象
            if case_type == 'WebCase':
                caseContext = WebCaseContext()
                keywords = caseContext.init_keywords()

            # 设置 Allure 报告的层级结构：特性 -> 故事 -> 标题
            allure.dynamic.parameter("caseinfo", "")
            allure.dynamic.feature(base_info.get('一级模块', "默认模块"))
            allure.dynamic.story(base_info.get('二级模块', "默认模块"))
            allure.dynamic.title(base_info.get('用例标题', "默认模块"))

            # 3. 准备全局上下文变量
            local_context = caseinfo.get("local_context", {})  # 用于数据驱动（DDT）的参数
            context = copy.deepcopy(g_context().show_dict())
            context.update(local_context)  # 将 DDT 数据合并到上下文中

            # 4. 执行前置脚本（如果有）
            pre_script = refresh(caseinfo.get("前置脚本", None), context)
            if pre_script:
                for script in eval(pre_script):
                    # 在全局上下文中执行 Python 代码字符串
                    run_script.exec_script(script, g_context().show_dict())

            # 5. 循环执行用例步骤
            steps = caseinfo.get("用例步骤", None)
            with tqdm(total=len(steps), desc="开始执行") as pbar:
                for step in steps:
                    step_name = list(step.keys())[0]  # 步骤名称
                    step_value = list(step.values())[0]  # 步骤参数
                    print(step_name, step_value)
                    pbar.set_description(f'{base_info.get("用例标题")}-当前步骤:{step_name}')
                    pbar.update(1)

                    # 6. 渲染步骤中的模板变量（如 {{username}}）
                    context = copy.deepcopy(g_context().show_dict())
                    context.update(local_context)
                    step_value = eval(refresh(step_value, context))
                    print('渲染之后的用例数据,没有模板', step_value)

                    # 7. 调用对应的关键字函数
                    with allure_step_with_log(step_name):
                        key = step_value['操作类型']  # 获取操作类型，即关键字名称
                        try:
                            # 尝试从内置关键字类中获取方法
                            key_func = keywords.__getattribute__(key)
                            key_func(**step_value)
                        except AttributeError as e:
                            # 如果内置关键字不存在，尝试从用户自定义的关键字目录加载
                            if g_context().get_dict("key_dir") is not None:
                                keywords.ex_invoke(key=key, step_value=step_value)
                        except Exception as e:
                            print('执行用例报错了', e)
                            raise e

            # 8. 执行后置脚本（如果有）
            local_context = caseinfo.get("local_context", {})
            context = copy.deepcopy(g_context().show_dict())
            context.update(local_context)

            post_script = refresh(caseinfo.get("后置脚本", None), context)
            if post_script:
                for script in eval(post_script):
                    run_script.exec_script(script, g_context().show_dict())

        finally:
            # 9. 无论成功与否，最后都释放资源（关闭浏览器）
            if caseContext is not None:
                caseContext.release()

