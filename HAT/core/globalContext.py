# -*- coding: utf-8 -*-
# @Author  : 柚一
# @File    : globalContext.py
# https://pypi.tuna.tsinghua.edu.cn/simple/
# 项目地址可能发生变化，测试数据如果太多可能随时还原。 碰到地址打不开，报错等等情况，联系班主任老师及时反馈

#全局变量类
class g_context:
    _dic={} #类属性  共享数据

    #设置字典数据 g_context().set_dict('name','Alice')  _dic={'name':'Alice'}
    def set_dict(self,key,value):
        self._dic[key]=value

    # 设置字典数据 g_context().set_dict({"age":18})  _dic={'name':'Alice',"age":18}
    def set_by_dict(self,dic):
        self._dic.update(dic)

    #得到字典数据
    def get_dict(self,key):
        return self._dic.get(key,None)

    #展示整个字典
    def show_dict(self):
        return self._dic