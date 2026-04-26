# -*- coding: utf-8 -*-
"""
web_keywords —— Playwright 版关键字类
======================================

这是框架的"演员"，封装了所有与浏览器交互的底层操作。
每个关键字方法对应 YAML/Excel 用例中"操作类型"字段的值。

Playwright 选择器体系（优先级从高到低）:
  text        — 文本精确匹配，最简洁: text=登录
  placeholder — 占位符文本: [placeholder='请输入邮箱']
  role        — 语义角色: role=button[name="登录"]
  testid      — 测试ID: [data-testid='submit-btn']
  css         — CSS 选择器: .btn-primary, input[type="password"]
  xpath       — XPath (兜底方案，不推荐首选)

内置关键字一览:
  【页面导航】 访问网址、页面刷新、页面前进、页面后退
  【元素操作】 点击元素、输入内容、清空输入框、鼠标悬停、双击元素、右键点击
  【表单操作】 选择下拉框选项、勾选复选框、取消勾选、上传文件
  【获取信息】 获取元素文本、获取元素属性、获取当前URL、获取页面标题
  【断言验证】 断言文本(含多种比较符)、断言元素存在/不存在、断言页面标题、断言浏览器路径
  【等待控制】 强制等待
  【窗口管理】 关闭浏览器、窗口最大化、切换窗口、关闭当前页面
  【iframe】   iframe_switch_to、iframe_to_default_content
  【键盘鼠标】 键盘按键、拖拽元素、滚动到元素、滚动页面
  【数据库】   提取数据MYSQL
  【验证码】   image_recognition (ddddocr)
  【变量存储】 store_text、random_six_digit_number
  【AI操作】   AI操作 (视觉模型识别+操作)、AI断言 (视觉模型判断)
  【JS执行】   执行JS
"""
import base64
import json
import os
import random
import re
import sys
import time
import uuid

import allure
import pymysql
from ddddocr import DdddOcr
from loguru import logger
from pymysql import cursors

from HAT.core.globalContext import g_context
from HAT.utils.allure_step_logger import _current_step_name


