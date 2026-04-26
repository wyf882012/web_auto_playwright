# -*- coding: utf-8 -*-
"""
WebCaseContext —— Playwright 浏览器上下文管理器
================================================

负责:
  1. Playwright 浏览器的初始化（chromium / firefox / webkit）
  2. 浏览器会话的复用管理（session_reuse 配置）
  3. Keywords 关键字对象的创建
  4. POM 页面对象的注册（支持"LoginPage.method"点分表示法调用）
  5. 资源的释放与截图回放生成

与 POM 的集成:
  init_keywords() 方法在创建 Keywords 实例后，
  自动调用 _init_page_objects() 实例化所有页面对象，
  并注册到 g_context 的 _POM_PAGES 字典中。
  TestRunner 通过该字典实现"LoginPage.login"这种点分表示法的解析。
"""
import atexit
import allure
from allure_commons.types import AttachmentType
from playwright.sync_api import sync_playwright

from HAT.core.globalContext import g_context
from HAT.keywords.web_keywords import Keywords

_global_browser = None
_global_playwright = None


def cleanup_shared_browser():
    """安全的清理函数 —— 程序退出时自动关闭共享浏览器。"""
    global _global_browser, _global_playwright
    try:
        if _global_browser is not None:
            _global_browser.close()
    except Exception:
        pass
    try:
        if _global_playwright is not None:
            _global_playwright.stop()
    except Exception:
        pass
    finally:
        _global_browser = None
        _global_playwright = None


atexit.register(cleanup_shared_browser)


