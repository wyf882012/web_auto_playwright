# -*- coding: utf-8 -*-
# @Author  : wyf
# @File    : CasesPlugin.py

from HAT.core.globalContext import g_context
from HAT.parse.caseParser import case_parser


# 自定义插件
class CasesPlugin:
    """
    HAT 框架的自定义 pytest 插件。

    该插件负责处理命令行参数、动态生成测试用例数据以及修复测试报告中的中文乱码问题。
    """

    def pytest_addoption(self, parser):
        """
        向 pytest 添加自定义命令行选项。

        :param parser: pytest 的参数解析器对象
        """
        parser.addoption("--type", action="store", default="yaml", help="用例类型")
        parser.addoption("--cases", action="store", help="用例路径")
        parser.addoption("--key_dir", action="store", help="扩展关键字代码文件夹路径")

    def pytest_generate_tests(self, metafunc):
        """
        在测试收集阶段动态生成参数化数据。

        根据命令行指定的用例类型（YAML 或 Excel）和路径，解析用例并传递给测试执行器。

        :param metafunc: pytest 的元函数对象，用于访问配置和生成参数化数据
        """
        case_type = metafunc.config.getoption("type")
        cases_dir = metafunc.config.getoption("cases")
        key_dir = metafunc.config.getoption("key_dir")
        g_context().set_dict("key_dir", key_dir)

        # 调用统一的解析器，根据类型自动分发到 YAML 或 Excel 解析逻辑
        data = case_parser(case_type, cases_dir)

        # 如果测试函数包含 'caseinfo' 参数，则进行参数化注入
        if "caseinfo" in metafunc.fixturenames:
            metafunc.parametrize("caseinfo", data["case_infos"], ids=data["case_names"])

    def pytest_collection_modifyitems(self, items):
        """
        修改收集到的测试项，解决中文名称在控制台和报告中显示为 Unicode 转义字符的问题。

        :param items: 收集到的所有测试项列表
        """
        for item in items:
            item.name = item.name.encode("utf-8").decode("unicode_escape")
            item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")