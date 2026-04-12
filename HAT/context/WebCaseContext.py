# -*- coding: utf-8 -*-
# @Author  : wyf
# @File    : WebCaseContext.py

import atexit

import allure
from allure_commons.types import AttachmentType
from selenium.webdriver import DesiredCapabilities

from HAT.core.globalContext import g_context
from selenium import webdriver

from HAT.keywords.web_keywords import Keywords
from selenium.webdriver.chrome.service import Service as Chrome_Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as Firefox_Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions, Options
from selenium.webdriver.ie.service import Service as Ie_Service
from selenium.webdriver.ie.options import Options as IeOptions

_global_driver_obj = None

# 复用浏览器也没有关闭
def cleanup_shared_driver():
    """
    安全的清理函数。
    
    在程序退出时自动调用，确保共享的浏览器驱动被正确关闭，防止残留进程。
    """
    global _global_driver_obj
    if _global_driver_obj is not None:
        try:
            # 方法1：温和关闭
            try:
                _global_driver_obj.quit()
            except:
                try:
                #方法2： close
                    _global_driver_obj.close()
                except:
                    #方法3：关闭进程
                    import os
                    import signal
                    if hasattr(_global_driver_obj, 'service') and _global_driver_obj.service.process:
                        try:
                            os.kill(_global_driver_obj.service.process.pid, signal.SIGTERM)
                        except:
                            pass
        except Exception as e:
            pass
        finally:
            _global_driver_obj = None
atexit.register(cleanup_shared_driver)

