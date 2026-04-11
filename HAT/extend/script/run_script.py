# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : run_script.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈

#script前置脚本的数据  context.update({'aname':'15574113906'})
#context全局变量  congtext.yaml元素定位数据
def exec_script(script,context):
    if script is None:return
    exec(script,{"context":context})

# exec是一个内置函数，动态执行python代码
#exec能让字符串的代码变成可执行的代码