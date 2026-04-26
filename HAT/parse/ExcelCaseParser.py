# -*- coding: utf-8 -*-
"""
ExcelCaseParser —— Excel 用例解析器
======================================

负责从指定目录中读取 Excel (.xlsx) 格式的测试用例文件，解析为框架统一的用例数据结构。

解析流程:
  1. load_context_from_excel() — 加载 context.xlsx 的 4 个页签:
     - "数据库配置" → _数据库
     - "浏览器配置" → _浏览器
     - "WEB页面元素" → _WEB页面元素
     - "通用配置" → 直接注入 g_context（username, password, base_url 等）
  2. load_excel_files() — 扫描目录，按文件名数字前缀排序加载用例文件
  3. group_cases_by_title() — 将扁平的行数据按"用例标题"聚合成用例结构
  4. excel_case_parser() — 输出最终的 case_infos/case_names

文件命名规则:
  - context.xlsx: 全局配置文件（多页签）
  - N_*.xlsx (N 为数字): 测试用例文件，按数字前缀排序（如 1_登录模块测试.xlsx）

Excel 用例格式:
  列: 模块 | 功能 | 用例标题 | 用例类型 | 测试步骤 | 操作类型 | 数据内容
  数据内容列使用 key="value" 格式（如 username="18318053665" password="qq111111"）

POM 支持:
  操作类型列支持 POM 点分表示法（如 LoginPage.login），
  解析器对操作类型值不做特殊处理，TestRunner 在运行时根据 "." 判断是否走 POM 路径。
"""
import ast
import json
import os.path
import re
import uuid

import pandas as pd
import yaml

from HAT.core.globalContext import g_context


# 目标：把excel读取出来的数据格式变成和yaml一致的格式

def load_dbinfo(name, all_sheets):
    """
    解析 Excel 中的数据库配置页签，转换为框架所需的字典格式。
    
    :param name: 页签名称
    :param all_sheets: pandas 读取的 DataFrame 对象
    :return: 数据库配置字典
    """
    db_config = all_sheets.fillna("").to_dict(orient="records")
    config_dict = {}
    for item in db_config:
        db_info = {}
        db_name = item.get('别名')
        host = item.get('服务器IP')
        port = item.get('端口号')
        user = item.get('用户名')
        password = item.get('密码')
        db = item.get('数据库名称')

        db_info.update({"host": host})
        db_info.update({"port": port})
        db_info.update({"user": user})
        db_info.update({"password": password})
        db_info.update({"db": db})

        config_dict[db_name] = db_info
    return config_dict

def load_browserInfo(name, all_sheets):
    """
    解析 Excel 中的浏览器配置页签，转换为框架所需的字典格式。
    
    :param name: 页签名称
    :param all_sheets: pandas 读取的 DataFrame 对象
    :return: 浏览器配置字典
    """
    config_dict = {}
    br_config = all_sheets.fillna("").to_dict(orient="records")
    for item in br_config:
        browser_data = {"capability": {"browserName": item.get("浏览器名称")}}
        gird_url = item.get("Grid服务器地址(二选一)")
        driver_path = item.get("本地驱动地址(二选一)")
        capability = item.get("启动参数")

        if gird_url != "":
            browser_data["grid_url"] = gird_url
        if driver_path != "":
            browser_data["driver_path"] = driver_path
        browser_data["capability"].update(json.loads(capability))
    config_dict.update(browser_data)
    return config_dict

def load_web_ele(name, all_sheets):
    """
    解析 Excel 中的 WEB 页面元素页签，转换为框架所需的字典格式。
    
    :param name: 页签名称
    :param all_sheets: pandas 读取的 DataFrame 对象
    :return: 页面元素定位字典
    """
    web_ele = all_sheets.to_dict(orient="records")
    config_dict = {
        item["元素名称"]: {
            "定位方式": item["定位方式"],
            "目标对象": item["目标对象"]
        }
        for item in web_ele
    }
    return config_dict

def load_configuration(name, all_sheets):
    """
    解析 Excel 中的通用配置页签。
    
    :param name: 页签名称
    :param all_sheets: pandas 读取的 DataFrame 对象
    :return: 通用配置字典
    """
    config_dict = {row['配置名']: row["配置值"] for _, row in all_sheets.iterrows()}
    for key, value in config_dict.items():
        config_dict[key] = to_dict(value)
    return config_dict

def to_dict(value):
    """
    通用类型数据转换，主要处理不确定类型的数据（如 JSON 字符串）。
    
    :param value: 待转换的值
    :return: 转换后的 Python 对象
    """
    if isinstance(value, dict):
        return value
    elif isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    else:
        return value