class WebCaseContext:
    """
    Web 用例上下文管理类。
    
    负责浏览器的初始化、关键字对象的创建以及资源的释放。
    它充当了“舞台监督”的角色，管理着测试环境的生命周期。
    """
    def __init__(self):
        self.driver = None
        self.keywords = None

    # 优化浏览器 让框架支持不同的浏览器运行
    def init_driver(self):
        """
        根据全局配置初始化 Selenium WebDriver。
        
        支持 Chrome, Firefox, IE 以及远程 Grid 模式。
        
        :return: 配置好的 WebDriver 实例
        """
        #映射表
        driver_class={
            "remote": {"driver": webdriver.Remote},#支持远程连接
            "chrome": {"driver": webdriver.Chrome,#谷歌浏览器
                       "service":Chrome_Service,#谷歌浏览器驱动
                       "options":ChromeOptions,#谷歌浏览器的配置
                       "capabilities":DesiredCapabilities.CHROME#浏览器自身版本 系统
                       },
            "firefox": {"driver": webdriver.Firefox,
                        "service": Firefox_Service,  # 谷歌浏览器驱动
                        "options": FirefoxOptions,  # 谷歌浏览器的配置
                        "capabilities": DesiredCapabilities.FIREFOX  # 浏览器自身版本 系统
                        },
            "ie": {"driver": webdriver.Ie,
                        "service": Ie_Service,  # 谷歌浏览器驱动
                        "options": IeOptions,  # 谷歌浏览器的配置
                        "capabilities": DesiredCapabilities.INTERNETEXPLORER  # 浏览器自身版本 系统
                        },
        }
        #用例 传过来 运行什么浏览器 在哪？
        _browser_config=g_context().get_dict("_浏览器")
        grid_url=_browser_config.get("grid_url",None)#grid_url有值就拿到，没值给个None
        options=_browser_config.get("options",None) #options配置
        capability=_browser_config.get("capability",None)#浏览器默认配置
        browser_name=capability.get("browserName", None)#浏览器名称
        capabilities=driver_class[browser_name.lower()]["capabilities"].copy()#不影响到原有配置

        #管理Service
        service=None
        driver_path=_browser_config.get("driver_path",None)#浏览器驱动位置
        if driver_path is not None:#不是空的  Chrome_Service(driver_path)
            service=driver_class[browser_name.lower()]['service'](driver_path)

        #capability 默认能力 浏览器的版本这些
        for key in capability.keys():
            capabilities.update({key: capability[key]})

        #添加options参数
        # browser_options=Options()
        browser_options=driver_class[browser_name.lower()]["options"]()
        if options is not None and len(options)>0:#如果options有值
            #ChromeOptions()
            # browser_options=driver_class[browser_name.lower()]['options']()
            args=options.get("args",[])
            for arg in args:
                browser_options.add_argument(arg)

        #如果有远程连接就用webdriver.Remote
        if grid_url is not None and len(grid_url)!=0: #有grid地址远程连接
            driver=webdriver.Remote(command_executor=_browser_config["grid_url"],
                             options=browser_options)
        else:  #没有远程连接，正常连接
            # 实例浏览器  webdriver.Chrome(service=service,options=browser_options)
            driver=driver_class[browser_name.lower()]['driver'](
                service=service,
                options=browser_options
            )
        return  driver



    # 浏览器复用还是不复用
    def init_keywords(self):
        """
        初始化关键字对象。
        
        根据配置决定是否复用浏览器会话。如果复用，则使用全局唯一的驱动对象；
        否则每次都会创建一个新的浏览器实例。
        
        :return: Keywords 实例
        """
        session_reuse=g_context().get_dict("session_reuse")
        if session_reuse is not None and session_reuse==True:#浏览器复用 保持在一个浏览器中只能实例一次浏览器
            global _global_driver_obj #定义一个全局变量
            if _global_driver_obj is None: #如果全局变量为空
                # _global_driver_obj = webdriver.Chrome() #实例一个浏览器
                _global_driver_obj = self.init_driver()
            self.driver=_global_driver_obj #把全局变量赋给self.driver
        else: #不复用  每次都要实例一个浏览器
            # self.driver = webdriver.Chrome()
            self.driver = self.init_driver()
        self.keywords = Keywords(self.driver)
        return self.keywords

    # 有些同学的浏览器不会关闭
    def release(self):
        """
        释放资源。
        
        包括生成 Allure 报告中的视频回放效果，以及在不复用模式下关闭浏览器。
        """
        try:
            self.add_video_like_slideshow(self.keywords.screen_shots)
            #不复用  浏览器没有自动关闭 就调这个方法
            session_reuse=g_context().get_dict("session_reuse")
            # 判断是否复用 不复用
            if (session_reuse is  None or session_reuse==False) and  self.driver is not None:
                self.driver.quit()
        except Exception as e:
            print(e)

    def add_video_like_slideshow(self, base64_images, title="录屏回放"):
        """
        添加视频效果的图片轮播到Allure报告

        :param allure: allure模块
        :param base64_images: base64图片
        :param title: 在报告中显示的标题
        """

        # HTML内容
        html_content = f"""
               <div class="video-like-slideshow" style="max-width: 800px; margin: 20px auto; position: relative; overflow: hidden; height: 550px; background: #000; border-radius: 8px;">
           <div id="slideshow-container" style="position: relative; height: calc(100% - 80px);">
               <!-- 图片会动态插入到这里 -->
           </div>
           <div id="caption-container" style="position: absolute; bottom: 40px; left: 0; right: 0; text-align: center; color: white; padding: 0 20px; z-index: 10;">
               <!-- 文字说明会动态插入到这里 -->
           </div>
           <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: rgba(255,255,255,0.2); z-index: 5;">
               <div id="progress-bar" style="height: 100%; width: 0%; background: #ff4757; transition: width 0.1s linear;"></div>
           </div>
       </div>

       <style>
           .slide {{
               position: absolute;
               top: 0;
               left: 0;
               width: 100%;
               height: 100%;
               object-fit: contain;
               opacity: 0;
               transition: opacity 1.2s ease;
               will-change: opacity;
               z-index: 1;
               background: #000;
           }}

           .slide.active {{
               opacity: 1;
               z-index: 2;
           }}

           .caption {{
               position: absolute;
               width: 100%;
               opacity: 0;
               transition: opacity 0.5s ease;
               font-size: 18px;
               text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
           }}

           .caption.active {{
               opacity: 1;
           }}
       </style>

       <script>
           // 图片和对应的文字说明数据
           const slidesData = {base64_images}

           const container = document.getElementById('slideshow-container');
           const captionContainer = document.getElementById('caption-container');
           const progressBar = document.getElementById('progress-bar');
           let currentIndex = 0;
           let slides = [];
           let captions = [];
           const intervalDuration = 3000; // 每张图片显示3秒
           let intervalId = null;
           let progressIntervalId = null;
           let totalDuration = slidesData.length * intervalDuration;
           let elapsedTime = 0;

           // 初始化轮播
           function initSlideshow() {{
               // 创建图片元素和文字说明
               slidesData.forEach((data, index) => {{
                   // 创建图片元素
                   const slide = document.createElement('img');
                   slide.className = 'slide';
                   slide.src = data.image;
                   container.appendChild(slide);
                   slides.push(slide);

                   // 创建文字说明元素
                   const caption = document.createElement('div');
                   caption.className = 'caption';
                   caption.textContent = data.caption;
                   captionContainer.appendChild(caption);
                   captions.push(caption);

                   // 激活第一张
                   if (index === 0) {{
                       slide.classList.add('active');
                       caption.classList.add('active');
                   }}
               }});

               startSlideshow();
               startTotalProgressBar();
           }}

           // 更新总进度条
           function startTotalProgressBar() {{
               clearInterval(progressIntervalId);
               progressBar.style.width = '0%';
               elapsedTime = 0;

               progressIntervalId = setInterval(() => {{
                   elapsedTime += 100;
                   const progress = (elapsedTime % totalDuration) / totalDuration * 100;
                   progressBar.style.width = `${{progress}}%`;
               }}, 100);
           }}

           // 切换到下一张
           function nextSlide() {{
               // 隐藏当前图片和文字
               slides[currentIndex].classList.remove('active');
               captions[currentIndex].classList.remove('active');

               // 计算下一张索引
               currentIndex = (currentIndex + 1) % slidesData.length;

               // 显示下一张图片和文字
               slides[currentIndex].classList.add('active');
               captions[currentIndex].classList.add('active');
           }}

           // 开始自动轮播
           function startSlideshow() {{
               if (!intervalId) {{
                   intervalId = setInterval(nextSlide, intervalDuration);
               }}
           }}

           // 页面加载完成后初始化
           window.addEventListener('DOMContentLoaded', initSlideshow);
       </script>
               """

        # 添加到Allure报告
        allure.attach(html_content, name=title, attachment_type=AttachmentType.HTML)

