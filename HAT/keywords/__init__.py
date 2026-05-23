"""
Built-in keyword methods — the "actors" that perform browser interactions.

Each method maps to an 操作类型 value in Excel/YAML cases.
All methods receive **kwargs from step parameters.

Playwright semantic locator chain (auto-wait, no manual wait_for_selector):
  _locator() → Locator object → locator.click() / fill() / expect(locator).to_be_visible()
"""

import base64
import os
import random
import sys
import time

import allure
import pymysql
from ddddocr import DdddOcr
from loguru import logger
from playwright.sync_api import expect
from pymysql import cursors

from HAT.ai import AIMixin
from HAT.core.config import cfg
from HAT.utils.step_logger import _current_step_name


class Keywords(AIMixin):
    """All browser-interaction methods for keyword-driven testing."""

    def __init__(self, page, context, browser):
        self.page = page
        self.context = context
        self.browser = browser
        self._screenshots = []

    # ── locator helper ─────────────────────────────────────────

    def _locator(self, **kwargs):
        """Return the Playwright Locator for the element named in kwargs.

        Priority chain: semantic _locators (YAML-built) → legacy _elements (context.xlsx).
        Semantic locators use Playwright's built-in auto-wait; legacy uses CSS/XPath strings.
        """
        key = str(kwargs.get("_页面元素", ""))
        loc_map = cfg.get("_locators") or {}
        if key in loc_map:
            loc = loc_map[key]
            idx = int(kwargs.get("INDEX", 0))
            return loc.nth(idx) if idx > 0 else loc
        # Legacy fallback
        selector = self._legacy_selector(key, **kwargs)
        return self.page.locator(selector)

    def _legacy_selector(self, key: str, **kwargs) -> str:
        """Build a CSS/XPath selector string from old-style _elements config."""
        elements = cfg.get("_elements") or {}
        if key not in elements:
            raise KeyError(f"Element '{key}' not found in _locators or _elements")
        meta = elements[key]
        loc_type = str(meta.get("定位方式", "text")).lower()
        target = meta.get("目标对象", "")
        mapping = {
            "text": f"text={target}",
            "placeholder": f"[placeholder='{target}']",
            "testid": f"[data-testid='{target}']",
            "id": f"#{target}",
            "name": f'[name="{target}"]',
            "class": f".{target}",
            "css": target,
            "css selector": target,
            "xpath": f"xpath={target}",
            "role": target,
            "tag": target,
        }
        return mapping.get(loc_type, f"text={target}")

    # ── screenshot ─────────────────────────────────────────────

    def screenshot(self):
        """Capture current page screenshot and attach to Allure."""
        try:
            img = self.page.screenshot(full_page=False)
            b64 = base64.b64encode(img).decode("ascii")
            self._screenshots.append({
                "image": f"data:image/png;base64,{b64}",
                "caption": _current_step_name.get() or "",
            })
            allure.attach(img, "Screenshot", allure.attachment_type.PNG)
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")

    # ══════════════════════════════════════════════════════════
    #  Page navigation
    # ══════════════════════════════════════════════════════════

    @allure.step("Navigate")
    def 访问网址(self, **kwargs):
        self.page.goto(
            kwargs.get("网址", ""),
            timeout=int(kwargs.get("超时", 30000)),
            wait_until=kwargs.get("等待方式", "domcontentloaded"),
        )
        self.screenshot()

    @allure.step("Reload")
    def 页面刷新(self, **kwargs):
        self.page.reload()
        self.screenshot()

    @allure.step("Go Forward")
    def 页面前进(self, **kwargs):
        self.page.go_forward()

    @allure.step("Go Back")
    def 页面后退(self, **kwargs):
        self.page.go_back()
        self.screenshot()

    # ══════════════════════════════════════════════════════════
    #  Element interaction
    # ══════════════════════════════════════════════════════════

    def _should_fallback(self) -> bool:
        return os.getenv("HAT_AI_FALLBACK", "true").lower() == "true"

    @allure.step("Click")
    def 点击元素(self, **kwargs):
        try:
            loc = self._locator(**kwargs)
            expect(loc).to_be_visible(timeout=int(kwargs.get("超时", 10000)))
            loc.click()
        except Exception as e:
            if not self._should_fallback():
                raise
            desc = kwargs.get("_页面元素", "")
            logger.warning(f"Traditional click '{desc}' failed: {e} → falling back to AI")
            allure.attach(
                f"Traditional locator failed for '{desc}', falling back to AI visual positioning",
                "AI Fallback", allure.attachment_type.TEXT)
            self.AI操作(操作描述=f"点击{desc}" if desc else kwargs.get("操作描述", "点击目标元素"))
        self.screenshot()

    @allure.step("Fill")
    def 输入内容(self, **kwargs):
        try:
            loc = self._locator(**kwargs)
            content = str(kwargs.get("数据内容", ""))
            timeout = int(kwargs.get("超时", 10000))
            expect(loc).to_be_visible(timeout=timeout)
            if kwargs.get("先清除", True):
                loc.clear()
            loc.fill(content)
        except Exception as e:
            if not self._should_fallback():
                raise
            desc = kwargs.get("_页面元素", "")
            logger.warning(f"Traditional fill '{desc}' failed: {e} → falling back to AI")
            allure.attach(
                f"Traditional locator failed for '{desc}', falling back to AI visual input",
                "AI Fallback", allure.attachment_type.TEXT)
            self.AI操作(操作描述=f"在{desc}输入{kwargs.get('数据内容', '')}"
                       if desc else f"输入{kwargs.get('数据内容', '')}")
        self.screenshot()

    @allure.step("Type (append)")
    def 输入内容追加(self, **kwargs):
        loc = self._locator(**kwargs)
        content = str(kwargs.get("数据内容", ""))
        expect(loc).to_be_visible(timeout=int(kwargs.get("超时", 10000)))
        loc.press_sequentially(content, delay=50)
        self.screenshot()

    @allure.step("Clear")
    def 清空输入框(self, **kwargs):
        self._locator(**kwargs).clear()
        self.screenshot()

    @allure.step("Hover")
    def 鼠标悬停(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible()
        loc.hover()
        self.screenshot()

    @allure.step("Double Click")
    def 双击元素(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible()
        loc.dblclick()
        self.screenshot()

    @allure.step("Right Click")
    def 右键点击(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible()
        loc.click(button="right")
        self.screenshot()

    @allure.step("Scroll to Element")
    def 滚动到元素(self, **kwargs):
        self._locator(**kwargs).scroll_into_view_if_needed()
        self.screenshot()

    # ══════════════════════════════════════════════════════════
    #  Form controls
    # ══════════════════════════════════════════════════════════

    @allure.step("Select Option (label)")
    def 选择下拉框选项(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible()
        loc.select_option(label=str(kwargs.get("数据内容", "")))
        self.screenshot()

    @allure.step("Select Option (value)")
    def 选择下拉框选项按值(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible()
        loc.select_option(value=str(kwargs.get("数据内容", "")))
        self.screenshot()

    @allure.step("Check Checkbox")
    def 勾选复选框(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible()
        loc.check()
        self.screenshot()

    @allure.step("Uncheck Checkbox")
    def 取消勾选(self, **kwargs):
        self._locator(**kwargs).uncheck()
        self.screenshot()

    @allure.step("Upload File")
    def 上传文件(self, **kwargs):
        self._locator(**kwargs).set_input_files(str(kwargs.get("文件路径", "")))
        self.screenshot()

    # ══════════════════════════════════════════════════════════
    #  Retrieval
    # ══════════════════════════════════════════════════════════

    @allure.step("Get Text")
    def 获取元素文本(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible(timeout=10000)
        text = loc.text_content()
        cfg.set(kwargs.get("变量名", "temp_var"), text)
        logger.info(f"Text: {text}")

    @allure.step("Get Attribute")
    def 获取元素属性(self, **kwargs):
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible(timeout=10000)
        val = loc.get_attribute(kwargs.get("属性名", "value"))
        cfg.set(kwargs.get("变量名", "temp_var"), val)
        logger.info(f"Attribute: {val}")

    @allure.step("Get Current URL")
    def 获取当前URL(self, **kwargs):
        cfg.set(kwargs.get("变量名", "current_url"), self.page.url)

    @allure.step("Get Page Title")
    def 获取页面标题(self, **kwargs):
        cfg.set(kwargs.get("变量名", "page_title"), self.page.title())

    # ══════════════════════════════════════════════════════════
    #  Assertions
    # ══════════════════════════════════════════════════════════

    def _assert(self, comparators: dict, **kwargs):
        op = kwargs.get("比较符", "==")
        if op not in comparators:
            raise ValueError(f"Unknown comparator: {op}")
        expected = kwargs.get("预期结果", "")
        actual = kwargs.get("实际结果", "")
        if kwargs.get("断言类型") == "数字":
            expected = float(expected)
        if not comparators[op](expected, actual):
            self.screenshot()
            msg = kwargs.get("错误信息") or f"Assertion failed: {actual} {op} {expected}"
            raise AssertionError(msg)

    @allure.step("Assert Text")
    def 断言文本(self, **kwargs):
        self._assert({
            "==": lambda a, b: a == b, "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
            "<": lambda a, b: a < b, "<=": lambda a, b: a <= b,
            "in": lambda a, b: a in str(b),
            "not in": lambda a, b: a not in str(b),
        }, **kwargs)

    def 断言文本相等(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": "=="})

    def 断言文本包含(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": "in"})

    def 断言文本不相等(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": "!="})

    def 断言数字相等(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": "==", "断言类型": "数字"})

    def 断言数字不相等(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": "!=", "断言类型": "数字"})

    def 断言数字大于(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": ">", "断言类型": "数字"})

    def 断言数字小于(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": "<", "断言类型": "数字"})

    def 断言数字大于等于(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": ">=", "断言类型": "数字"})

    def 断言数字小于等于(self, **kwargs):
        self.断言文本(**{**kwargs, "比较符": "<=", "断言类型": "数字"})

    @allure.step("Assert URL Contains")
    def 断言浏览器路径(self, **kwargs):
        expected = str(kwargs.get("数据内容", ""))
        actual = self.page.url
        self.screenshot()
        if expected not in actual:
            raise AssertionError(f"URL mismatch: expected '{expected}' not in '{actual}'")

    @allure.step("Assert Element Visible")
    def 断言元素存在(self, **kwargs):
        try:
            loc = self._locator(**kwargs)
            expect(loc).to_be_visible(timeout=int(kwargs.get("超时", 5000)))
            self.screenshot()
        except Exception:
            self.screenshot()
            raise AssertionError(f"Element not visible: {kwargs.get('_页面元素', '')}")

    @allure.step("Assert Element Hidden")
    def 断言元素不存在(self, **kwargs):
        try:
            loc = self._locator(**kwargs)
            expect(loc).to_be_hidden(timeout=int(kwargs.get("超时", 5000)))
            self.screenshot()
        except Exception:
            self.screenshot()
            raise AssertionError(f"Element still visible: {kwargs.get('_页面元素', '')}")

    @allure.step("Assert Page Title")
    def 断言页面标题(self, **kwargs):
        expected = str(kwargs.get("预期结果", ""))
        actual = self.page.title()
        if expected not in actual:
            raise AssertionError(f"Title mismatch: expected '{expected}' not in '{actual}'")

    # ══════════════════════════════════════════════════════════
    #  Window / tab / iframe
    # ══════════════════════════════════════════════════════════

    @allure.step("Switch to Iframe")
    def iframe_switch_to(self, **kwargs):
        frame = self._locator(**kwargs).content_frame
        cfg.set("_current_frame", frame)
        logger.info(f"Switched to iframe: {kwargs.get('_页面元素', '')}")

    @allure.step("Exit Iframe")
    def iframe_to_default_content(self, **kwargs):
        cfg.set("_current_frame", None)
        logger.info("Exited iframe")

    @allure.step("Switch to Latest Tab")
    def switch_to_latest_handle(self, **kwargs):
        pages = self.context.pages
        if len(pages) > 1:
            self.page = pages[-1]
        self.screenshot()

    @allure.step("Switch to Tab by Index")
    def switch_to_appoint_handle(self, **kwargs):
        pages = self.context.pages
        idx = int(kwargs.get("数据内容", 0))
        if idx < len(pages):
            self.page = pages[idx]
        self.screenshot()

    @allure.step("Close Current Tab")
    def 关闭当前页面(self, **kwargs):
        self.page.close()
        pages = self.context.pages
        if pages:
            self.page = pages[-1]

    # ══════════════════════════════════════════════════════════
    #  Misc
    # ══════════════════════════════════════════════════════════

    @allure.step("Sleep")
    def 强制等待(self, **kwargs):
        time.sleep(float(kwargs.get("数据内容", 1)))

    @allure.step("Maximize")
    def 窗口最大化(self, **kwargs):
        self.page.set_viewport_size({"width": 1920, "height": 1080})

    @allure.step("Close Browser")
    def 关闭浏览器(self, **kwargs):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()

    @allure.step("Keyboard Press")
    def 键盘按键(self, **kwargs):
        self.page.keyboard.press(str(kwargs.get("数据内容", "Enter")))
        self.screenshot()

    @allure.step("Drag Element")
    def 拖拽元素(self, **kwargs):
        src = self._locator(_页面元素=kwargs.get("源元素", ""))
        dst = self._locator(_页面元素=kwargs.get("目标元素", ""))
        src.drag_to(dst)
        self.screenshot()

    @allure.step("Scroll Page")
    def 滚动页面(self, **kwargs):
        x, y = int(kwargs.get("X", 0)), int(kwargs.get("Y", 0))
        self.page.evaluate(f"window.scrollBy({x}, {y})")
        self.screenshot()

    @allure.step("Execute JS")
    def 执行JS(self, **kwargs):
        result = self.page.evaluate(str(kwargs.get("数据内容", "")))
        name = kwargs.get("变量名")
        if name:
            cfg.set(name, result)
        return result

    @allure.step("Accept Dialog")
    def 接受弹窗(self, **kwargs):
        def handler(d): d.accept()
        self.page.on("dialog", handler)

    @allure.step("Dismiss Dialog")
    def 取消弹窗(self, **kwargs):
        def handler(d): d.dismiss()
        self.page.on("dialog", handler)

    @allure.step("Get Dialog Text")
    def 获取弹窗文本(self, **kwargs):
        msgs = []
        def handler(d):
            msgs.append(d.message)
            d.accept()
        self.page.on("dialog", handler)
        cfg.set(kwargs.get("变量名", "dialog_msg"), msgs)

    # ══════════════════════════════════════════════════════════
    #  Variables
    # ══════════════════════════════════════════════════════════

    @allure.step("Store Variable")
    def store_text(self, **kwargs):
        cfg.set(kwargs.get("变量名", "store_var"), kwargs.get("变量值", ""))

    @allure.step("Random 6-digit")
    def random_six_digit_number(self, **kwargs):
        val = random.randint(100000, 999999)
        cfg.set(kwargs.get("变量名", "random_6"), val)
        logger.info(f"Random 6-digit: {val}")

    # ══════════════════════════════════════════════════════════
    #  Database (MySQL)
    # ══════════════════════════════════════════════════════════

    def 提取数据MYSQL(self, **kwargs):
        db_alias = kwargs["_数据库"]
        db_cfg = cfg.get("_database", {})
        if db_alias not in db_cfg:
            raise KeyError(f"Database alias '{db_alias}' not found in context config. "
                           f"Available: {list(db_cfg)}")
        try:
            conn = pymysql.connect(cursorclass=cursors.DictCursor, **db_cfg[db_alias])
            cur = conn.cursor()
            cur.execute(kwargs["SQL"])
            rows = cur.fetchall()
        except Exception as e:
            raise RuntimeError(
                f"Database query failed [{db_alias}]: {e}\n"
                f"SQL: {kwargs.get('SQL', '')[:200]}"
            ) from e
        finally:
            try:
                cur.close()
                conn.close()
            except Exception:
                pass

        var_names = kwargs.get("变量名", [])
        result = {}
        if not var_names:
            for i, row in enumerate(rows, 1):
                for k, v in row.items():
                    result[f"{k}_{i}"] = v
        else:
            if rows and len(var_names) != len(rows[0]):
                raise ValueError("Variable count != column count")
            for idx, row in enumerate(rows, 1):
                for col_idx, key in enumerate(row):
                    result[f"{var_names[col_idx]}_{idx}"] = row[key]
        cfg.update(result)
        logger.info(f"DB result: {result}")

    # ══════════════════════════════════════════════════════════
    #  CAPTCHA recognition (ddddocr)
    # ══════════════════════════════════════════════════════════

    @allure.step("OCR Recognition")
    def image_recognition(self, **kwargs):
        logger.info("Starting OCR...")
        ocr = DdddOcr()
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible()
        path = "img.png"
        loc.screenshot(path=path)
        with open(path, "rb") as f:
            result = ocr.classification(f.read())
            logger.info(f"OCR result: {result}")
        cfg.set(kwargs.get("引用变量", "captcha_code"), result)

    # ══════════════════════════════════════════════════════════
    #  External custom keywords (ex_invoke)
    # ══════════════════════════════════════════════════════════

    @allure.step("Custom Keyword")
    def ex_invoke(self, **kwargs):
        key = kwargs.get("key", "")
        step_value = kwargs.get("step_value", {})
        key_dir = cfg.get("key_dir")
        if not key_dir:
            raise RuntimeError("key_dir not configured — cannot load custom keyword")
        sys.path.append(key_dir)
        mod = __import__(key)
        cls = getattr(mod, key)
        instance = cls(self.page, self.context, self.browser)
        getattr(instance, key)(**step_value)
