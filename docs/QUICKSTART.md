# HAT 自动化测试框架 — 快速入门

## 目录

1. [环境准备](#1-环境准备)
2. [5分钟快速体验](#2-5分钟快速体验)
3. [项目结构](#3-项目结构)
4. [测试用例编写](#4-测试用例编写)
5. [POM 页面对象模式](#5-pom-页面对象模式)
6. [DDT 数据驱动测试](#6-ddt-数据驱动测试)
7. [查看测试报告](#7-查看测试报告)
8. [CLI 命令行参数](#8-cli-命令行参数)
9. [CI/CD 集成](#9-cicd-集成)
10. [常见问题排查](#10-常见问题排查)

---

## 1. 环境准备

### 安装 Python 3.8+

```bash
python --version
```

### 创建虚拟环境

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 安装 Allure CLI

1. 下载: https://github.com/allure-framework/allure2/releases
2. 解压到任意目录（如 `C:\allure`）
3. 将 `bin` 目录添加到 PATH 环境变量
4. 验证: `allure --version`

---

## 2. 5分钟快速体验

```bash
# Excel 用例模式（默认）
python main.py --cases=./examples/reelmate-cases-excel

# 无头模式（CI/CD，不显示浏览器）
python main.py --cases=./examples/reelmate-cases-excel --headless

# 无头 + 并行执行（最快）
python main.py --cases=./examples/reelmate-cases-excel --headless --workers=4

# 指定浏览器
python main.py --cases=./examples/reelmate-cases-excel --browser=firefox
```

运行成功后自动打开 Allure 可视化报告。

---

## 3. 项目结构

```
web_auto_playwright/
├── main.py                    # CLI 入口
├── conftest.py                # pytest 全局配置
├── HAT/                       # 框架核心
│   ├── config.py              # 全局配置管理
│   ├── plugin.py              # pytest 插件（用例收集与参数化）
│   ├── runner.py              # 测试执行器（三级派发）
│   ├── browser.py             # Playwright 浏览器生命周期
│   ├── keywords.py            # 内置关键字方法（40+）
│   ├── locator.py             # 语义化定位器构建器
│   ├── parser.py              # Excel/YAML 用例解析器（含 DDT）
│   ├── template.py            # Jinja2 变量渲染
│   ├── pages/                 # POM 页面对象
│   │   ├── base.py            # 基础页面对象
│   │   └── login.py           # 登录页面对象
│   └── locators/              # 页面元素定位（YAML）
│       └── login_page.yaml
├── examples/                  # 示例测试项目
│   ├── reelmate-cases-excel/  # Excel 用例示例
│   ├── reelmate-cases/        # YAML 用例示例
│   └── pom-login-test/        # POM 示例
└── docs/
    └── QUICKSTART.md          # 本文档
```

---

## 4. 测试用例编写

### 4.1 Excel 用例格式（推荐）

**context.xlsx** — 全局配置（多 Sheet）：

| Sheet 名称 | 说明 |
|-----------|------|
| 浏览器配置 | browserName, 启动参数 |
| WEB页面元素 | 元素名称, 定位方式, 目标对象 |
| 通用配置 | 全局变量 (base_url, username 等) |
| 数据库配置 | 别名, 服务器IP, 端口, 用户名, 密码 |

**用例文件** `1_登录测试.xlsx`：

| 用例编号 | 模块 | 功能 | 用例标题 | 用例类型 | 测试步骤 | 操作类型 | 数据内容 |
|---------|------|------|---------|---------|---------|---------|---------|
| TC-1001 | 登录 | 密码登录 | 正确账号登录 | WebCase | 打开首页 | 访问网址 | 网址=https://example.com |
| | | | | | 输入账号 | 输入内容 | _页面元素=用户名输入框 数据内容=18318053665 |
| | | | | | 点击登录 | 点击元素 | _页面元素=登录按钮 |

**规则**: 每个用例首行填写完整，后续行这些列留空；数据内容用 `key=value` 格式。

### 4.2 YAML 用例格式（保留支持）

```yaml
基础配置:
  用例类型: WebCase
  一级模块: 登录模块
  二级模块: 密码登录
  用例标题: 正确账号登录成功

用例步骤:
  - 打开首页:
      操作类型: 访问网址
      网址: "{{base_url}}"

  - 输入账号:
      操作类型: 输入内容
      数据内容: "{{username}}"
      _页面元素: 用户名输入框

  - 点击登录:
      操作类型: 点击元素
      _页面元素: 登录按钮
```

### 4.3 元素定位方式

优先级从高到低（Playwright 最佳实践）：

| 定位方式 | 说明 | 配置示例 |
|---------|------|---------|
| role | 语义角色+名称（最稳定） | `role, button, "登录"` |
| label | 关联 label 的表单元素 | `label, , "用户名"` |
| placeholder | 输入框占位符 | `placeholder, , "请输入邮箱"` |
| text | 可见文本 | `text, , "登录"` |
| testid | data-testid 属性 | `testid, , "submit-btn"` |
| css | CSS 选择器（兜底） | `css, , ".btn-primary"` |
| xpath | XPath（最后手段） | `xpath, , "//button[@type='submit']"` |

**语义化定位器 YAML 格式** (`HAT/locators/xxx.yaml`)：

```yaml
username_input:
  type: placeholder
  value: "请输入手机号/邮箱"
  frame: "#loginDialog iframe"  # iframe 内元素需指定 frame

login_submit_btn:
  type: role
  role: button
  name: "立即登录"
  frame: "#loginDialog iframe"
```

### 4.4 常用操作类型速查

**导航**: 访问网址, 页面刷新, 页面前进, 页面后退
**元素**: 点击元素, 输入内容, 输入内容追加, 清空输入框, 鼠标悬停, 双击元素, 右键点击
**表单**: 选择下拉框选项, 勾选复选框, 取消勾选, 上传文件
**获取**: 获取元素文本, 获取元素属性, 获取当前URL, 获取页面标题
**断言**: 断言文本包含, 断言文本相等, 断言元素存在, 断言元素不存在, 断言页面标题, 断言浏览器路径
**窗口**: 强制等待, 窗口最大化, iframe_switch_to, switch_to_latest_handle
**其他**: 执行JS, 键盘按键, 拖拽元素, 滚动到元素, 关闭浏览器

---

## 5. POM 页面对象模式

### 5.1 使用 POM 用例

在 Excel/YAML 中，操作类型使用 `页面类名.方法名` 格式：

```yaml
用例步骤:
  - 导航到登录页:
      操作类型: LoginPage.navigate_to_login

  - 登录:
      操作类型: LoginPage.login
      username: "{{username}}"
      password: "{{password}}"

  - 验证成功:
      操作类型: LoginPage.verify_login_success
```

### 5.2 新建页面对象

1. 在 `HAT/locators/` 下创建 `my_page.yaml` 定义元素定位器
2. 在 `HAT/pages/` 下创建 `my_page.py` 继承 `BasePage`
3. 在 `HAT/runner.py` 的 `_init_pages()` 中注册

```python
# HAT/pages/my_page.py
from types import SimpleNamespace
from HAT.locator import LocatorBuilder
from HAT.pages.base import BasePage

class MyPage(BasePage):
    PAGE_URL = "https://example.com"

    def __init__(self, keywords):
        super().__init__(keywords)
        # Load semantic locators from YAML
        import os
        yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "locators", "my_page.yaml")
        locators = LocatorBuilder.from_yaml(self.page, yaml_path)
        self.locators = SimpleNamespace(**locators)

    def click_login(self):
        self.click(self.locators.login_btn)
```

---

## 6. DDT 数据驱动测试

### 6.1 概念

一个测试模板 + 多组数据 = 多个独立测试实例

### 6.2 YAML 方式

```yaml
用例步骤:
  - 输入账号:
      操作类型: 输入内容
      数据内容: "{{username}}"
      _页面元素: 用户名输入框

数据驱动:
  - username: "user1@test.com"
    描述标题: 有效账号登录

  - username: "user1@test.com"
    描述标题: 错误密码登录

  - username: ""
    描述标题: 空账号校验
```

展开生成：`登录测试-有效账号登录`, `登录测试-错误密码登录`, `登录测试-空账号校验`

### 6.3 Excel 方式

在 Excel 用例文件中添加 **"数据驱动"** Sheet：

| 用例标题 | 描述标题 | username | password |
|---------|---------|----------|----------|
| 登录测试 | 有效账号 | user1@test.com | pass123 |
| 登录测试 | 错误密码 | user1@test.com | wrong |
| 登录测试 | 空账号 | | pass123 |

**规则**:
- `用例标题` 必须与用例 Sheet 中的标题完全匹配
- `描述标题` 必填，作为测试实例名称后缀
- 其他列自动作为 DDT 参数

### 6.4 DDT 最佳实践

1. **描述标题要具体**: 用 `有效账号-手机号` 而非 `case1`
2. **覆盖边界值**: 空值、超长、特殊字符、SQL 注入等
3. **正反用例分开**: 在 DDT 中混合正反用例时，断言也要参数化
4. **Excel 更适合大数据量 DDT**: 20+ 组数据时 Excel 管理更直观

---

## 7. 查看测试报告

测试完成后自动打开 Allure 报告：

```bash
# 报告位置
HTML测试报告/report.html

# 包含内容
# - 测试通过/失败统计
# - 每步执行截图
# - 失败用例错误信息
# - 截图幻灯片回放
# - Playwright Trace（可在 trace.playwright.dev 查看）
```

---

## 8. CLI 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--cases` | `examples/reelmate-cases-excel` | 用例文件夹路径 |
| `--type` | `excel` | 用例格式: excel / yaml |
| `--headless` | `false` | 无头模式（不显示浏览器） |
| `--browser` | `chromium` | 浏览器: chromium / firefox / webkit |
| `--workers` | `1` | 并行执行数 (`pip install pytest-xdist`) |
| `--alluredir` | `./test-results` | Allure 原始数据目录 |
| `--report_html_path` | `./HTML测试报告` | HTML 报告输出目录 |
| `--keyDir` | (空) | 自定义关键字扩展目录 |

---

## 9. CI/CD 集成

### GitHub Actions

```yaml
- name: HAT Tests
  run: |
    pip install -r requirements.txt
    playwright install chromium --with-deps
    python main.py --cases=./examples/reelmate-cases-excel --headless --workers=4
```

### Jenkins / GitLab CI / Drone

```bash
python main.py --cases=./examples/reelmate-cases-excel --headless --workers=4 --report_html_path=./test-report
```

---

## 10. 常见问题排查

### Q: "未找到页面元素定义"

检查 context 文件中的 `_WEB页面元素` 或 `_locators` 是否包含步骤中引用的元素名称。

### Q: `{{变量名}}` 没有被替换

变量未在 context 文件或 DDT 数据中定义。确保变量名拼写一致。

### Q: 浏览器打开后立即关闭

```bash
playwright install chromium
playwright install-deps
```

### Q: Allure 报告未生成

确认 Allure CLI 已安装并配置到 PATH: `allure --version`

### Q: POM 用例报错 "未找到注册的页面对象"

页面对象未在 `TestRunner._init_pages()` 中注册。

### Q: 并行执行不生效

```bash
pip install pytest-xdist
```

### Q: Excel 用例中文乱码

确保 Excel 文件为 UTF-8 编码，或使用项目中的 `create_excel_cases.py` 生成标准文件。
