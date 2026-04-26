# -*- coding: utf-8 -*-
"""
VarRender —— Jinja2 模板变量渲染器
====================================

核心功能:
  使用 Jinja2 模板引擎将用例中的占位符（如 {{username}}, {{password}}）
  替换为全局上下文或 DDT 参数中的真实值。

工作原理:
  在 TestRunner 执行步骤之前，调用 refresh() 方法对步骤参数字典进行
  模板渲染。例如:
    输入:  "{{username}}" + context={"username": "18318053665"}
    输出:  "18318053665"

使用示例:
  refresh("我的账号是{{username}}", {"username": "18318053665"})
  → "我的账号是18318053665"
"""
from jinja2 import Template


def refresh(target, context):
    """
    使用 Jinja2 模板引擎进行字符串变量替换。

    将 target 中的 {{变量名}} 占位符替换为 context 字典中对应键的值。

    :param target: 目标值（通常为字典或字符串），包含 {{变量名}} 占位符
    :param context: 源字典，包含 {变量名: 实际值} 的键值对
    :return: 替换后的字符串。如果 target 为 None 则返回 None
    """
    if target is None:
        return None
    return Template(str(target)).render(context)


if __name__ == '__main__':
    a = "我的姓名是,{{aname}}"
    b = {'aname': '15574113906'}
    print('打印看下返回的结果', refresh(a, b))