class WebCaseContext:
    """
    Web 用例上下文管理类（Playwright 版）。

    负责浏览器的初始化、关键字对象的创建以及资源的释放。
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.keywords = None

    def init_browser(self):
        """
        根据全局配置初始化 Playwright 浏览器。

        支持 chromium / firefox / webkit 以及 headless 模式。
        """
        _browser_config = g_context().get_dict("_浏览器") or {}
        capability = _browser_config.get("capability", {})
        browser_name = capability.get("browserName", "chromium").lower()
        options = _browser_config.get("options", {})
        args = options.get("args", []) if options else []

        self.playwright = sync_playwright().start()

        # 选择浏览器类型
        browser_type_map = {
            "chrome": self.playwright.chromium,
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit,
            "edge": self.playwright.chromium,  # Edge 也是基于 chromium
        }
        browser_type = browser_type_map.get(browser_name, self.playwright.chromium)

        # 判断是否 headless
        headless = "headless" in args if args else False

        # 启动参数
        launch_args = []
        for arg in args:
            if arg != "headless":
                launch_args.append(arg)

        self.browser = browser_type.launch(
            headless=headless,
            args=launch_args if launch_args else None
        )

        # 创建浏览器上下文（相当于一个隔离的会话）
        viewport = {"width": 1920, "height": 1080}
        self.context = self.browser.new_context(
            viewport=viewport,
            locale="zh-CN"
        )
        self.page = self.context.new_page()
        return self.browser

    def init_keywords(self):
        """
        初始化关键字对象。

        根据配置决定是否复用浏览器会话。
        """
        session_reuse = g_context().get_dict("session_reuse")
        global _global_browser, _global_playwright

        if session_reuse is True:
            if _global_browser is None:
                self.playwright = sync_playwright().start()
                _global_playwright = self.playwright

                _browser_config = g_context().get_dict("_浏览器") or {}
                capability = _browser_config.get("capability", {})
                browser_name = capability.get("browserName", "chromium").lower()
                options = _browser_config.get("options", {})
                args = options.get("args", []) if options else []
                headless = "headless" in args if args else False

                browser_type_map = {
                    "chrome": self.playwright.chromium,
                    "chromium": self.playwright.chromium,
                    "firefox": self.playwright.firefox,
                    "webkit": self.playwright.webkit,
                    "edge": self.playwright.chromium,
                }
                browser_type = browser_type_map.get(browser_name, self.playwright.chromium)

                launch_args = [a for a in args if a != "headless"]
                _global_browser = browser_type.launch(
                    headless=headless,
                    args=launch_args if launch_args else None
                )

            self.browser = _global_browser
            self.playwright = _global_playwright
        else:
            self.init_browser()

        if self.context is None:
            viewport = {"width": 1920, "height": 1080}
            self.context = self.browser.new_context(viewport=viewport, locale="zh-CN")

        if self.page is None:
            self.page = self.context.new_page()

        self.keywords = Keywords(self.page, self.context, self.browser)

        # ── POM 页面对象注册 ──
        # 将所有页面对象实例化并存储到全局上下文，
        # 使 TestRunner 可以通过"LoginPage.method"点分表示法调用页面对象方法
        self._init_page_objects()

        return self.keywords

    def _init_page_objects(self):
        """
        初始化并注册所有 POM 页面对象。

        将页面对象存储在 g_context 的 _POM_PAGES 字典中，
        键为页面类名（如 "LoginPage"），值为页面对象实例。

        使用方式:
          在 YAML/Excel 用例中通过"LoginPage.login"调用页面对象方法，
          TestRunner 根据 "." 判断这是 POM 调用，从 _POM_PAGES 中查找对应实例。

        扩展方式:
          在此方法中新增页面对象的实例化和注册:
            from HAT.pages.home_page import HomePage
            pom_pages[HomePage.__name__] = HomePage(self.keywords)
        """
        from HAT.pages.login_page import LoginPage

        pom_pages = {}

        # 注册 LoginPage —— reelmate.cn 登录页面对象
        login_page = LoginPage(self.keywords)
        pom_pages[LoginPage.__name__] = login_page  # "LoginPage" -> LoginPage 实例

        # 未来扩展示例: 在此处注册更多页面对象
        # from HAT.pages.home_page import HomePage
        # home_page = HomePage(self.keywords)
        # pom_pages[HomePage.__name__] = home_page

        # 注册到全局上下文（供 TestRunner._invoke_pom_method 查找）
        g_context().set_dict("_POM_PAGES", pom_pages)

    def register_page(self, page_instance):
        """
        动态注册一个页面对象（供测试代码或自定义扩展使用）。

        :param page_instance: 页面对象实例（必须继承自 BasePage）
        :raises TypeError: 如果 page_instance 不是 BasePage 的子类
        """
        from HAT.pages.base_page import BasePage

        if not isinstance(page_instance, BasePage):
            raise TypeError(f"页面对象必须继承自 BasePage，得到: {type(page_instance)}")

        pom_pages = g_context().get_dict("_POM_PAGES") or {}
        class_name = page_instance.__class__.__name__
        pom_pages[class_name] = page_instance
        g_context().set_dict("_POM_PAGES", pom_pages)

    def release(self):
        """释放资源 —— 生成截图回放并关闭浏览器。"""
        try:
            self.add_video_like_slideshow(self.keywords.screen_shots)
            session_reuse = g_context().get_dict("session_reuse")
            if (session_reuse is None or session_reuse is False) and self.page is not None:
                if self.context:
                    self.context.close()
                if self.browser:
                    self.browser.close()
                if not session_reuse and self.playwright:
                    self.playwright.stop()
        except Exception as e:
            print(f"释放资源异常: {e}")

    def add_video_like_slideshow(self, base64_images, title="录屏回放"):
        """添加截图轮播到 Allure 报告（HTML 方式实现类似视频播放效果）。"""
        if not base64_images:
            return
        import json

        slides_json = json.dumps(base64_images, ensure_ascii=False)

        html_content = f"""
            <div class="video-like-slideshow" style="max-width: 800px; margin: 20px auto; position: relative; overflow: hidden; height: 550px; background: #000; border-radius: 8px;">
                <div id="slideshow-container" style="position: relative; height: calc(100% - 80px);"></div>
                <div id="caption-container" style="position: absolute; bottom: 40px; left: 0; right: 0; text-align: center; color: white; padding: 0 20px; z-index: 10;"></div>
                <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.2); z-index: 5;">
                    <div id="progress-bar" style="height: 100%; width: 0%; background: #ff4757; transition: width 0.1s linear;"></div>
                </div>
            </div>
            <style>
                .slide {{
                    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                    object-fit: contain; opacity: 0; transition: opacity 1.2s ease;
                    will-change: opacity; z-index: 1; background: #000;
                }}
                .slide.active {{ opacity: 1; z-index: 2; }}
                .caption {{
                    position: absolute; width: 100%; opacity: 0;
                    transition: opacity 0.5s ease; font-size: 18px;
                    text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
                }}
                .caption.active {{ opacity: 1; }}
            </style>
            <script>
                const slidesData = {slides_json};
                const container = document.getElementById('slideshow-container');
                const captionContainer = document.getElementById('caption-container');
                const progressBar = document.getElementById('progress-bar');
                let currentIndex = 0;
                let slides = [];
                let captions = [];
                let intervalId = null;
                let progressIntervalId = null;
                const intervalDuration = 3000;
                let elapsedTime = 0;

                function initSlideshow() {{
                    slidesData.forEach((data, index) => {{
                        const slide = document.createElement('img');
                        slide.className = 'slide';
                        slide.src = data.image;
                        container.appendChild(slide);
                        slides.push(slide);
                        const caption = document.createElement('div');
                        caption.className = 'caption';
                        caption.textContent = data.caption;
                        captionContainer.appendChild(caption);
                        captions.push(caption);
                        if (index === 0) {{
                            slide.classList.add('active');
                            caption.classList.add('active');
                        }}
                    }});
                    startSlideshow();
                    startTotalProgressBar();
                }}

                function startTotalProgressBar() {{
                    clearInterval(progressIntervalId);
                    progressBar.style.width = '0%';
                    elapsedTime = 0;
                    progressIntervalId = setInterval(() => {{
                        elapsedTime += 100;
                        const progress = (elapsedTime % (slidesData.length * intervalDuration)) / (slidesData.length * intervalDuration) * 100;
                        progressBar.style.width = progress + '%';
                    }}, 100);
                }}

                function nextSlide() {{
                    slides[currentIndex].classList.remove('active');
                    captions[currentIndex].classList.remove('active');
                    currentIndex = (currentIndex + 1) % slidesData.length;
                    slides[currentIndex].classList.add('active');
                    captions[currentIndex].classList.add('active');
                }}

                function startSlideshow() {{
                    if (!intervalId) intervalId = setInterval(nextSlide, intervalDuration);
                }}

                window.addEventListener('DOMContentLoaded', initSlideshow);
            </script>
        """
        allure.attach(html_content, name=title, attachment_type=AttachmentType.HTML)
