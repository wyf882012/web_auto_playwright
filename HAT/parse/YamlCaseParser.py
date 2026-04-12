# -*- coding: utf-8 -*-
# @Author  : wyf
# @File    : YamlCaseParser.py

import copy
import os.path
import uuid
from shutil import Error

import yaml

from HAT.core.globalContext import g_context

def read_yaml(file_path):
    """
    读取单个 YAML 文件并返回解析后的数据列表。

    :param file_path: YAML 文件的绝对或相对路径
    :return: 包含解析后字典数据的列表
    """
    case_infos = []
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    case_infos.append(data)
    return case_infos

def load_context_from_yaml(folder_path):
    """
    从指定文件夹加载 context.yaml 配置文件，并将其内容存入全局上下文。

    :param folder_path: 包含 context.yaml 的文件夹路径
    :raises Error: 当文件不存在或解析失败时抛出异常
    """
    try:
        yaml_file_path = os.path.join(folder_path, 'context.yaml')
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            if data:
                g_context().set_by_dict(data)
    except Exception as e:
        raise Error('读取context.yaml文件数据失败', e)

def load_yaml_files(config_path):
    """
    扫描指定目录，按命名规则加载所有有效的 YAML 用例文件。

    命名规则：文件名必须以数字开头，后接下划线（例如：01_登录测试.yaml）。
    
    :param config_path: 用例文件夹路径
    :return: 包含所有用例数据的列表
    """
    yaml_caseInfos = []
    suite_folder = os.path.join(config_path)
    
    # 优先加载全局配置，确保解析用例时能获取到页面元素等共享数据
    load_context_from_yaml(suite_folder)
    
    # 筛选并按数字前缀排序符合条件的 YAML 文件
    file_names = [(int(f.split("_")[0]), f) for f in os.listdir(suite_folder) if f.endswith('.yaml') and f.split('_')[0].isdigit()]
    file_names.sort()
    file_names = [f[-1] for f in file_names]

    # 依次读取并解析每个用例文件
    for file_name in file_names:
        file_path = os.path.join(suite_folder, file_name)
        with open(file_path, 'r', encoding='utf-8') as rfile:
            data = yaml.load(rfile, Loader=yaml.FullLoader)
            yaml_caseInfos.append(data)
    return yaml_caseInfos


def yaml_case_parser(config_path):
    """
    YAML 用例解析器入口函数，处理数据驱动（DDT）逻辑。

    如果用例包含“数据驱动”字段，会根据驱动数据生成多个测试实例；
    否则直接返回原始用例数据。

    :param config_path: 用例文件夹路径
    :return: 包含 'case_infos' (用例数据列表) 和 'case_names' (用例名称列表) 的字典
    """
    case_infos = []
    case_names = []
    yaml_caseInfos = load_yaml_files(config_path)

    for case_info in yaml_caseInfos:
        ddts = case_info.get("数据驱动", [])

        # 提取数据驱动后，从模板中移除该字段以避免干扰执行
        if len(ddts) > 0:
            case_info.pop("数据驱动")

        if len(ddts) == 0:
            # 无数据驱动：直接使用基础配置中的标题
            case_name = case_info.get("基础配置").get("用例标题", uuid.uuid4().__str__())
            case_names.append(case_name)
            case_infos.append(case_info)
        else:
            # 有数据驱动：为每一组数据生成一个独立的测试用例实例
            for ddt in ddts:
                new_case = copy.deepcopy(case_info)
                new_case.update({"local_context": ddt})
                
                # 组合生成具有描述性的用例标题（例如：登录测试-密码错误）
                base_title = case_info.get("基础配置").get("用例标题", uuid.uuid4().__str__())
                case_name = f'{base_title}-{ddt.get("描述标题", uuid.uuid4().__str__())}'
                new_case.get("基础配置").update({"用例标题": case_name})
                
                case_names.append(case_name)
                case_infos.append(new_case)
                
    return {
        "case_infos": case_infos,
        "case_names": case_names
    }