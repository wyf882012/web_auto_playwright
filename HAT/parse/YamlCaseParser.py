# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : YamlCaseParser.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
import copy
import os.path
import uuid
from shutil import Error

import yaml

from HAT.core.globalContext import g_context

#读取单个yaml
def read_yaml(file_path):
    case_infos=[] #把用例数据放在列表中
    with open(file_path,'r', encoding='utf-8') as f:
        #Loader=yaml.FullLoader安全读取
        data=yaml.load(f,Loader=yaml.FullLoader)
        # print('读取学习的yaml数据',data)
    case_infos.append(data)
    return case_infos

#读取context.yaml文件数据，拿到数据，
# 保存在全局变量
def load_context_from_yaml(folder_path):
    try:
        yaml_file_path=os.path.join(folder_path,'context.yaml')
        # print('正在读取context.yaml文件数据',yaml_file_path)
        with open(yaml_file_path,'r', encoding='utf-8') as f:
            data=yaml.load(f,Loader=yaml.FullLoader)
            # print('正在读取context.yaml文件数据',data)
            # 把数据保存在全局变量中 实现数据的共享  后续就能从这个变量中拿到数据使用
            if data:g_context().set_by_dict(data)
            # print('展示保存在全局变量中的数据',g_context().show_dict())
    except Exception as e:
        raise Error('读取context.yaml文件数据失败',e)

#思路：
# 1.读取整个yaml用例文件夹
# 2.用例的文件命名有要求  必须是数字开头下划线进行分割以.yaml介绍  不符合规则就不是我们要的用例

#读取文件夹里面符合规则的yaml文件
def load_yaml_files(config_path):
    """
    :param config_path: 用例文件夹
    :return:
    """
    yaml_caseInfos=[]
    #读取到整个文件夹
    suite_folder=os.path.join(config_path)
    #读用例之前把数据放到全局变量 以便读取用例数据的时候用
    load_context_from_yaml(suite_folder)
    #读取用例 规则 文件名必须以数字开头，数字后面跟下划线，后缀.yaml 不符合规则的就不读取
    file_names=[(int(f.split("_")[0]), f)  for f in os.listdir(suite_folder) if f.endswith('.yaml') and f.split('_')[0].isdigit()]
    file_names.sort() #排序
    file_names=[f[-1] for f in file_names]
    # print('正在读取的yaml文件',file_names)

    #读取符合规则的yaml文件数据
    for file_name in file_names:
        file_path=os.path.join(suite_folder,file_name)
        # print('正在读取的yaml文件的路径',file_path)
        with open(file_path,'r', encoding='utf-8') as rfile:
            data=yaml.load(rfile,Loader=yaml.FullLoader)
            yaml_caseInfos.append(data)
    return yaml_caseInfos


#专门处理用例中ddt数据驱动的
def yaml_case_parser(config_path):
    case_infos=[]  #存放用例数据
    case_names=[] #存放用例名称
    #拿到所有符合规则的yaml数据拿到
    yaml_caseInfos=load_yaml_files(config_path)

    # 循环所有用例数据
    for case_info in yaml_caseInfos:
        #拿数据驱动
        ddts=case_info.get("数据驱动",[])
        # print('正在处理数据驱动的数据',ddts)

        #如果有数据驱动的数据  把ddt数据删掉
        #拿用例模板
        if len(ddts)>0:
            case_info.pop("数据驱动")
        # print('只留下用例模板',case_info)

        #拼接用例模板和数据驱动的数据  有几组数据拼成几条用例
        if len(ddts)==0:  #没有数据驱动 就正常的拿数据
            #拿yaml用例标题，没有用例标题就生成一个
            case_name=case_info.get("基础配置").get("用例标题", uuid.uuid4().__str__())
            case_names.append(case_name)
            case_infos.append(case_info)

        else: #有数据驱动的数据  有几组数据拼成几条用例
            for ddt in ddts:
                new_case=copy.deepcopy(case_info)#复制用例模板数据
                new_case.update({"local_context":ddt}) #后面需要用到ddt的数据就从这里拿
                # print('用例模板+ddt数据',new_case)
                #需要知道测试用例的标题  登陆用例--密码错误  登陆用例--正常登陆
                case_name = case_info.get("基础配置").get("用例标题", uuid.uuid4().__str__())
                #登陆用例-密码错误
                case_name = f'{case_name}-{ddt.get("描述标题", uuid.uuid4().__str__())}'
                #case_name的用例标题更新到用例模板中
                new_case.get("基础配置").update({"用例标题": case_name})
                # print('更新用例标题后的数据',new_case)
                case_names.append(case_name)
                case_infos.append(new_case)
    return {
        "case_infos":case_infos,
        "case_names":case_names
    }
if __name__ == '__main__':
    #./代表当前目录
    #../上级目录
    #../../上上级目录

    a=yaml_case_parser(r'../../examples/web-cases-yaml')
    print('所有的数据都拿到了',a['case_infos'])
    print('所有的数据名称都拿到了',a['case_names'])

    # data=load_yaml_files(r'../../examples/web-cases-yaml')
    # print(data)

    # load_context_from_yaml(r'../../examples/web-cases-yaml')
    # print('展示保存在全局变量中的数据2', g_context().show_dict())
    # data=read_yaml('../../examples/web-cases-yaml/1_loginsuccess.yaml')
    # print(data)