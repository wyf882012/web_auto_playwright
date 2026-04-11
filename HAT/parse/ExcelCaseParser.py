# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : ExcelCaseParser.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
import ast
import json
import os.path
import re
import uuid

import pandas as pd
import yaml

from HAT.core.globalContext import g_context


#目标：把excel读取出来的数据格式变成和yaml一致的格式

# 改数据库数据变成和yaml一致
def load_dbinfo(name,all_sheets):
    db_config=all_sheets.fillna("").to_dict(orient="records")
    # print("数据库数据",db_config)

    config_dict={}
    for item in db_config:
        db_info={}
        db_name=item.get('别名')
        host=item.get('服务器IP')
        port=item.get('端口号')
        user=item.get('用户名')
        password=item.get('密码')
        db=item.get('数据库名称')
        # print(db_name,host,port,user,password,db)

        db_info.update({"host":host})
        db_info.update({"port":port})
        db_info.update({"user":user})
        db_info.update({"password":password})
        db_info.update({"db":db})

        config_dict[db_name]=db_info
    return config_dict

# 改浏览器配置数据变成和yaml一致
def load_browserInfo(name,all_sheets):
    config_dict={}
    br_config=all_sheets.fillna("").to_dict(orient="records")
    # print("浏览器数据",br_config)
    for item in br_config:
        browser_data={"capability":{"browserName":item.get("浏览器名称")}}
        gird_url=item.get("Grid服务器地址(二选一)")#只是拿值，还没放在字典
        driver_path=item.get("本地驱动地址(二选一)")
        capability=item.get("启动参数")

        if gird_url!="":
            browser_data["grid_url"]=gird_url
        if driver_path!="":
            browser_data["driver_path"]=driver_path
        browser_data["capability"].update(json.loads(capability))
    config_dict.update(browser_data)
    return config_dict

# 改页面元素数据变成和yaml一致
def load_web_ele(name,all_sheets):
    web_ele=all_sheets.to_dict(orient="records")
    #字典推导式  简洁一点  config_dict={}  for item in web_ele:  key=item["元素名称"]
    # value={"定位方式":item["定位方式"],"目标对象":item["目标对象"]} config_dict[key]=value
    config_dict={
        item["元素名称"]:{
            "定位方式":item["定位方式"],
            "目标对象":item["目标对象"]
        }
        for item in web_ele
    }
    return config_dict

def load_configuration(name,all_sheets):
    config_dict={row['配置名']:row["配置值"]  for _,row in all_sheets.iterrows()}
    # print(config_dict)

    for key,value in config_dict.items():
        config_dict[key]=to_dict(value)
    return config_dict

#通用类型数据转换 主要处理不确定类型的数据
def to_dict(value):
    if isinstance(value, dict):  # 如果值已经是字典，直接返回
        return value
    elif isinstance(value, str):  # 如果是字符串，尝试解析为 JSON
        try:
            return json.loads(value)  # 成功则返回解析后的字典/列表
        except json.JSONDecodeError:   # 解析失败（不是合法 JSON），返回原字符串
            return value
    else:    # 其他类型（如数字、布尔值、列表等），直接返回
        return value

#读取context.xlsx数据
def load_context_from_excel(folder_path):
    #context.xlsx数据拿出来
    excel_file_path=os.path.join(folder_path, 'context.xlsx')

    #存储所有context.xlsx数据  数据库配置....
    context_data={}

    #读取数据库的数据
    all_sheets=pd.read_excel(excel_file_path,sheet_name="数据库配置")
    # print("数据库数据",all_sheets)
    #改数据变成和yaml一致
    config_dict=load_dbinfo("数据库配置",all_sheets)
    context_data.update({"_数据库":config_dict})

    #浏览器配置
    all_sheets = pd.read_excel(excel_file_path, sheet_name="浏览器配置")
    config_dict=load_browserInfo("浏览器配置",all_sheets)
    context_data.update({"_浏览器":config_dict})

    # web页面元素定位
    all_sheets = pd.read_excel(excel_file_path, sheet_name="WEB页面元素")
    config_dict = load_web_ele("WEB页面元素", all_sheets)
    context_data.update({"_WEB页面元素": config_dict})

    # 通用配置
    all_sheets = pd.read_excel(excel_file_path, sheet_name="通用配置")
    config_dict = load_configuration("通用配置", all_sheets)
    context_data.update(config_dict)

    if context_data:g_context().set_by_dict(context_data)

