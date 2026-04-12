# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : VarRender.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
from jinja2 import Template


# 安装pip install jinja2 -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 封装的方法：字符串模板和字典进行字符串的替换操作
def refresh(target, context):
    """
    原理：字符串模板和字典进行字符串的替换操作。
    
    使用 Jinja2 模板引擎将用例中的占位符（如 {{username}}）替换为全局上下文中的真实值。
    
    :param target: 目标值，需要是一个字符串模板，例如 '{{变量名}}'
    :param context: 源字典，包含键值对 {键:值}
    :return: 替换后的字符串
    """
    if target is None:
        return None
    return Template(str(target)).render(context)  # 实现替换操作

if __name__ == '__main__':
    a="我的姓名是,{{aname}}"
    b={'_WEB页面元素': {'手机号_输入框': {'定位方式': 'id', '目标对象': 'txtUName'}}, 'aname': '15574113906'}
    print('打印看下返回的结果',refresh(a,b))

#说这个的目的，前置{"aname":"15574113906"} 数据放在全局变量
# 字典
#{'_WEB页面元素': {'手机号_输入框': {'定位方式': 'id', '目标对象': 'txtUName'},, 'aname': '15574113906'}
# 用例步骤有个模板  '{{aname}}'