class Keywords:
    """
    Web 自动化关键字类（Playwright 版）。

    封装所有与浏览器交互的底层操作。
    所有方法通过 **kwargs 接收参数，与 YAML/Excel 用例结构完全对应。

    :param page:    Playwright Page 对象（当前标签页）
    :param context: Playwright BrowserContext 对象（浏览器会话）
    :param browser: Playwright Browser 对象（浏览器实例）
    """

    def __init__(self, page, context, browser):
        self.page = page
        self.context = context
        self.browser = browser
        self.screen_shots = []

    # ───────────────── 定位器辅助方法 ─────────────────
    def _build_selector(self, **kwargs):
        """
        根据 context.yaml/Excel 中定义的元素名称，构建 Playwright 原生选择器。

        Playwright 选择器优先级（从高到低）:
          1. role    — role=button[name="登录"]  语义化角色定位，最稳定
          2. text    — text=登录                  精确文本匹配，简洁高效
          3. placeholder — placeholder=请输入邮箱  占位符文本匹配
          4. testid  — [data-testid="login-btn"] 测试专用属性，最可靠
          5. css     — .btn-primary              标准 CSS 选择器
          6. xpath   — xpath=//button             兜底方案，不推荐首选

        还兼容旧版定位方式: id / name / class / tag
        """
        all_ele_data = g_context().get_dict("_WEB页面元素") or {}
        key = str(kwargs.get("_页面元素", ""))
        if key not in all_ele_data:
            raise Exception(f"未找到页面元素定义: '{key}'，请检查 context.yaml 或 context.xlsx")
        ele_data = all_ele_data[key]
        loc_type = str(ele_data.get("定位方式", "text")).lower()
        target = ele_data.get("目标对象", "")

        # Playwright 原生选择器引擎映射
        selector_map = {
            # --- Playwright 原生引擎（推荐） ---
            # 语义角色: role=button[name="登录"]
            "role": target,
            # 精确文本: text=登录
            "text": f"text={target}",
            # 占位符: placeholder=请输入邮箱
            "placeholder": f"[placeholder='{target}']",
            # 测试ID: data-testid="submit-btn"
            "testid": f"[data-testid='{target}']",
            # --- 兼容旧版定位方式 ---
            "id": f"#{target}",
            "name": f'[name="{target}"]',
            "class": f".{target}",
            "css": target,
            "css selector": target,
            "xpath": f"xpath={target}",
            "tag": target,
        }
        selector = selector_map.get(loc_type, f"text={target}")
        return selector

    def _get_selector_with_index(self, **kwargs):
        """构建选择器，并处理 INDEX 参数（第几个匹配元素）。"""
        selector = self._build_selector(**kwargs)
        index = int(kwargs.get("INDEX", 0))
        if index > 0:
            selector = f"{selector} >> nth={index}"
        return selector

    # ───────────────── 截图方法 ─────────────────
    def get_screenshot(self):
        """截取当前页面并附加到 Allure 报告。"""
        try:
            img_bytes = self.page.screenshot(full_page=False)
            img_base64 = base64.b64encode(img_bytes).decode("ascii")
            self.screen_shots.append({
                "image": f"data:image/png;base64,{img_base64}",
                "caption": _current_step_name.get() or ""
            })
            allure.attach(img_bytes, "截图", allure.attachment_type.PNG)
        except Exception as e:
            logger.warning(f"截图失败: {e}")

    def show_log(self, data_name, data=None):
        logger.debug(f"------------- Log:{data_name} ------------")
        logger.debug(f"{data_name}: {data}")
        logger.debug(f"----------------- END Log:{data_name} ------------")

    # ───────────────── 内置关键字方法 ─────────────────
    @allure.step("访问网址")
    def 访问网址(self, **kwargs):
        url = kwargs.get("网址", "")
        timeout = int(kwargs.get("超时", 30000))
        wait_until = kwargs.get("等待方式", "domcontentloaded")
        self.page.goto(url, timeout=timeout, wait_until=wait_until)
        self.get_screenshot()

    @allure.step("点击元素")
    def 点击元素(self, **kwargs):
        self.show_log("点击元素", kwargs)
        selector = self._get_selector_with_index(**kwargs)
        timeout = int(kwargs.get("超时", 10000))
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        self.page.click(selector)
        self.get_screenshot()

    @allure.step("输入内容")
    def 输入内容(self, **kwargs):
        self.show_log("输入内容", kwargs)
        selector = self._get_selector_with_index(**kwargs)
        content = str(kwargs.get("数据内容", ""))
        timeout = int(kwargs.get("超时", 10000))
        # 是否先清除后输入
        clear_first = kwargs.get("先清除", True)
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        if clear_first:
            self.page.fill(selector, "")
        self.page.fill(selector, content)
        self.get_screenshot()

    @allure.step("输入内容(追加)")
    def 输入内容追加(self, **kwargs):
        """不先清除，直接追加输入。"""
        self.show_log("输入内容追加", kwargs)
        selector = self._get_selector_with_index(**kwargs)
        content = str(kwargs.get("数据内容", ""))
        timeout = int(kwargs.get("超时", 10000))
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        self.page.type(selector, content, delay=50)
        self.get_screenshot()

    @allure.step("清空输入框")
    def 清空输入框(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        self.page.fill(selector, "")
        self.get_screenshot()

    @allure.step("关闭浏览器")
    def 关闭浏览器(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()

    @allure.step("窗口最大化")
    def 窗口最大化(self):
        # Playwright 通过 viewport 设置窗口大小，这里设为全高清
        self.page.set_viewport_size({"width": 1920, "height": 1080})

    @allure.step("强制等待")
    def 强制等待(self, **kwargs):
        seconds = float(kwargs.get("数据内容", 1))
        time.sleep(seconds)

    @allure.step("获取元素文本")
    def 获取元素文本(self, **kwargs):
        try:
            selector = self._get_selector_with_index(**kwargs)
            self.page.wait_for_selector(selector, state="visible", timeout=10000)
            ex_data = self.page.text_content(selector)
            print(f"获取文本值: {ex_data}")
            g_context().set_dict(kwargs.get("变量名", "temp_var"), ex_data)
            logger.info(f"获取文本值成功: {ex_data}")
        except Exception as e:
            logger.error(f"获取文本值失败: {e}")
            raise e

    @allure.step("获取元素属性")
    def 获取元素属性(self, **kwargs):
        """获取元素的指定属性值。"""
        try:
            selector = self._get_selector_with_index(**kwargs)
            attr_name = kwargs.get("属性名", "value")
            self.page.wait_for_selector(selector, state="visible", timeout=10000)
            attr_value = self.page.get_attribute(selector, attr_name)
            g_context().set_dict(kwargs.get("变量名", "temp_var"), attr_value)
            logger.info(f"获取属性 {attr_name}={attr_value}")
        except Exception as e:
            logger.error(f"获取属性失败: {e}")
            raise e

    @allure.step("获取当前URL")
    def 获取当前URL(self, **kwargs):
        url = self.page.url
        g_context().set_dict(kwargs.get("变量名", "current_url"), url)
        logger.info(f"当前 URL: {url}")

    @allure.step("获取页面标题")
    def 获取页面标题(self, **kwargs):
        title = self.page.title()
        g_context().set_dict(kwargs.get("变量名", "page_title"), title)
        logger.info(f"页面标题: {title}")

    @allure.step("页面刷新")
    def 页面刷新(self, **kwargs):
        self.page.reload()
        self.get_screenshot()

    @allure.step("页面前进")
    def 页面前进(self, **kwargs):
        self.page.go_forward()

    @allure.step("页面后退")
    def 页面后退(self, **kwargs):
        self.page.go_back()
        self.get_screenshot()

    # ───────────────── 断言方法 ─────────────────
    def _do_assert(self, comparators, **kwargs):
        """通用断言逻辑。"""
        self.show_log("断言数据", kwargs)
        compare_type = kwargs.get("断言类型", "文本")
        operatros = kwargs.get("比较符", "==")
        message = kwargs.get("错误信息", None)

        if operatros not in comparators:
            raise Exception(f"不支持的比较符: {operatros}")

        expected = kwargs.get("预期结果", "")
        actual = kwargs.get("实际结果", "")
        if compare_type == "数字":
            expected = float(expected)

        if not comparators[operatros](expected, actual):
            self.get_screenshot()
            if message:
                raise AssertionError(message)
            else:
                raise AssertionError(f"断言失败: 实际值 '{actual}' {operatros} 预期值 '{expected}'")

    @allure.step("断言文本")
    def 断言文本(self, **kwargs):
        comparators = {
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "in": lambda a, b: a in str(b),
            "not in": lambda a, b: a not in str(b),
        }
        self._do_assert(comparators, **kwargs)

    def 断言文本相等(self, **kwargs):
        kwargs.update({"比较符": "=="})
        self.断言文本(**kwargs)

    def 断言文本包含(self, **kwargs):
        kwargs.update({"比较符": "in"})
        self.断言文本(**kwargs)

    def 断言文本不相等(self, **kwargs):
        kwargs.update({"比较符": "!="})
        self.断言文本(**kwargs)

    def 断言数字相等(self, **kwargs):
        kwargs.update({"比较符": "==", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字不相等(self, **kwargs):
        kwargs.update({"比较符": "!=", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字大于(self, **kwargs):
        kwargs.update({"比较符": ">", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字小于(self, **kwargs):
        kwargs.update({"比较符": "<", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字大于等于(self, **kwargs):
        kwargs.update({"比较符": ">=", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字小于等于(self, **kwargs):
        kwargs.update({"比较符": "<=", "断言类型": "数字"})
        self.断言文本(**kwargs)

    @allure.step("断言浏览器路径")
    def 断言浏览器路径(self, **kwargs):
        expected_url = str(kwargs.get("数据内容", ""))
        actual_url = self.page.url
        self.get_screenshot()
        if expected_url not in actual_url:
            raise AssertionError(f"URL断言失败! 期望包含: {expected_url}, 实际: {actual_url}")

    @allure.step("断言元素存在")
    def 断言元素存在(self, **kwargs):
        try:
            selector = self._get_selector_with_index(**kwargs)
            self.page.wait_for_selector(selector, state="visible", timeout=int(kwargs.get("超时", 5000)))
            self.get_screenshot()
        except Exception:
            self.get_screenshot()
            raise AssertionError(f"元素不存在或不可见: {kwargs.get('_页面元素', '')}")

    @allure.step("断言元素不存在")
    def 断言元素不存在(self, **kwargs):
        try:
            selector = self._get_selector_with_index(**kwargs)
            self.page.wait_for_selector(selector, state="hidden", timeout=int(kwargs.get("超时", 5000)))
            self.get_screenshot()
        except Exception:
            self.get_screenshot()
            raise AssertionError(f"元素仍然存在: {kwargs.get('_页面元素', '')}")

    @allure.step("断言页面标题")
    def 断言页面标题(self, **kwargs):
        expected = str(kwargs.get("预期结果", ""))
        actual = self.page.title()
        if expected not in actual:
            raise AssertionError(f"标题断言失败! 期望包含: {expected}, 实际: {actual}")

    # ───────────────── 数据库操作 ─────────────────
    def 提取数据MYSQL(self, **kwargs):
        db_config = g_context().get_dict("_数据库")[kwargs["_数据库"]]
        config = {"cursorclass": cursors.DictCursor}
        config.update(db_config)
        con = pymysql.connect(**config)
        cursor = con.cursor()
        sql = kwargs["SQL"]
        cursor.execute(sql)
        rs = cursor.fetchall()
        cursor.close()
        con.close()

        var_names = kwargs.get("变量名", [])
        result = {}
        if not var_names:
            for i, item in enumerate(rs, start=1):
                for key, value in item.items():
                    result[f"{key}_{i}"] = value
        else:
            field_length = len(rs[0]) if rs else 0
            if len(var_names) != field_length:
                raise Exception("变量名数量和数据库字段数量不一致")
            for idx, item in enumerate(rs, start=1):
                for col_idx, key in enumerate(item):
                    result[f"{var_names[col_idx]}_{idx}"] = item[key]
        g_context().set_by_dict(result)
        logger.info(f"数据库查询结果: {result}")

    # ───────────────── 坐标点击/输入 ─────────────────
    def click_location(self, **kwargs):
        coordinate = kwargs.get("坐标", "0,0")
        x = float(coordinate.split(",")[0].strip())
        y = float(coordinate.split(",")[1].strip())
        self.page.mouse.click(x, y)
        self.get_screenshot()

    def input_location(self, **kwargs):
        self.click_location(**kwargs)
        text = kwargs.get("文本", "")
        self.page.keyboard.type(text, delay=30)
        self.get_screenshot()

    # ───────────────── iframe 操作 ─────────────────
    def _get_frame_selector(self, **kwargs):
        all_ele_data = g_context().get_dict("_WEB页面元素") or {}
        key = str(kwargs.get("_页面元素", ""))
        if key not in all_ele_data:
            raise Exception(f"未找到 iframe 元素定义: '{key}'")
        ele_data = all_ele_data[key]
        loc_type = ele_data.get("定位方式", "xpath").lower()
        target = ele_data.get("目标对象", "")
        return f"{loc_type}={target}" if loc_type == "xpath" else f"xpath={target}"

    @allure.step("切换到iframe")
    def iframe_switch_to(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        frame = self.page.frame_locator(selector)
        g_context().set_dict("_current_frame", frame)
        logger.info(f"已切换到 iframe: {kwargs.get('_页面元素', '')}")

    @allure.step("退出到最外层")
    def iframe_to_default_content(self, **kwargs):
        g_context().set_dict("_current_frame", None)
        logger.info("已退出到最外层")

    # ───────────────── 窗口/标签页操作 ─────────────────
    @allure.step("切换最新窗口")
    def switch_to_latest_handle(self, **kwargs):
        pages = self.context.pages
        if len(pages) > 1:
            self.page = pages[-1]
            self.keywords = Keywords(self.page, self.context, self.browser)
            logger.info(f"已切换到最新窗口: {self.page.url}")
        self.get_screenshot()

    @allure.step("切换指定窗口")
    def switch_to_appoint_handle(self, **kwargs):
        pages = self.context.pages
        index = int(kwargs.get("数据内容", 0))
        if index < len(pages):
            self.page = pages[index]
            logger.info(f"已切换到窗口 {index}: {self.page.url}")
        self.get_screenshot()

    @allure.step("关闭当前页面")
    def 关闭当前页面(self, **kwargs):
        self.page.close()
        pages = self.context.pages
        if pages:
            self.page = pages[-1]

    # ───────────────── 下拉框/复选框/单选框 ─────────────────
    @allure.step("选择下拉框选项")
    def 选择下拉框选项(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        option_text = str(kwargs.get("数据内容", ""))
        self.page.wait_for_selector(selector, state="visible")
        self.page.select_option(selector, label=option_text)
        self.get_screenshot()

    @allure.step("选择下拉框选项(按值)")
    def 选择下拉框选项按值(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        value = str(kwargs.get("数据内容", ""))
        self.page.wait_for_selector(selector, state="visible")
        self.page.select_option(selector, value=value)
        self.get_screenshot()

    @allure.step("勾选复选框")
    def 勾选复选框(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        self.page.wait_for_selector(selector, state="visible")
        self.page.check(selector)
        self.get_screenshot()

    @allure.step("取消勾选")
    def 取消勾选(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        self.page.uncheck(selector)
        self.get_screenshot()

    # ───────────────── 弹窗/对话框处理 ─────────────────
    @allure.step("接受弹窗")
    def 接受弹窗(self, **kwargs):
        def handle_dialog(dialog):
            dialog.accept()

        self.page.on("dialog", handle_dialog)
        logger.info("已设置弹窗自动接受")

    @allure.step("取消弹窗")
    def 取消弹窗(self, **kwargs):
        def handle_dialog(dialog):
            dialog.dismiss()

        self.page.on("dialog", handle_dialog)

    @allure.step("获取弹窗文本")
    def 获取弹窗文本(self, **kwargs):
        dialog_msg = []

        def handle_dialog(dialog):
            dialog_msg.append(dialog.message)
            dialog.accept()

        self.page.on("dialog", handle_dialog)
        g_context().set_dict(kwargs.get("变量名", "dialog_msg"), dialog_msg)

    # ───────────────── 文件上传 ─────────────────
    @allure.step("上传文件")
    def 上传文件(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        file_path = str(kwargs.get("文件路径", ""))
        self.page.set_input_files(selector, file_path)
        self.get_screenshot()

    # ───────────────── 鼠标悬停 ─────────────────
    @allure.step("鼠标悬停")
    def 鼠标悬停(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        self.page.wait_for_selector(selector, state="visible")
        self.page.hover(selector)
        self.get_screenshot()

    @allure.step("双击元素")
    def 双击元素(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        self.page.wait_for_selector(selector, state="visible")
        self.page.dblclick(selector)
        self.get_screenshot()

    @allure.step("右键点击")
    def 右键点击(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        self.page.wait_for_selector(selector, state="visible")
        self.page.click(selector, button="right")
        self.get_screenshot()

    # ───────────────── 键盘操作 ─────────────────
    @allure.step("键盘按键")
    def 键盘按键(self, **kwargs):
        key = str(kwargs.get("数据内容", "Enter"))
        self.page.keyboard.press(key)
        self.get_screenshot()

    @allure.step("拖拽元素")
    def 拖拽元素(self, **kwargs):
        source_sel = self._build_selector(_页面元素=kwargs.get("源元素", ""))
        target_sel = self._build_selector(_页面元素=kwargs.get("目标元素", ""))
        self.page.drag_and_drop(source_sel, target_sel)
        self.get_screenshot()

    # ───────────────── 滚动操作 ─────────────────
    @allure.step("滚动到元素")
    def 滚动到元素(self, **kwargs):
        selector = self._get_selector_with_index(**kwargs)
        self.page.locator(selector).scroll_into_view_if_needed()
        self.get_screenshot()

    @allure.step("滚动页面")
    def 滚动页面(self, **kwargs):
        x = int(kwargs.get("X", 0))
        y = int(kwargs.get("Y", 0))
        self.page.evaluate(f"window.scrollBy({x}, {y})")
        self.get_screenshot()

    # ───────────────── JS执行 ─────────────────
    @allure.step("执行JS")
    def 执行JS(self, **kwargs):
        script = str(kwargs.get("数据内容", ""))
        result = self.page.evaluate(script)
        var_name = kwargs.get("变量名", None)
        if var_name:
            g_context().set_dict(var_name, result)
        return result

    # ───────────────── 验证码识别 ─────────────────
    def image_recognition(self, **kwargs):
        """图片数字验证码识别，使用 ddddocr。"""
        print("---开始图片识别---")
        ocr = DdddOcr()
        selector = self._get_selector_with_index(**kwargs)
        self.page.wait_for_selector(selector, state="visible")
        file_name = "img.png"
        self.page.locator(selector).screenshot(path=file_name)
        with open(file_name, "rb") as code:
            v_img = code.read()
            result = ocr.classification(v_img)
            print(f"识别结果: {result}")
        var_names = kwargs.get("引用变量", "captcha_code")
        g_context().set_by_dict({var_names: result})

    # ───────────────── 存储变量 ─────────────────
    def store_text(self, **kwargs):
        g_context().set_dict(kwargs.get("变量名", "store_var"), kwargs.get("变量值", ""))

    def random_six_digit_number(self, **kwargs):
        random_val = random.randint(100000, 999999)
        g_context().set_dict(kwargs.get("变量名", "random_6"), random_val)
        logger.info(f"生成随机6位数: {random_val}")

    # ───────────────── AI 操作 ─────────────────
    def AI操作(self, **kwargs):
        from openai import OpenAI

        ai_client = OpenAI(
            api_key=g_context().get_dict("HAT_LLM_API_KEY"),
            base_url=g_context().get_dict("HAT_LLM_BASE_URL"),
        )
        actions = ["点击", "输入", "文本提取"]
        prompt = """## 目标\n- 识别屏幕截图和文本中与用户描述最匹配的一个元素。\n\n## 输出格式\n```json\n{{\n  "bbox": [xmin,ymin,xmax,ymax],\n  "action": "用户的操作类型（{actions}）",\n  "text": "提取的文本内容",\n  "errors"?: "如果你无法找到，就把你的原因写在这里"\n}}\n```\n只能是一个json对象，不能是数组列表\n\n## 工作流程\n1. 接受用户描述的文字以及提供的截图。\n2. 分析用户的文字内容，提取其中关于元素的描述信息。\n3. 返回元素在截图中的 bbox 具体位置信息。\n\n## 用户描述\n{user_text}\n"""
        ai_prompt = prompt.format(user_text=kwargs.get("操作描述", ""), actions=", ".join(actions))

        # 截图
        img_bytes = self.page.screenshot(full_page=False)
        image_base64 = base64.b64encode(img_bytes).decode("ascii")

        # 保存到临时文件获取尺寸
        image_path = os.path.join(os.path.dirname(__file__), f"{str(uuid.uuid4()).replace('-', '')}.png")
        with open(image_path, "wb") as f:
            f.write(img_bytes)

        from PIL import Image
        width, height = Image.open(image_path).size
        logger.debug(f"截图尺寸：{width}, {height}")

        min_pixels = 512 * 28 * 28
        max_pixels = 2048 * 28 * 28
        from qwen_vl_utils import smart_resize
        input_height, input_width = smart_resize(height, width, factor=1.0, min_pixels=min_pixels, max_pixels=max_pixels)
        os.remove(image_path)

        completion = ai_client.chat.completions.create(
            model=g_context().get_dict("HAT_LLM_MODEL_NAME"),
            messages=[{"role": "user", "content": [
                {"type": "image_url", "min_pixels": min_pixels, "max_pixels": max_pixels,
                 "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                {"type": "text", "text": ai_prompt}
            ]}]
        )

        ai_response = json.loads(completion.model_dump_json())["choices"][0]["message"]["content"]
        pattern = r"```json\n(.*?)```"
        match = re.search(pattern, ai_response, re.DOTALL)
        json_content = match.group(1)
        result = json.loads(json_content)
        logger.debug(f"AI 返回: {result}")

        bbox = result["bbox"]
        result["bbox"] = [
            bbox[0] / input_width * width, bbox[1] / input_height * height,
            bbox[2] / input_width * width, bbox[3] / input_height * height,
        ]

        if result.get("action") == "点击":
            x = (result["bbox"][0] + result["bbox"][2]) / 2
            y = (result["bbox"][1] + result["bbox"][3]) / 2
            self.click_location(坐标=f"{x},{y}")
        elif result.get("action") == "输入":
            x = (result["bbox"][0] + result["bbox"][2]) / 2
            y = (result["bbox"][1] + result["bbox"][3]) / 2
            self.input_location(坐标=f"{x},{y}", 文本=result.get("text", ""))
        elif result.get("action") == "文本提取":
            self.store_text(变量名="ai_value", 变量值=result.get("text", ""))
        else:
            raise Exception(f"不支持的 AI 操作: {result.get('action')}")
        self.get_screenshot()

    def AI断言(self, **kwargs):
        from openai import OpenAI

        ai_client = OpenAI(
            api_key=g_context().get_dict("HAT_LLM_API_KEY"),
            base_url=g_context().get_dict("HAT_LLM_BASE_URL"),
        )
        prompt = """## 目标\n- 分析用户给出的一个对于图片内容的判断，并返回你的判断结果。\n\n## 输出格式示例：\n```json\n{{\n  "result": "true",\n  "msg": "你的判断依据"\n}}\n```\n只能是一个json对象，不能是数组列表\n\n## 工作流程\n1. 接受用户描述的文字以及提供的截图。\n\n## 用户描述\n{user_text}\n"""
        ai_prompt = prompt.format(user_text=kwargs.get("操作描述", ""))

        img_bytes = self.page.screenshot(full_page=False)
        image_base64 = base64.b64encode(img_bytes).decode("ascii")

        image_path = os.path.join(os.path.dirname(__file__), f"{str(uuid.uuid4()).replace('-', '')}.png")
        with open(image_path, "wb") as f:
            f.write(img_bytes)

        from PIL import Image
        width, height = Image.open(image_path).size
        min_pixels = 512 * 28 * 28
        max_pixels = 2048 * 28 * 28
        from qwen_vl_utils import smart_resize
        input_height, input_width = smart_resize(height, width, factor=1.0, min_pixels=min_pixels, max_pixels=max_pixels)
        os.remove(image_path)

        completion = ai_client.chat.completions.create(
            model=g_context().get_dict("HAT_LLM_MODEL_NAME"),
            messages=[{"role": "user", "content": [
                {"type": "image_url", "min_pixels": min_pixels, "max_pixels": max_pixels,
                 "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                {"type": "text", "text": ai_prompt}
            ]}]
        )
        ai_response = json.loads(completion.model_dump_json())["choices"][0]["message"]["content"]
        pattern = r"```json\n(.*?)```"
        match = re.search(pattern, ai_response, re.DOTALL)
        json_content = match.group(1)
        result = json.loads(json_content)
        logger.debug(f"AI断言结果: {result}")
        assert str(result.get("result", "")).lower() == "true", result.get("msg", "AI断言失败")

    # ───────────────── 自定义关键字扩展 ─────────────────
    def ex_invoke(self, **kwargs):
        key = kwargs.get("key", "")
        step_value = kwargs.get("step_value", {})
        if g_context().get_dict("key_dir") is not None:
            sys.path.append(g_context().get_dict("key_dir"))
            module = __import__(key)
            class_ = getattr(module, key)
            key_func = class_(self.page, self.context, self.browser).__getattribute__(key)
            key_func(**step_value)
