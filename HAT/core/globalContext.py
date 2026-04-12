# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : globalContext.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈

# 全局变量类
class g_context:
    """
    全局上下文管理类。
    
    使用单例模式的思想（通过类属性共享数据），在框架运行期间存储和传递配置信息、
    页面元素定位数据以及用例执行过程中产生的中间变量。
    """
    _dic = {}  # 类属性：用于存储所有共享数据的字典

    def set_dict(self, key, value):
        """
        设置单个键值对到全局上下文中。
        
        :param key: 键名
        :param value: 对应的值
        """
        self._dic[key] = value

    def set_by_dict(self, dic):
        """
        批量更新全局上下文，将传入字典的内容合并到现有上下文中。
        
        :param dic: 包含多个键值对的字典
        """
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
        展示当前全局上下文中的所有数据。
        
        :return: 完整的上下文字典
        """
        return self._dic