def load_context_from_excel(folder_path):
    """
    从指定文件夹加载 context.xlsx 配置文件，并将其内容存入全局上下文。

    依次读取各个页签，缺失的页签会被跳过（不会导致错误）。

    :param folder_path: 包含 context.xlsx 的文件夹路径
    """
    excel_file_path = os.path.join(folder_path, 'context.xlsx')
    if not os.path.exists(excel_file_path):
        return

    context_data = {}
    xl = pd.ExcelFile(excel_file_path)

    # 数据库配置（可选页签）
    if "数据库配置" in xl.sheet_names:
        all_sheets = pd.read_excel(excel_file_path, sheet_name="数据库配置")
        context_data.update({"_数据库": load_dbinfo("数据库配置", all_sheets)})

    # 浏览器配置
    if "浏览器配置" in xl.sheet_names:
        all_sheets = pd.read_excel(excel_file_path, sheet_name="浏览器配置")
        context_data.update({"_浏览器": load_browserInfo("浏览器配置", all_sheets)})

    # WEB页面元素（可选页签，POM 模式下不需要）
    if "WEB页面元素" in xl.sheet_names:
        all_sheets = pd.read_excel(excel_file_path, sheet_name="WEB页面元素")
        context_data.update({"_WEB页面元素": load_web_ele("WEB页面元素", all_sheets)})

    # 通用配置
    if "通用配置" in xl.sheet_names:
        all_sheets = pd.read_excel(excel_file_path, sheet_name="通用配置")
        context_data.update(load_configuration("通用配置", all_sheets))

    if context_data:
        g_context().set_by_dict(context_data)

def group_cases_by_title(data):
    """
    将 Excel 中按行存储的步骤数据，根据“用例标题”聚合成完整的用例结构。
    
    :param data: Excel 原始行数据列表
    :return: 聚合后的用例列表
    """
    current_case = None
    result = []
    for row in data:
        module_1 = row.get('模块')
        module_2 = row.get('功能')
        title = row.get('用例标题')
        case_type = row.get('用例类型')
        if case_type is None:
            case_type = g_context().get_dict('用例类型')
        step_desc = row.get("测试步骤")
        action_type = row.get("操作类型")
        data_content = row.get("数据内容")

        # 处理数据内容字符串，将其转换为字典
        data_content_dict = {}
        if isinstance(data_content, str) and data_content.strip():
            pattern = r'(\w+)=(?:"([^"]*)"|(\S+))'
            matches = re.findall(pattern, data_content)
            for key, quoted_value, unquoted_value in matches:
                value = quoted_value if quoted_value else unquoted_value
                if value is not None:
                    data_content_dict[key] = safe_convert_value(value)
                else:
                    data_content_dict[key] = None

        # 如果遇到新的用例标题，则保存上一个用例并开始新的用例
        if title is not None and title != "":
            if current_case is not None:
                result.append(current_case)

            current_case = {"基础配置": {}, "用例步骤": []}
            current_case["基础配置"].update({"用例标题": title})
            current_case["基础配置"].update({"用例类型": case_type})
            current_case["基础配置"].update({"一级模块": module_1})
            current_case["基础配置"].update({"二级模块": module_2})

        if current_case is not None:
            current_case["用例步骤"].append({
                step_desc: {
                    "操作类型": action_type,
                    **data_content_dict
                }
            })

    if current_case is not None:
        result.append(current_case)
    return result

def safe_convert_value(value_str):
    """
    安全地将字符串转换为 Python 基本数据类型。
    
    :param value_str: 字符串形式的值
    :return: 转换后的 Python 对象
    """
    value_str = value_str.strip()
    try:
        return json.loads(value_str)
    except json.JSONDecodeError:
        pass
    try:
        return ast.literal_eval(value_str)
    except (SyntaxError, ValueError):
        return value_str

def load_excel_files(config_path):
    """
    扫描指定目录，加载所有符合命名规则的 Excel 用例文件。
    
    :param config_path: 用例文件夹路径
    :return: 包含所有用例数据的列表
    """
    excel_caseInfos = []
    suite_folder = os.path.join(config_path)
    
    # 读取 context.xlsx 并存入全局变量
    load_context_from_excel(suite_folder)
    
    # 筛选并按数字前缀排序符合条件的 xlsx 文件
    file_names = [(int(f.split("_")[0]), f) for f in os.listdir(suite_folder) if
                  f.endswith('.xlsx') and f.split('_')[0].isdigit()]
    file_names.sort()
    file_names = [f[-1] for f in file_names]

    for file_name in file_names:
        file_path = os.path.join(suite_folder, file_name)
        data = pd.read_excel(file_path, sheet_name=0)
        data = data.where(data.notnull(), None)  # 把 nan 变成 None
        data = data.to_dict(orient="records")
        
        # 将 Excel 行数据聚合成用例结构
        grop_cases = group_cases_by_title(data)
        for case in grop_cases:
            excel_caseInfos.append(case)
    return excel_caseInfos

def excel_case_parser(config_path):
    """
    Excel 用例解析器入口函数。
    
    :param config_path: 用例文件夹路径
    :return: 包含 'case_infos' 和 'case_names' 的字典
    """
    case_infos = []
    case_names = []
    excel_caseInfos = load_excel_files(config_path)
    for caseinfo in excel_caseInfos:
        case_name = caseinfo.get("基础配置").get("用例标题", uuid.uuid4().__str__())
        case_infos.append(caseinfo)
        case_names.append(case_name)
    return {
        "case_infos": case_infos,
        "case_names": case_names
    }