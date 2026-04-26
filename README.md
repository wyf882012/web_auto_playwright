# HAT (HCTest Automation Tool) 自动化测试框架

基于 **Playwright + pytest + Allure** 的混合型企业级自动化测试框架，支持关键字驱动与 POM (Page Object Model) 两种模式。

---

## 目录

- [特性](#特性)
- [框架架构](#框架架构)
- [快速开始](#快速开始)
- [用例格式](#用例格式)
- [POM 页面对象模式](#pom-页面对象模式)
- [关键字参考](#关键字参考)
- [配置说明](#配置说明)
- [命令行参数](#命令行参数)
- [AI 视觉操作](#ai-视觉操作)
- [高级功能](#高级功能)

---

## 特性

- **双引擎架构** — 关键字驱动 + POM 页面对象，可混用
- **Playwright 原生选择器** — text / role / placeholder / testid / css / xpath
- **双格式用例** — YAML / Excel，数据结构统一
- **数据驱动 (DDT)** — 一组用例模板 + 多组数据 = 多个测试实例
- **Jinja2 模板变量** — `{{username}}` 占位符自动替换
- **Allure 报告** — 自动生成可视化 HTML 测试报告，含截图回放
- **AI 视觉操作** — 视觉模型识别屏幕元素并执行操作/断言
- **截图播放回放** — 每步骤自动截图，生成幻灯片式回放

---

## 框架架构

```
main.py (入口)
  └─ CasesPlugin (pytest 插件)
       └─ case_parser (YAML/Excel 解析)
            └─ TestRunner (测试执行器)
                 ├── WebCaseContext (浏览器生命周期)
                 ├── Keywords (50+ 关键字方法)
                 └── POM Pages (页面对象)

HAT/
├── core/         测试核心
│   ├── CasesPlugin.py       pytest 自定义插件
│   ├── TestRunner.py        测试执行器（三级解析机制）
│   └── globalContext.py     全局上下文单例
├── context/
│   └── WebCaseContext.py    Playwright 浏览器管理 + POM 注册
├── keywords/
│   └── web_keywords.py      50+ 内置关键字方法
├── pages/         POM 页面对象层（v2026.4 新增）
│   ├── base_page.py         POM 基类
│   └── login_page.py        reelmate.cn 登录页面对象
├── parse/         用例解析器
│   ├── caseParser.py        统一派发入口
│   ├── YamlCaseParser.py    YAML 解析
│   └── ExcelCaseParser.py   Excel 解析
├── utils/         工具
│   ├── VarRender.py         Jinja2 模板渲染
│   └── allure_step_logger.py 步骤日志收集
├── extend/        扩展
│   ├── script/run_script.py   动态 Python 脚本执行
│   └── allure_combine/        Allure 单文件报告合并
└── key_dir/       自定义关键字扩展
```

### 三级解析机制

TestRunner 在解析 `操作类型` 时按以下优先级查找：

```
操作类型: "LoginPage.login"     → Level 1: POM 页面对象方法 [新]
操作类型: "输入内容"             → Level 2: Keywords 内置关键字
操作类型: "自定义关键字"         → Level 3: ex_invoke 动态加载
```

---

## 快速开始

### 环境要求

- Python 3.8+
- Allure CLI（[下载地址](https://github.com/allure-framework/allure2/releases)）

### 安装

```bash
# 1. 安装 Python 依赖
pip install -r requeirement.txt

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 安装 Allure CLI 并配置到 PATH
# 下载: https://github.com/allure-framework/allure2/releases
```

### 运行测试

```bash
# Excel 用例模式（推荐）
python main.py --type=excel --cases=./examples/reelmate-cases-excel

# YAML 用例模式
python main.py --type=yaml --cases=./examples/reelmate-cases

# 指定自定义报告路径
python main.py --type=excel --cases=./examples/reelmate-cases-excel --alluredir=./test-results --report_html_path=./报告
```

---

## 用例格式

### YAML 格式

```yaml
基础配置:
  用例类型: WebCase
  一级模块: 登录模块
  二级模块: 登录功能
  用例标题: 正确账号密码登录成功

用例步骤:
  - 访问首页:
      操作类型: 访问网址
      网址: "{{base_url}}"
      等待方式: load

  - 输入账号:
      操作类型: 输入内容
      数据内容: "{{username}}"
      _页面元素: 用户名输入框

  - 输入密码:
      操作类型: 输入内容
      数据内容: "{{password}}"
      _页面元素: 密码输入框

  - 点击登录:
      操作类型: 点击元素
      _页面元素: 登录提交按钮

数据驱动:
  - username: "18318053665"
    password: "qq111111"
    描述标题: 有效账号
```

### Excel 格式

| 模块 | 功能 | 用例标题 | 用例类型 | 测试步骤 | 操作类型 | 数据内容 |
|------|------|----------|----------|----------|----------|----------|
| 登录模块 | 登录功能 | TC002-正确账号密码登录 | WebCase | 访问首页 | 访问网址 | 网址="https://www.reelmate.cn" 等待方式="load" |
| 登录模块 | 登录功能 | TC002-正确账号密码登录 | WebCase | 输入账号 | 输入内容 | 数据内容="18318053665" _页面元素="用户名输入框" |
| 登录模块 | 登录功能 | TC002-正确账号密码登录 | WebCase | 输入密码 | 输入内容 | 数据内容="qq111111" _页面元素="密码输入框" |
| 登录模块 | 登录功能 | TC002-正确账号密码登录 | WebCase | 点击登录 | 点击元素 | _页面元素="登录提交按钮" |

### context 配置文件

元素定位器使用 Playwright 原生选择器（优先级：text > placeholder > role > testid > css > xpath）：

```yaml
# context.yaml
_浏览器:
  capability:
    browserName: chromium

username: "18318053665"
password: "qq111111"
base_url: "https://www.reelmate.cn"

_WEB页面元素:
  用户名输入框:
    定位方式: css
    目标对象: 'input[type="email"], input[name="username"]'
  登录提交按钮:
    定位方式: css
    目标对象: 'button[type="submit"], button:has-text("登录")'
```

---

## POM 页面对象模式 (v2026.4)

### 概念

POM 模式将页面元素定位器和业务操作方法封装在页面对象类中，提供更高层次的抽象。通过 `操作类型` 字段的点分表示法调用：

```
操作类型: LoginPage.login          → LoginPage 实例的 login() 方法
操作类型: LoginPage.navigate_to_login → LoginPage 实例的 navigate_to_login() 方法
```

### POM 用例示例

#### YAML 格式

```yaml
基础配置:
  用例类型: WebCase
  一级模块: 登录模块
  二级模块: 登录功能
  用例标题: POM方式-登录成功测试

用例步骤:
  - 导航到登录页:
      操作类型: LoginPage.navigate_to_login

  - 执行登录:
      操作类型: LoginPage.login
      username: "{{username}}"
      password: "{{password}}"

  - 验证登录成功:
      操作类型: LoginPage.verify_login_success
      login_url: "https://accounts.wondershare.cn/login"
```

#### Excel 格式

| 操作类型 | 数据内容 |
|----------|----------|
| LoginPage.navigate_to_login | (空) |
| LoginPage.login | username="18318053665" password="qq111111" |
| LoginPage.verify_login_success | login_url="https://accounts.wondershare.cn/login" |

### 内置页面对象

#### LoginPage — 登录页面对象

| 方法 | 参数 | 说明 |
|------|------|------|
| `navigate_to_login` | — | 打开首页 → 点击登录入口 |
| `login` | username, password | 完整登录流程（输入+点击+等待） |
| `enter_username` | username | 仅输入用户名 |
| `enter_password` | password | 仅输入密码 |
| `click_login_button` | — | 仅点击登录按钮 |
| `clear_username` | — | 清空用户名输入框 |
| `clear_password` | — | 清空密码输入框 |
| `verify_login_page_elements` | — | 验证用户名/密码/登录按钮存在 |
| `verify_login_success` | login_url | 验证 URL 已离开登录页 |
| `verify_login_failed_stay_on_page` | login_url | 验证 URL 仍在登录页 |
| `get_error_message` | timeout | 获取登录错误提示文本 |
| `is_login_page` | — | 检查是否在登录页面 |
| `is_logged_in` | — | 检查是否已登录成功 |

### 自定义页面对象

继承 `BasePage` 创建新的页面对象：

```python
from HAT.pages.base_page import BasePage

class HomePage(BasePage):
    PAGE_NAME = "HomePage"
    PAGE_URL = "https://www.reelmate.cn"

    _LOCATORS = {
        "搜索框": {
            "定位方式": "css",
            "目标对象": 'input[type="search"]'
        },
        "搜索按钮": {
            "定位方式": "text",
            "目标对象": "搜索"
        },
    }

    def search(self, keyword: str):
        self.fill("搜索框", keyword)
        self.click("搜索按钮")
```

然后在 `WebCaseContext._init_page_objects()` 中注册：

```python
home_page = HomePage(self.keywords)
pom_pages[HomePage.__name__] = home_page
```

---

## 关键字参考

### 页面导航

| 方法 | 参数 | 说明 |
|------|------|------|
| `访问网址` | 网址, 超时, 等待方式 | 打开指定 URL |
| `页面刷新` | — | 刷新当前页面 |
| `页面前进` | — | 浏览器前进 |
| `页面后退` | — | 浏览器后退 |

### 元素操作

| 方法 | 参数 | 说明 |
|------|------|------|
| `点击元素` | _页面元素, 超时, INDEX | 点击元素 |
| `输入内容` | _页面元素, 数据内容, 超时, 先清除 | 输入文本 |
| `输入内容追加` | _页面元素, 数据内容, 超时 | 追加输入 |
| `清空输入框` | _页面元素 | 清空输入框 |
| `鼠标悬停` | _页面元素 | 鼠标悬停 |
| `双击元素` | _页面元素 | 双击元素 |
| `右键点击` | _页面元素 | 右键点击 |

### 表单操作

| 方法 | 参数 | 说明 |
|------|------|------|
| `选择下拉框选项` | _页面元素, 数据内容 | 按文本选择 |
| `选择下拉框选项按值` | _页面元素, 数据内容 | 按值选择 |
| `勾选复选框` | _页面元素 | 勾选 |
| `取消勾选` | _页面元素 | 取消勾选 |
| `上传文件` | _页面元素, 文件路径 | 上传文件 |

### 断言

| 方法 | 参数 | 说明 |
|------|------|------|
| `断言文本` | 预期结果, 实际结果, 比较符 | 通用断言（==, !=, in, >, < 等） |
| `断言文本相等` | 预期结果, 实际结果 | 等于断言 |
| `断言文本包含` | 预期结果, 实际结果 | 包含断言 |
| `断言元素存在` | _页面元素, 超时 | 元素存在断言 |
| `断言元素不存在` | _页面元素, 超时 | 元素不存在断言 |
| `断言浏览器路径` | 数据内容 | URL 包含断言 |
| `断言页面标题` | 预期结果 | 标题包含断言 |
| `断言数字相等/不相等/大于/小于/大于等于/小于等于` | 预期结果, 实际结果 | 数字比较 |

### 等待与窗口

| 方法 | 参数 | 说明 |
|------|------|------|
| `强制等待` | 数据内容 | 等待 N 秒 |
| `关闭浏览器` | — | 关闭浏览器 |
| `关闭当前页面` | — | 关闭当前标签页 |
| `switch_to_latest_handle` | — | 切换到最新标签页 |
| `switch_to_appoint_handle` | 数据内容 | 切换到指定标签页 |

### 获取信息

| 方法 | 参数 | 说明 |
|------|------|------|
| `获取元素文本` | _页面元素, 变量名 | 获取文本 |
| `获取元素属性` | _页面元素, 属性名, 变量名 | 获取属性 |
| `获取当前URL` | 变量名 | 获取 URL |
| `获取页面标题` | 变量名 | 获取标题 |

### 高级

| 方法 | 参数 | 说明 |
|------|------|------|
| `执行JS` | 数据内容, 变量名 | 执行 JavaScript |
| `iframe_switch_to` | _页面元素 | 切换到 iframe |
| `iframe_to_default_content` | — | 退出 iframe |
| `键盘按键` | 数据内容 | 键盘操作 |
| `拖拽元素` | 源元素, 目标元素 | 拖拽 |
| `滚动到元素` | _页面元素 | 滚动到元素 |
| `滚动页面` | X, Y | 滚动页面 |
| `store_text` | 变量名, 变量值 | 存储变量 |
| `random_six_digit_number` | 变量名 | 生成随机 6 位数 |
| `image_recognition` | _页面元素, 引用变量 | ddddocr 验证码识别 |

---

## 配置说明

### context.yaml / context.xlsx

```yaml
# 浏览器配置
_浏览器:
  capability:
    browserName: chromium      # chromium / firefox / webkit
  options:
    args:
      - "--disable-blink-features=AutomationControlled"

# 会话复用（同一浏览器实例执行多个用例，加快执行速度）
session_reuse: False

# 测试数据
username: "18318053665"
password: "qq111111"
base_url: "https://www.reelmate.cn"

# 页面元素（关键字模式使用）
_WEB页面元素:
  用户名输入框:
    定位方式: css
    目标对象: 'input[type="email"], input[name="username"]'
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `HAT_LOG_LEVEL` | 日志级别（DEBUG/INFO/WARNING/ERROR，默认 INFO） |
| `HAT_LLM_API_KEY` | AI 大模型 API Key |
| `HAT_LLM_BASE_URL` | AI 大模型 API 地址 |
| `HAT_LLM_MODEL_NAME` | AI 大模型名称 |

---

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 用例类型: yaml \| excel | yaml |
| `--cases` | 用例文件夹路径 | examples/web-cases-yaml |
| `--keyDir` | 自定义关键字代码路径 | — |
| `--alluredir` | Allure 结果目录 | ./test-results |
| `--report_html_path` | HTML 报告输出目录 | ./HTML测试报告 |

---

## AI 视觉操作

配置大模型环境变量后，可使用 AI 视觉模式：

```yaml
- AI操作步骤:
    操作类型: AI操作
    操作描述: "点击页面上的登录按钮"

- AI断言步骤:
    操作类型: AI断言
    操作描述: "页面显示了用户名"
```

AI 模式使用视觉模型对截图进行元素识别和判断，适用于传统选择器无法定位的复杂场景。

---

## 高级功能

### 数据驱动 (DDT)

```yaml
用例步骤:
  - 输入账号:
      操作类型: 输入内容
      数据内容: "{{username}}"
      _页面元素: 用户名输入框

数据驱动:
  - username: "18318053665"
    password: "qq111111"
    描述标题: 有效账号
  - username: "invalid@test.com"
    password: "wrongpass"
    描述标题: 无效账号
```

### 前置/后置脚本

```yaml
前置脚本:
  - context.update({'timestamp': '20260426'})
  - context.update({'random_email': f'user{random.randint(100,999)}@test.com'})

用例步骤:
  # ... 使用 {{timestamp}} 和 {{random_email}} 变量
```

### 自定义关键字

在 `key_dir/` 目录下创建 Python 类，方法名即关键字名：

```python
# key_dir/我的操作.py
class 我的操作:
    def __init__(self, page, context, browser):
        self.page = page

    def 我的操作(self, **kwargs):
        # 自定义逻辑
        print(kwargs.get("参数1", ""))
```

---

## 项目版本

**v2026.4-playwright** — 基于 Playwright 的混合型自动化测试框架，支持关键字驱动与 POM 双模式。
