# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : caseParser.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
import os.path

from HAT.parse.ExcelCaseParser import excel_case_parser
from HAT.parse.YamlCaseParser import yaml_case_parser


# 统一调用的方法
# case_type:用例类型yaml/excel  case_dir:用例路径
def case_parser(case_type, case_dir):
    """
    统一的用例解析入口。
    
    根据传入的用例类型（yaml 或 excel），自动分发到对应的解析器进行处理。
    
    :param case_type: 用例类型字符串 ('yaml' 或 'excel')
    :param case_dir: 用例所在的文件夹路径
    :return: 包含解析后用例数据和名称的字典
    """
    config_path = os.path.join(case_dir)
    if case_type == 'yaml':
        return yaml_case_parser(config_path)
    elif case_type == 'excel':  # excel处理 拿到excel所有的数据
        return excel_case_parser(config_path)