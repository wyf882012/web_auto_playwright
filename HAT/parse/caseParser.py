# -*- coding: utf-8 -*-
"""
caseParser —— 统一用例解析入口
================================

根据命令行传入的 --type 参数，自动分发到对应解析器:
  - type=yaml → YamlCaseParser
  - type=excel → ExcelCaseParser

两种格式输出的数据结构完全一致，保证了后续 TestRunner 处理逻辑的统一。
"""
import os.path
from HAT.parse.ExcelCaseParser import excel_case_parser
from HAT.parse.YamlCaseParser import yaml_case_parser


def case_parser(case_type, case_dir):
    """
    统一的用例解析入口函数。

    根据用例类型字符串，自动调用对应的解析器。

    :param case_type: "yaml" 或 "excel"
    :param case_dir:  用例文件夹路径
    :return: dict → {"case_infos": [...], "case_names": [...]}
    """
    config_path = os.path.join(case_dir)
    if case_type == "yaml":
        return yaml_case_parser(config_path)
    elif case_type == "excel":
        return excel_case_parser(config_path)
    else:
        raise ValueError(f"不支持的用例类型: {case_type}，请使用 yaml 或 excel")
