# -*- coding: utf-8 -*-
"""
run_script —— 动态 Python 脚本执行器
=======================================

核心功能:
  在测试用例的前置脚本（pre_script）和后置脚本（post_script）阶段，
  动态执行 Python 代码字符串，使得测试用例可以包含自定义逻辑。

使用场景:
  - 前置脚本: 动态生成测试数据、设置初始状态
    例如: context.update({'aname': '15574113906'})
  - 后置脚本: 清理测试数据、记录执行结果

工作原理:
  YAML/Excel 用例中的"前置脚本"或"后置脚本"字段需要是 Python 代码
  字符串的列表:
    前置脚本:
      - context.update({'timestamp': '20260426'})  # 生成测试时间戳

  TestRunner 会遍历 eval 后的脚本列表，逐条调用 exec_script() 执行。
  exec() 函数将代码字符串编译为可执行的 Python 代码，并在包含 context
  全局字典的命名空间中执行，这样脚本就可以直接通过 context 变量访问
  全局上下文数据。
"""


def exec_script(script, context):
    """
    动态执行 Python 代码字符串。

    :param script: Python 代码字符串。如果为 None 或空则直接返回
    :param context: 全局上下文字典，在脚本中可通过 context 变量访问
                    例如在脚本中写 context['key'] = value 来修改全局上下文

    示例:
      exec_script("context.update({'aname': '15574113906'})",
                  {"_WEB页面元素": {...}})
    """
    if script is None:
        return
    # exec() 是 Python 内置函数，将字符串形式的代码编译并在指定命名空间中执行
    # 这里将 context 字典作为全局命名空间注入，脚本可直接操作 context 变量
    exec(script, {"context": context})