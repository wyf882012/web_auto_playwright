"""
Test runner — orchestrates a single test case execution.

Five-category dispatch (操作类型 resolution):
  1. AI atomic:    "AI:操作" → AI vision click/input/extract
  2. AI assertion: "AI:断言" → AI vision assertion
  3. AI composite: "AI:执行" → multi-turn AI agent
  4. POM:          "PageClass.method" → page-object method
  5. Traditional:  "点击元素", "断言文本包含", ... → Keywords methods
  *. Custom:       ex_invoke from user's key_dir

All categories resolved via HAT.operation_types.categorize().
"""

import ast

import allure
from loguru import logger
from tqdm import tqdm

from HAT.browser import BrowserManager
from HAT.config import cfg
from HAT.keywords import Keywords
from HAT.operation_types import categorize, OpCategory
from HAT.template import render
from HAT.utils.step_logger import allure_step_with_log


class TestRunner:
    """Executes a single caseinfo dict as a test case."""

    # POM page registry — populated by _init_pages()
    _pages: dict = {}

    @classmethod
    def register_page(cls, page_instance):
        """Register a POM page object for dot-notation dispatch."""
        cls._pages[page_instance.__class__.__name__] = page_instance

    @classmethod
    def _init_pages(cls, keywords):
        """Instantiate and register all POM pages."""
        cls._pages.clear()
        from HAT.pages.login import LoginPage
        from HAT.pages.video import VideoPage
        cls._pages["LoginPage"] = LoginPage(keywords)
        cls._pages["VideoPage"] = VideoPage(keywords)

    @classmethod
    def _invoke_ai(cls, key: str, params: dict, keywords):
        """Dispatch 'AI:操作' / 'AI:断言' to Keywords AI methods."""
        action = key[3:]  # Strip "AI:" prefix
        method = getattr(keywords, action, None)
        if method is None:
            raise AttributeError(f"Unknown AI action: '{action}'")
        method(**{k: v for k, v in params.items() if k != "操作类型"})

    @classmethod
    def _invoke_pom(cls, key: str, params: dict):
        """Resolve 'PageClass.method' and invoke it."""
        dot = key.index(".")
        cls_name, method = key[:dot], key[dot + 1:]
        page = cls._pages.get(cls_name)
        if page is None:
            raise KeyError(f"Page '{cls_name}' not registered. "
                           f"Available: {list(cls._pages)}")
        func = getattr(page, method)
        # Remove framework-internal keys from call params
        call = {k: v for k, v in params.items()
                if k not in ("操作类型", "_页面元素", "INDEX")}
        func(**call)

    def test_case(self, caseinfo: dict):
        """Execute one test case (pytest parametrized entry)."""
        browser = BrowserManager()
        try:
            # ── 1. Setup ──
            base = caseinfo.get("基础配置", {})
            case_title = base.get("用例标题", "untitled")
            cfg.set("_current_case", case_title)

            allure.dynamic.parameter("caseinfo", "")
            allure.dynamic.feature(base.get("一级模块", "Default Module"))
            allure.dynamic.story(base.get("二级模块", "Default Feature"))
            allure.dynamic.title(case_title)
            cid = base.get("用例编号")
            if cid:
                allure.dynamic.id(str(cid))

            # ── 2. Browser & keywords ──
            browser.start()
            keywords = Keywords(browser.page, browser.context, browser._browser)
            keywords._screenshots = browser._screenshots = []
            self._init_pages(keywords)

            # ── 3. Context + pre-scripts ──
            local = caseinfo.get("local_context", {})
            context = dict(cfg.all())
            context.update(local)

            pre = render(caseinfo.get("前置脚本"), context)
            if pre:
                from HAT.utils.script import exec_script
                for s in ast.literal_eval(pre):
                    exec_script(s, cfg.all())

            # ── 4. Execute steps ──
            steps = caseinfo.get("用例步骤", [])
            for step in tqdm(steps, desc=case_title):
                name = next(iter(step))
                params = next(iter(step.values()))
                tqdm.write(f"  [{name}] {params}")

                # Refresh context + render templates
                context = dict(cfg.all())
                context.update(local)
                params = ast.literal_eval(render(params, context))

                with allure_step_with_log(name):
                    self._dispatch(params, keywords)

            # ── 5. Post-scripts ──
            context = dict(cfg.all())
            context.update(local)
            post = render(caseinfo.get("后置脚本"), context)
            if post:
                from HAT.utils.script import exec_script
                for s in ast.literal_eval(post):
                    exec_script(s, cfg.all())

        except Exception:
            # Capture failure screenshot before browser closes
            if browser.page:
                try:
                    allure.attach(browser.page.screenshot(full_page=True),
                                  "Failure Screenshot", allure.attachment_type.PNG)
                    allure.attach(browser.page.url, "Failure URL",
                                  allure.attachment_type.TEXT)
                except Exception:
                    pass
            raise
        finally:
            browser._screenshots = getattr(keywords, "_screenshots", [])
            browser.stop()

    def _dispatch(self, params: dict, keywords: Keywords):
        """Category-driven dispatch via OpCategory registry."""
        key = params["操作类型"]
        call = {k: v for k, v in params.items() if k != "操作类型"}
        cat = categorize(key)

        if cat == OpCategory.AI_ATOMIC:
            keywords.AI操作(**call)
        elif cat == OpCategory.AI_ASSERTION:
            keywords.AI断言(**call)
        elif cat == OpCategory.AI_COMPOSITE:
            keywords.AI执行(**call)
        elif cat == OpCategory.POM:
            self._invoke_pom(key, params)
        elif cat in (OpCategory.ACTION, OpCategory.ASSERTION):
            getattr(keywords, key)(**params)
        else:  # CUSTOM
            if cfg.get("key_dir"):
                keywords.ex_invoke(key=key, step_value=params)
            else:
                raise AttributeError(
                    f"Unknown keyword: '{key}'. "
                    f"Check spelling or configure key_dir for custom keywords."
                ) from None
