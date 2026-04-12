# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : allure_step_logger.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈
import contextvars
import io
from contextlib import contextmanager

import allure
from loguru import logger


class StepLogCollector:
    """
    步骤日志收集器。
    
    利用上下文管理器（with 语句）临时捕获特定步骤内的日志输出，
    并在步骤结束后将其作为附件附加到 Allure 报告中。
    """
    def __init__(self):
        self.log_buffer = io.StringIO()  # 创建一个StringIO对象 临时存储日志 日记本
        self.sink_id = None

    # 进入会议
    def __enter__(self):
        self.sink_id = logger.add(self.log_buffer, level='DEBUG')
        return self

    # 结束会议
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 移除临时处理器
        logger.remove(self.sink_id)
        # 日志信息拿到放到allure中
        log_content = self.log_buffer.getvalue()
        if log_content.strip():
            allure.attach(
                log_content,
                name='日志内容',
                attachment_type=allure.attachment_type.TEXT
            )
        self.log_buffer.close()

# 保证线程安全，避免多线程场景混乱 报错的时候，解决问题去查出来
_current_step_name = contextvars.ContextVar("current_step_name", default=None)

@contextmanager    # 把普通函数变成上下文关联器，能用with语句进行管理
def allure_step_with_log(step_name):
    """
    带有日志记录的 Allure 步骤上下文管理器。
    
    :param step_name: 当前步骤的名称
    """
    token = _current_step_name.set(step_name)  # 存储当前b步骤名称
    with allure.step(step_name):  # 存储当前步骤
        with StepLogCollector() as collector:  # 收集日志
            yield collector  # 执行测试代码
    _current_step_name.reset(token)  # 清理上下文