# -*- coding: utf-8 -*-
# @Author  : wyf
# @File    : web_keywords.py

import sys
import time
from base64 import b64decode

import allure
import pymysql
from ddddocr import DdddOcr
from loguru import logger
from pymysql import cursors
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from HAT.core.globalContext import g_context


# 项目经常要做的操作封装这个类
# 考虑后期能复用 浏览器可能要打开不同的浏览器 访问网址 可能要用 找元素 输入用户名 找元素输入密码
# 封装可以封装很多 iframe 下拉框 窗口切换 上传文件。。。 没封装到可以后续补

class Keywords:
    """
    Web 自动化关键字类。
    
    该类封装了所有与浏览器交互的底层操作，如点击、输入、断言等。
    它是框架中的“演员”，负责执行具体的动作。
    """
    # 初始化方法 __init__只要实例化类Keywords,就回进入到这个方法 浏览器可以从外面传过来
    def __init__(self, driver):
        """
        初始化关键字对象。
        
        :param driver: Selenium WebDriver 实例
        """
        self.driver = driver
        self.screen_shots = []

    # 访问网址 不确定传多少值
    @allure.step("访问网址")
    def 访问网址(self, **kwargs):
        """导航到指定的 URL。"""
        self.driver.get(kwargs['网址'])

    # 找元素的时候用显示等待找
    # 封装显示等待
    def wait_for_element(self, locator):
        """
        使用显式等待查找页面元素。
        
        :param locator: 定位器元组 (By.ID, 'value')
        :return: 匹配的元素列表
        """
        try:
            ele = WebDriverWait(self.driver, 10).until(EC.visibility_of_all_elements_located(locator))
            return ele
        except Exception as e:
            print(f"元素定位失败: {locator}, 错误: {e}")
            return []

    @allure.step("找元素")
    def find_element(self, **kwargs):
        """
        根据 context.yaml 中定义的名称查找元素。
        
        :param kwargs: 包含 '_页面元素' 键的字典
        :return: Selenium WebElement 对象
        """
        all_ele_data = g_context().get_dict('_WEB页面元素')
        key = str(kwargs['_页面元素'])
        ele_data = all_ele_data[key]
        loctor_type = {
            'id': By.ID,
            'name': By.NAME,
            'class': By.CLASS_NAME,
            'xpath': By.XPATH,
            'By.ID': By.ID,
        }
        locator_types = loctor_type.get(ele_data['定位方式'], None)
        locator = (locator_types, ele_data['目标对象'])
        elses_list = self.wait_for_element(locator)
        
        # 增加空值检查，避免 NoneType 错误
        if elses_list is None or len(elses_list) == 0:
            raise Exception(f"未找到页面元素: '{key}', 定位方式: {ele_data['定位方式']}, 目标对象: {ele_data['目标对象']}")
        
        if len(elses_list) == 1:
            return elses_list[0]
        else:
            index = int(kwargs.get('INDEX', 0))
            return elses_list[index]

    @allure.step("点击元素")
    def 点击元素(self, **kwargs):
        """点击页面上的指定元素。"""
        self.show_log("点击数据显示出来", kwargs)
        eles_list = self.find_element(**kwargs)
        eles_list.click()
        self.get_screenshot()

    @allure.step("输入内容")
    def 输入内容(self, **kwargs):
        """向指定的输入框中输入文本。"""
        self.show_log("输入数据显示出来", kwargs)
        eles_list = self.find_element(**kwargs)
        eles_list.send_keys(kwargs['数据内容'])
        self.get_screenshot()

    # 关闭浏览器
    @allure.step("关闭浏览器")
    def 关闭浏览器(self):
        """关闭并退出浏览器驱动。"""
        self.driver.quit()

    # 窗口最大化
    @allure.step("窗口最大化")
    def 窗口最大化(self):
        """将浏览器窗口最大化。"""
        self.driver.maximize_window()

    @allure.step("强制等待")
    def 强制等待(self, **kwargs):
        """执行固定的时间等待（单位：秒）。"""
        time.sleep(int(kwargs['数据内容']))

    @allure.step("获取元素文本")
    def 获取元素文本(self, **kwargs):
        """获取元素的文本内容并存入全局变量。"""
        try:
            eles_list = self.find_element(**kwargs)
            ex_data = eles_list.text
            print('获取文本值', ex_data)
            g_context().set_dict(kwargs['变量名'], ex_data)
            logger.info(f'获取文本值成功{ex_data}')
        except Exception as e:
            logger.error(f'获取文本值失败{e}')
            raise e

    def 获取元素文本2(self, **kwargs):
        all_ele_data = g_context().get_dict('_WEB页面元素')
        key = str(kwargs['_页面元素'])  # 通过_页面元素  找到 手机号_输入框
        ele_data = all_ele_data[key]
        value = WebDriverWait(self.driver, 10).until(
            lambda x: x.find_element(ele_data['定位方式'], ele_data['目标对象']).text
        )
        g_context().set_dict(kwargs["变量名"], value)  # 设置到全局变量 中

    @allure.step("断言文本")
    def 断言文本(self,**kwargs):
        self.show_log("断言数据显示出来",kwargs)
        comparators={
            '>': lambda a,b:a>b,
            '>=': lambda a,b:a>=b,
            '<': lambda a,b:a<b,
            '<=': lambda a,b:a<=b,
            '==': lambda a,b:a==b,
            '!=': lambda a,b:a!=b,
            'in': lambda a,b:a in b,
            'not in': lambda a,b:a not in b,
        }
        message=kwargs.get('错误信息',None)
        compare_type=kwargs.get('断言类型','文本')
        operatros=kwargs.get('比较符','==')

        if operatros not in comparators:
            raise Exception(f'{operatros} 不在比较器中')

        if compare_type=='数字':
            compare_value=float(kwargs['预期结果'])
        else:
            compare_value=str(kwargs['预期结果'])

        if not comparators[operatros](kwargs['预期结果'],kwargs['实际结果']):
            if message:
                raise Exception(message)
            else:
                raise Exception(f'{kwargs["实际结果"]} {operatros} {kwargs["预期结果"]} 失败')

    def 断言文本相等(self,**kwargs):
        kwargs.update({"比较符":"=="})
        # 断言
        self.断言文本(**kwargs)

    def 断言文本包含(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """
        kwargs.update({"比较符": "in"})
        self.断言文本(**kwargs)

    def 断言文本不相等(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """
        kwargs.update({"比较符": "!="})
        self.断言文本(**kwargs)

        # ---------------------断言数字方法--------------------------------

    def 断言数字相等(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """

        kwargs.update({"比较符": "==", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字不相等(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """
        kwargs.update({"比较符": "!=", "断言类型": "数字"})
        self.断言文本(**kwargs)

    ##3>5
    def 断言数字大于(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """
        kwargs.update({"比较符": ">", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字小于(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """
        kwargs.update({"比较符": "<", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字大于等于(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """
        kwargs.update({"比较符": ">=", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 断言数字小于等于(self, **kwargs):
        """
        调用 断言文本assert_text方法
        """
        kwargs.update({"比较符": "<=", "断言类型": "数字"})
        self.断言文本(**kwargs)

    def 提取数据MYSQL(self, **kwargs):
        #拿到你想要的数据库信息
        db_config=g_context().get_dict("_数据库")[kwargs["_数据库"]]
        #以字典数据展示
        config={"cursorclass":cursors.DictCursor}
        config.update(db_config)
        #连接数据库
        con=pymysql.connect(**config)
        #创建游标
        cursor = con.cursor()
        sql=kwargs["SQL"]
        #执行sql
        cursor.execute(sql)
        # 获得结果
        rs = cursor.fetchall()
        ##6.关闭游标
        cursor.close()
        # 7.关闭数据库连接
        con.close()

        #需要把结果保存在全局变量中，后续需要从全局变量中去拿
        var_names=kwargs.get("变量名",[])
        result={}
        #最终效果没有用变量名 username_xx=15574113906  nick_name_xx='youyi'
        if not var_names:
            for i,item in enumerate(rs,start=1):#rs 假设2条数据 i=1 item={'username': '15574113906', 'nick_name': '15574113906'}  i=2 item={'username': '15574113906xx', 'nick_name': '155741xx13906'}
                for key,value in item.items():
                    #{username_1:15574113906,nick_name_1:15574113906}
                    result[f"{key}_{i}"]=value
        else:# 变量名有值 uname_xx:15574113906 nick_name_xx:'youyi'
            #获取数据库字段的数量
            field_length=len(rs[0]) if rs else 0
            # 判断变量名数量和数据库字段数量是否一致
            if len(var_names)!=field_length:
                raise Exception(f"变量名数量和数据库字段数量不一致")

            for idx,item in enumerate(rs,start=1):#i=1 item={'username': '15574113906', 'nick_name': '15574113906'}
                for col_idx,key in enumerate(item): #col_idx=0  key='username'  col_idx=1 nick_name
                    result[f"{var_names[col_idx]}_{idx}"] = item[key]
                    #{uname[0]}=uname     uname_1= item[username]  uname_1='15574113906'  下课后大家理一下
        #保存在全局变量
        g_context().set_by_dict(result)
        print('数据库查询结果的全局变量',g_context().show_dict())


    def show_log(self,data_name,data=None):
        logger.debug(f"-------------Log:{data_name}------------")
        logger.debug(f"{data_name}:{data}")
        logger.debug(f"-----------------END Log:{data_name}")

    def get_screenshot(self):#截图的方法
        img_base64=self.driver.get_screenshot_as_base64()
        #程序运行时正常每个步骤截图 不会串线程
        from HAT.utils.allure_step_logger import _current_step_name
        #截图不至于数据混乱
        self.screen_shots.append({
            "image": f"data:image/png;base64,{img_base64}",
            "caption": _current_step_name.get()
        })
        allure.attach(b64decode(img_base64.encode("ascii")),"截图",allure.attachment_type.PNG)


    def click_loacation(self,**kwargs):
        #拿到坐标进行点击x,y
        coordinate=kwargs['坐标']
        x_coordinate = float(coordinate.split(',')[0].strip())
        y_coordinate = float(coordinate.split(',')[1].strip())
        action_builder = ActionBuilder(self.driver)
        action_builder.pointer_action.move_to_location(x_coordinate, y_coordinate).click()
        action_builder.perform()

    #具体执行输入
    def input_location(self,**kwargs):
        self.click_loacation(坐标=kwargs['坐标'])
        #激活输入框输入
        self.driver.switch_to.active_element.send_keys(kwargs['文本'])

    #提取文本
    def store_text(self,**kwargs):
        g_context().set_dict(kwargs["变量名"], kwargs["变量值"])

    def AI操作(self,**kwargs):
        import base64, json, os, re, time, uuid
        from openai import OpenAI
        # 创建一个对象，用于执行 AI 指令  只是拿到
        ai_client = OpenAI(
            #从全局变量中拿到密钥，暂时还没用
            api_key=g_context().get_dict("HAT_LLM_API_KEY"),
            base_url=g_context().get_dict("HAT_LLM_BASE_URL"),
        )
        # 定义 AI 指令
        actions=["点击","输入","文本提取"]

        #提示词  很关键 但是可能需要优化，根据你的项目你可能需要优化
        prompt = """
                                  ## 目标
                                  - 识别屏幕截图和文本中与用户描述最匹配的一个元素。

                                  ## 输出格式
                                  ```json
                                  {{
                                    "bbox": [xmin,ymin,xmax,ymax],
                                    "action": "用户的操作类型（{actions}）",
                                    "text": "提取的文本内容",
                                    "errors"?: "如果你无法找到，就把你的原因写在这里"
                                  }}
                                  ```
                                  只能是一个json对象，不能是数组列表

                                  ## 工作流程
                                  1. 接受用户描述的文字以及提供的截图。请注意，文本可能包含非英文字符（例如中文），这表面程序可能是非英文的。
                                  2. 分析用户的文字内容，提取其中关于元素的描述信息。根据关于元素的描述信息，找到屏幕截图中目标元素。
                                  3. 返回元素在截图中的 bbox 具体位置信息。

                                  ## 用户描述
                                  {user_text}
                                          """
        # 提示词  决定了人工智能还是人工智障
        ai_prompt = prompt.format(
            user_text=kwargs["操作描述"],
            actions=", ".join(actions)
        )

        #进行截图的操作 获取屏幕截图
        image_base64=self.driver.get_screenshot_as_base64()
        #保存到文件中，文件名用uuid生成
        image_path=os.path.join(os.path.dirname(__file__), f"{str(uuid.uuid4()).replace('-', '')}.png")
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_base64))

        #获取图片的尺寸
        from PIL import Image
        width, height = Image.open(image_path).size
        logger.debug(f"截图尺寸：{width}, {height} ")

        #缩放图片 需要换算成模型所需要的尺寸
        min_pixels = 512 * 28 * 28
        max_pixels = 2048 * 28 * 28
        from qwen_vl_utils import smart_resize
        # input_height, input_width = smart_resize(height, width, min_pixels=min_pixels, max_pixels=max_pixels)
        input_height, input_width = smart_resize(height, width, factor=1.0, min_pixels=min_pixels,
                                                 max_pixels=max_pixels)

        #删除图片
        os.remove(image_path)

        #图片+文字发给ai大模型
        completion = ai_client.chat.completions.create(
            model=g_context().get_dict("HAT_LLM_MODEL_NAME"),
            # 此处以qwen-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[{"role": "user", "content": [
                {"type": "image_url",
                 "min_pixels": min_pixels,
                 "max_pixels": max_pixels,
                 "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                {"type": "text", "text": ai_prompt}
            ]}]
        )
        logger.debug("AI执行结果：", completion.model_dump_json())
        ## json:
        # {
        # "bbox":[100,200,150,220] //按钮在图片上的位置
        # "action": "点击"  //要执行的动作
        # "text":"xxx"  //输入要文字
        # }

        #返回结果  需要对于这个结果去进行处理  想看结果 json.loads(completion.model_dump_json())打印出来 取content
        ai_response = json.loads(completion.model_dump_json())['choices'][0]['message']['content']
        pattern = r'```json\n(.*?)```'
        match = re.search(pattern, ai_response, re.DOTALL)
        json_content = match.group(1)
        # 根据json数据进行后续处理
        result = json.loads(json_content)
        logger.debug(f"提取出来要处理的操作: {result}")

        #坐标是图片的坐标换算真实的坐标
        bbox = result['bbox']
        result['bbox'] = [bbox[0] / input_width * width, bbox[1] / input_height * height, bbox[2] / input_width * width,
                          bbox[3] / input_height * height]

        #取中心点
        if result["action"]=="点击":
            bbox=result['bbox']
            x_coordinate = (bbox[0] + bbox[2]) / 2
            y_coordinate = (bbox[1] + bbox[3]) / 2
            # 进行点击操作
            self.click_loacation(坐标=f"{x_coordinate},{y_coordinate}")
        elif result["action"]=="输入":
            bbox = result['bbox']
            x_coordinate = (bbox[0] + bbox[2]) / 2
            y_coordinate = (bbox[1] + bbox[3]) / 2
            # 进行点击操作
            self.input_location(坐标=f"{x_coordinate},{y_coordinate}",文本=result["text"])
        elif result["action"]=="文本提取":
            self.store_text(变量名="ai_value", 变量值=result['text'])
        else:
            raise Exception("不支持的操作")
        self.get_screenshot()


    def AI断言(self,**kwargs):
        import base64, json, os, re, time, uuid
        from openai import OpenAI
        # 创建一个对象，用于执行 AI 指令  只是拿到
        ai_client = OpenAI(
            # 从全局变量中拿到密钥，暂时还没用
            api_key=g_context().get_dict("HAT_LLM_API_KEY"),
            base_url=g_context().get_dict("HAT_LLM_BASE_URL"),
        )
        # 提示词  很关键 但是可能需要优化，根据你的项目你可能需要优化
        prompt = """
                          ## 目标
                          - 分析用户给出的一个对于图片内容的判断，并返回你的判断结果。

                          ## 输出格式示例：
                          ```json
                          {{
                            "result": "true", # 统一小写
                            "msg": "你的判断依据"
                          }}
                          ```
                          只能是一个json对象，不能是数组列表

                          ## 工作流程
                          1. 接受用户描述的文字以及提供的截图。请注意，文本可能包含非英文字符（例如中文），这表面程序可能是非英文的


                          ## 用户描述
                          {user_text}
                                  """
        # 提示词  决定了人工智能还是人工智障
        ai_prompt = prompt.format(
            user_text=kwargs["操作描述"],   #检查页面右上角我的书架旁边是否包含15574113907的账号
        )

        # 进行截图的操作 获取屏幕截图
        image_base64 = self.driver.get_screenshot_as_base64()
        # 保存到文件中，文件名用uuid生成
        image_path = os.path.join(os.path.dirname(__file__), f"{str(uuid.uuid4()).replace('-', '')}.png")
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_base64))

        # 获取图片的尺寸
        from PIL import Image
        width, height = Image.open(image_path).size
        logger.debug(f"截图尺寸：{width}, {height} ")

        # 缩放图片 需要换算成模型所需要的尺寸
        min_pixels = 512 * 28 * 28
        max_pixels = 2048 * 28 * 28
        from qwen_vl_utils import smart_resize
        # input_height, input_width = smart_resize(height, width, min_pixels=min_pixels, max_pixels=max_pixels)
        input_height, input_width = smart_resize(height, width, factor=1.0, min_pixels=min_pixels,
                                                 max_pixels=max_pixels)

        # 删除图片
        os.remove(image_path)

        # 图片+文字发给ai大模型
        completion = ai_client.chat.completions.create(
            model=g_context().get_dict("HAT_LLM_MODEL_NAME"),
            # 此处以qwen-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[{"role": "user", "content": [
                {"type": "image_url",
                 "min_pixels": min_pixels,
                 "max_pixels": max_pixels,
                 "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                {"type": "text", "text": ai_prompt}
            ]}]
        )
        logger.debug("AI执行结果：", completion.model_dump_json())
        #{
        # id：xxx
        # object："chat.completion"
        # created：xxx
        # model："qwen-vl-plus"
        # choices：[{xxxx}]
        # }
        ai_response = json.loads(completion.model_dump_json())['choices'][0]['message']['content']
        pattern = r'```json\n(.*?)```'
        match = re.search(pattern, ai_response, re.DOTALL)
        json_content = match.group(1)
        # 根据json数据进行后续处理
        result = json.loads(json_content)
        logger.debug(f"提取出来要处理的操作: {result}")
        """
         ```json
                          {{
                            "result": "true", # 统一小写
                            "msg": "你的判断依据"
                          }}
                          ```
        """
        #断言
        assert str(result["result"]).lower()=="true",result["msg"]

    def 断言浏览器路径(self, **kwargs):
        """# 断言处理 - 断言当前Url"""
        expected_url = kwargs["数据内容"]
        actual_url = self.driver.current_url
        result = EC.url_to_be(expected_url)(self.driver)
        
        if not result:
            self.get_screenshot()
            raise AssertionError(f"URL断言失败!\n期望: {expected_url}\n实际: {actual_url}")
        
        self.get_screenshot()

        # 元素 - 图片数字验证码识别
    def image_recognition(self, **kwargs):
        print("---开始图片识别---")
        ocr = DdddOcr()
        eles_list = self.find_element(**kwargs)

        file_name = "img.png"

        eles_list.screenshot(file_name)

        # 打开我的图片binary_pic  取个名字code read进行读
        with open(file_name, 'rb') as code:
            v_img = code.read()
            # 读图片里面的内容  以后你们碰到了阴影 一般.出来的代码是最正确
            result = ocr.classification(v_img)
            print("识别出来的结果为", result)

        var_names = kwargs["引用变量"]
        g_context().set_by_dict({var_names: result})

        # iframe切换 - 切换到指定窗口

    def iframe_switch_to(self, **kwargs):
        eles_list = self.find_element(**kwargs)
        # 再切换进iframe
        self.driver.switch_to.frame(eles_list)
        # iframe切换 - 退出到上一层

    def iframe_to_parent_frame(self, **kwargs):
        self.driver.switch_to.parent_frame()
        # iframe切换 - 退出到最外层

    def iframe_to_default_content(self, **kwargs):
        self.driver.switch_to.default_content()

    def random_six_digit_number(self, **kwargs):  # 方法名称 必须与关键字名称一致
        import random
        # 生成一个6位数的随机数
        random_six_digit_number = random.randint(100000, 999999)
        g_context().set_dict(kwargs["变量名"], random_six_digit_number)

    # 浏览器操作- 切换最新的窗口
    def switch_to_latest_handle(self, **kwargs):
        handle = self.driver.window_handles[-1]
        self.driver.switch_to.window(handle)

    # 浏览器操作- 切换指定的窗口
    def switch_to_appoint_handle(self, **kwargs):
        index = int(kwargs["数据内容"])
        handle = self.driver.window_handles[index]
        self.driver.switch_to.window(handle)


    def ex_invoke(self, **kwargs):
        key=kwargs["key"] #输入内容
        if g_context().get_dict("key_dir") is not None:#./HAT/key_dir
            sys.path.append(g_context().get_dict("key_dir"))#拿到key_dir目录
            module=__import__(key)  #from HAT.keywords.web_keywords import Keywords
            class_=getattr(module,key)#获取类
            key_func=class_(self.driver).__getattribute__(key)#在类中获取方法名
            key_func(**kwargs['step_value'])#执行方法
