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
def case_parser(case_type,case_dir):
    config_path=os.path.join(case_dir)
    if case_type=='yaml':
        return yaml_case_parser(config_path)
    elif case_type=='excel':  # excel处理 拿到excel所有的数据
        return excel_case_parser(config_path)