# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : TestRunner.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
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
    def test_case_execute(self,caseinfo):
        caseContext=None
        try:

            #基础配置 --测试报告
            base_info=caseinfo.get("基础配置",None)#{'用例类型': 'WebCase', '一级模块': '登陆功能', '二级模块': '登陆功能', '用例标题': '正常登陆用例'}
            case_type=base_info.get('用例类型')#WebCase
            if case_type=='WebCase':
                caseContext=WebCaseContext()
                keywords=caseContext.init_keywords()

            #设置在allure报告中
            allure.dynamic.parameter("caseinfo","")
            allure.dynamic.feature(base_info.get('一级模块',"默认模块"))
            allure.dynamic.story(base_info.get('二级模块',"默认模块"))
            allure.dynamic.title(base_info.get('用例标题',"默认模块"))

            #如果前置脚本的数据 也是从外部传过来的  只是考虑到后面有这种情况
            local_context=caseinfo.get("local_context",{})#这个值目前用不到，后面讲ddt的时候会用到  拿到ddt数据
            context=copy.deepcopy(g_context().show_dict())
            context.update(local_context)  #更新全局变量

            #拿前置脚本的数据
            pre_script=refresh(caseinfo.get("前置脚本", None),context)  #- "context.update({'aname':'15574113906'})"
            if pre_script:#如果前置脚本有数据
                for script in eval(pre_script):#循环前置脚本数据
                    #把前置脚本的数据放在全局变量中g_context().show_dct()
                    run_script.exec_script(script,g_context().show_dict())
                    # print('执行完前置脚本后的全局变量数据', g_context().show_dict())

            #用例步骤--具体要执行的内容  访问网址  输入内容到keywords方法去
            steps = caseinfo.get("用例步骤", None)
            with tqdm(total=len(steps),desc="开始执行")as pbar:
                for step in steps:
                    step_name=list(step.keys())[0]  #访问网址   输入手机号关键字
                    step_value=list(step.values())[0]  #{'操作类型': '访问网址', '网址': 'http://novel.hctestedu.com/user/login.html'}
                    print(step_name,step_value)
                    pbar.set_description(f'{base_info.get("用例标题")}-当前步骤:{step_name}')
                    pbar.update(1)

                    # print('没有渲染之前的用例有个模板{{xx}}',step_value)
                    #复制一下全局变量
                    context=copy.deepcopy(g_context().show_dict())#深拷贝复制全局变量，不会影响到之前的结构
                    context.update(local_context)#把ddt的数据放在全局变量
                    step_value=eval(refresh(step_value,context))
                    print('渲染之后的用例数据,没有模板',step_value)

                    with allure_step_with_log(step_name):
                    # with allure.step(step_name):#在测试报告中添加步骤  在函数里面添加with allure.step
                        key=step_value['操作类型'] #访问网址  输入内容  输入内容  点击元素
                        try:
                            # 找一下keywords中有没有key的方法名
                            key_func=keywords.__getattribute__(key)#这句代码的意思 找Keywords类里面有没有key拿出来的方法名称
                            # 找到方法名称后，调用方法  #执行用例
                            key_func(**step_value)
                        except AttributeError as e:
                            if g_context().get_dict("key_dir") is not None:#全局变量有key_dir数据
                                keywords.ex_invoke(key=key, step_value=step_value)
                        except Exception as e:
                            print('执行用例报错了',e)
                            raise e


            # 如果后置脚本的数据 也是从外部传过来的  只是考虑到后面有这种情况
            local_context = caseinfo.get("local_context", {})  # 这个值目前用不到，后面讲ddt的时候会用到
            context = copy.deepcopy(g_context().show_dict())
            context.update(local_context)

            # 拿前置脚本的数据
            pre_script = refresh(caseinfo.get("后置脚本", None), context)
            if pre_script:  # 如果前置脚本有数据
                for script in eval(pre_script):  # 循环前置脚本数据
                    # 把前置脚本的数据放在全局变量中g_context().show_dct()
                    run_script.exec_script(script, g_context().show_dict())
                    # print('执行完前置脚本后的全局变量数据', g_context().show_dict())
        finally: #不管执行成功还是失败，都会执行  关闭浏览器
            if caseContext is not None:
                caseContext.release()

