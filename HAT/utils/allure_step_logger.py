# -*- coding: utf-8 -*-
"""
allure_step_logger —— Allure 步骤日志增强器
===============================================

核心功能:
  1. allure_step_with_log() — 上下文管理器，在执行测试步骤时自动收集
     该步骤产生的所有日志，并将其附加到 Allure 报告中
  2. StepLogCollector — 日志收集器，临时拦截 loguru 输出到内存缓冲区
  3. _current_step_name — 线程安全的上下文变量，存储当前步骤名称，
     供 web_keywords.py 中的 get_screenshot() 获取截图标题

使用方式 (TestRunner 中):
  with allure_step_with_log("输入用户名"):
      keywords.输入内容(**kwargs)
  # 退出 with 块后，该步骤期间的所有日志会自动附加到 Allure 报告中
"""
import contextvars
import io
from contextlib import contextmanager

import allure
from loguru import logger


class StepLogCollector:
    """
    步骤日志收集器。

    利用 Python 上下文管理器协议（with 语句），在进入时向 loguru 添加
    一个临时的内存日志处理器，在退出时移除该处理器并将收集到的日志
    作为文本附件附加到 Allure 报告中。

    用法:
        with StepLogCollector():
            # 此代码块内的所有日志会被捕捉并附加到 Allure
            keywords.点击元素(...)
    """

    def __init__(self):
        # 创建内存缓冲区用于临时存储日志
        self.log_buffer = io.StringIO()
        self.sink_id = None

    def __enter__(self):
        """进入上下文: 向 loguru 添加临时内存日志处理器。"""
        self.sink_id = logger.add(self.log_buffer, level='DEBUG')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文: 移除临时处理器，将收集的日志附加到 Allure。"""
        # 移除临时日志处理器
        logger.remove(self.sink_id)
        # 将收集到的日志内容附加到 Allure 报告
        log_content = self.log_buffer.getvalue()
        if log_content.strip():
            allure.attach(
                log_content,
                name='日志内容',
                attachment_type=allure.attachment_type.TEXT
            )
        self.log_buffer.close()


# 线程安全的上下文变量:
#   存储当前正在执行的步骤名称，供其他模块（如 web_keywords.py）
#   获取当前截图所属的步骤标题，避免多线程并发场景下的数据混乱
_current_step_name = contextvars.ContextVar("current_step_name", default=None)


@contextmanager
def allure_step_with_log(step_name):
    """
    带有日志收集功能的 Allure 步骤上下文管理器。

    此装饰器将一个普通的测试步骤包装成 Allure 报告中的一个步骤节点，
    同时自动收集该步骤执行期间产生的所有日志输出。

    工作流程:
      1. 将当前步骤名称存入线程安全的上下文变量
      2. 在 Allure 报告中创建一个步骤节点
      3. 初始化日志收集器
      4. 执行实际的测试代码（yield）
      5. 退出时: 收集的日志自动附加到 Allure → 清理步骤名称上下文

    :param step_name: 当前步骤的显示名称（如 "输入用户名"）
    :yield: StepLogCollector 实例（用于收集该步骤内的日志）
    """
    token = _current_step_name.set(step_name)  # 存储当前步骤名称（线程安全）
    with allure.step(step_name):                # 创建 Allure 步骤节点
        with StepLogCollector() as collector:   # 初始化日志收集器
            yield collector                     # 执行测试代码
    _current_step_name.reset(token)             # 清理上下文，避免内存泄漏