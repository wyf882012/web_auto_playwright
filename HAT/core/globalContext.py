# -*- coding: utf-8 -*-
"""
globalContext —— 全局上下文管理（单例模式）
============================================

在框架运行期间，所有测试用例共享此全局上下文。
存储内容包括:
  - 配置信息（浏览器类型、session 复用策略等）
  - 页面元素定位数据（_WEB页面元素）
  - 数据库连接信息（_数据库）
  - 用例执行过程中产生/提取的中间变量
  - AI 大模型相关配置

设计:
  使用类属性 _dic 实现单例效果 —— 所有 g_context() 实例共享同一份数据。
"""
class g_context:
    """
    全局上下文管理类。

    通过类属性 _dic 在框架运行期间存储和传递共享数据。
    使用方法:
      ctx = g_context()
      ctx.set_dict("key", value)     # 设置单个值
      ctx.set_by_dict({k: v, ...})   # 批量设置
      ctx.get_dict("key")            # 获取值
      ctx.show_dict()                # 获取全部数据（浅拷贝）
    """
    _dic = {}  # 类属性：所有实例共享的数据字典

    def set_dict(self, key, value):
        """设置单个键值对到全局上下文中。"""
        self._dic[key] = value

    def set_by_dict(self, dic):
        """批量合并字典到全局上下文。"""
        if dic:
            self._dic.update(dic)

    def get_dict(self, key):
        """
        从全局上下文中获取指定键的值。

        :param key: 要查询的键名
        :return: 对应的值，若不存在则返回 None
        """
        return self._dic.get(key, None)

    def show_dict(self):
        """
        返回当前全局上下文中的所有数据。

        :return: 完整的上下文字典
        """
        return self._dic
