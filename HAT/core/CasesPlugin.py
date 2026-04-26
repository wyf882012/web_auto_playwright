# -*- coding: utf-8 -*-
"""
CasesPlugin —— pytest 自定义插件
================================

此插件负责:
  1. 注册自定义命令行选项（--type, --cases, --key_dir）
  2. 在测试收集阶段动态生成参数化测试数据
  3. 修复中文测试名称在控制台和报告中的显示问题

工作原理:
  - pytest_addoption: 向 pytest 添加框架特有的命令行参数
  - pytest_generate_tests: 根据 --type 和 --cases 参数，
    调用 case_parser 解析用例文件，生成 caseinfo 参数列表，
    传递给 TestRunner.test_case_execute 方法
  - pytest_collection_modifyitems: 修复 test item 名称编码问题
"""
from HAT.core.globalContext import g_context
from HAT.parse.caseParser import case_parser


class CasesPlugin:
    """
    HAT 框架的 pytest 自定义插件。

    该插件连接了"命令行参数"和"用例数据"之间的桥梁。
    """

    def pytest_addoption(self, parser):
        """
        向 pytest 注册自定义命令行选项。

        --type:   用例类型（yaml | excel）
        --cases:  用例文件夹路径
        --key_dir: 自定义关键字代码文件夹路径（可选）
        """
        parser.addoption("--type", action="store", default="yaml", help="用例类型: yaml / excel")
        parser.addoption("--cases", action="store", help="用例文件夹路径")
        parser.addoption("--key_dir", action="store", help="扩展关键字代码文件夹路径")

    def pytest_generate_tests(self, metafunc):
        """
        在测试收集阶段动态生成参数化数据。

        pytest 在收集测试函数时会调用此方法。如果测试函数包含
        'caseinfo' 参数，此方法会根据命令行参数解析用例文件，
        并将每条用例作为独立的测试实例注入。

        :param metafunc: pytest 的元函数对象，可访问配置和注入参数
        """
        case_type = metafunc.config.getoption("type")        # "yaml" 或 "excel"
        cases_dir = metafunc.config.getoption("cases")       # 用例文件夹路径
        key_dir = metafunc.config.getoption("key_dir")       # 自定义关键字目录
        g_context().set_dict("key_dir", key_dir)

        # 调用统一解析器，根据 case_type 自动分发到 YAML 或 Excel 解析逻辑
        data = case_parser(case_type, cases_dir)

        # 如果测试函数需要 'caseinfo' 参数，则进行参数化注入
        if "caseinfo" in metafunc.fixturenames:
            # ids 参数用于在 pytest 输出中显示用例名称
            metafunc.parametrize("caseinfo", data["case_infos"], ids=data["case_names"])

    def pytest_collection_modifyitems(self, items):
        """
        修复测试项的编码问题。

        解决中文名称在 pytest 控制台和 Allure 报告中显示为
        Unicode 转义字符（如 \u767b\u5f55）的问题。

        :param items: pytest 收集到的所有测试项列表
        """
        for item in items:
            item.name = item.name.encode("utf-8").decode("unicode_escape")
            item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")
