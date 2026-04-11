# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : CasesPlugin.py.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
from HAT.core.globalContext import g_context
from HAT.parse.caseParser import case_parser


#自定义插件
class CasesPlugin:
    #添加命令行参数
    def pytest_addoption(self,parser):
        parser.addoption("--type",action="store",default="yaml",help="用例类型")#类型  yaml excel
        parser.addoption("--cases",action="store",help="用例路径")#用例路径
        parser.addoption("--key_dir", action="store", help="扩展关键字")  # 扩展关键字 没有封装keywords里面 可以在其他的地方引用
        #我们在keywords里面没有找到方法，那么就从扩展关键字里面找目录


    #动态的生成参数化数据
    def pytest_generate_tests(self,metafunc):
        case_type=metafunc.config.getoption("type")#从mian里面获得用例类型
        cases_dir=metafunc.config.getoption("cases")#从mian里面获得用例路径
        key_dir=metafunc.config.getoption("key_dir")
        g_context().set_dict("key_dir",key_dir)

        #调用方法  如果你传过来的是excel调excel的方法  如果你传过来的yaml调yaml的方法  统一调用的方法
        #可能是excel,也可能是yaml的数据
        data=case_parser(case_type,cases_dir)

        #检查测试函数否需要caseinfo，需要就把数据data["case_infos"]传到核心执行器用例中去
        #ids=data["case_name"]控制台会展示用例名称
        if "caseinfo" in metafunc.fixturenames:
            metafunc.parametrize("caseinfo",data["case_infos"],ids=data["case_names"])

    #让中文不要乱码
    def pytest_collection_modifyitems(self,items):
        for item in items:
            item.name=item.name.encode("utf-8").decode("unicode_escape")
            item._nodeid=item.nodeid.encode("utf-8").decode("unicode_escape")