def group_cases_by_title(data):
    current_case=None
    result=[]
    for row in data:
        module_1=row.get('模块')
        module_2=row.get('功能')
        title=row.get('用例标题')
        case_type=row.get('用例类型')
        if case_type is None:
            case_type=g_context().get_dict('用例类型')
        step_desc=row.get("测试步骤")
        action_type=row.get("操作类型")
        data_content=row.get("数据内容")
        # print(module_1,module_2,title,case_type,step_desc,action_type,data_content)

        #处理用例数据
        #_页面元素=登录页面_用户名
        # 数据内容=15071113907
        #{数据内容:15071113907}
        data_content_dict={}#空字典
        if data_content is not None and data_content!="":#数据不为空
            pattern = r'(\w+)=(?:"([^"]*)"|(\S+))'  #匹配 网址 = xxxx
            matches = re.findall(pattern, data_content)
            # print("匹配结果",matches)
            #key '网址'  quoted_value带引号的值  不带引号的值
            for key, quoted_value, unquoted_value in matches:
                value = quoted_value if quoted_value else unquoted_value
                # print('字段名',key,'值',value)
                if value is not None:
                    data_content_dict[key]=safe_convert_value(value) #添加字段名和值{'网址':http://192.168.1.41:18001/user/login.html}  '[1,2,3]'==[1,2,3]
                else:
                    data_content_dict[key] = None
            # print("数据内容",data_content_dict)

        if title is not None and title!="":
            #如果当前的用例不为空，将当前的用例添加到结果中
            if current_case is not None:
                result.append(current_case)

            current_case={"基础配置":{},"用例步骤":[]}
            current_case["基础配置"].update({"用例标题":title})
            current_case["基础配置"].update({"用例类型":case_type})
            current_case["基础配置"].update({"一级模块":module_1})
            current_case["基础配置"].update({"二级模块":module_2})

        if current_case is not None:
            current_case["用例步骤"].append({
                step_desc:{
                    "操作类型":action_type,
                    **data_content_dict
                }
            })

    if current_case is not None:
        result.append(current_case)
    print("结果",result)
    return result

#数据类型转换
def safe_convert_value( value_str):
    # 使用 .strip() 方法去除字符串两端的空白字符（如空格、换行、制表符等），防止因多余空格导致解析失败。
    value_str = value_str.strip()

    # 先尝试 JSON 解析（支持 true/false）
    try:
        return json.loads(value_str)  # 解析json格式字符串 字符串 “”  true
    except json.JSONDecodeError:
        pass
    # 再尝试 Python 字面量解析（支持单引号）
    try:
        return ast.literal_eval(value_str)  # 解析 Python 字面量表达式 单双引号  True
    except (SyntaxError, ValueError):
        return value_str

#Excel用例数据格式转成和yaml用例一样的格式

#专门处理excel用例  读取文件夹里面符合规则的yaml文件
def load_excel_files(config_path):
    excel_caseInfos = []
    # 读取到整个excel文件夹
    suite_folder = os.path.join(config_path)
    # 读用例之前把数据放到全局变量 以便读取用例数据的时候用
    load_context_from_excel(suite_folder)
    # 读取用例 规则 文件名必须以数字开头，数字后面跟下划线，后缀.xlsx 不符合规则的就不读取
    file_names = [(int(f.split("_")[0]), f) for f in os.listdir(suite_folder) if
                  f.endswith('.xlsx') and f.split('_')[0].isdigit()]
    file_names.sort()  # 排序
    file_names = [f[-1] for f in file_names]

    #读取符合规则的xlsx数据
    for file_name in file_names:
        file_path = os.path.join(suite_folder, file_name)
        data=pd.read_excel(file_path, sheet_name=0)
        # print('正在读取符合规则的xlsx文件数据',data)
        data=data.where(data.notnull(),None)#把nan变成None
        data=data.to_dict(orient="records")
        #读取xlsx的数据  注意Excel用例数据格式转成和yaml用例一样的格式
        grop_cases=group_cases_by_title(data)
        for case in grop_cases:
            excel_caseInfos.append(case)
    return excel_caseInfos

#和yaml返回的数据统一  没有做数据驱动
def excel_case_parser(config_path):
    case_infos=[]
    case_names=[]
    excel_caseInfos=load_excel_files(config_path) #拿到所有符合规则的xlsx数据
    for caseinfo in excel_caseInfos:
        case_name=caseinfo.get("基础配置").get("用例标题", uuid.uuid4().__str__())
        case_infos.append(caseinfo)
        case_names.append(case_name)
    return {
        "case_infos": case_infos,
        "case_names": case_names
    }



#测试代码，给运行之前，xlsx的数据变成和yaml格式一致，只用看,
if __name__ == '__main__':
    # load_context_from_excel('../../examples/web-cases-excel')
    # load_context_exlce=g_context().show_dict()
    # with open("./context_excel.yaml",'w',encoding='utf-8') as f:
    #     yaml.dump(load_context_exlce,f,allow_unicode=True)

    all_excel_data= load_excel_files('../../examples/web-cases-excel')
    with open("./写入_excel.yaml",'w',encoding='utf-8') as f:
        yaml.dump(all_excel_data,f,allow_unicode=True)