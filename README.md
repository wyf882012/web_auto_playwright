# HAT (Hybrid Automation Testing) 自动化测试框架

基于 **Playwright + pytest + Allure** 的混合型企业级 UI 自动化框架，支持关键字驱动、POM、AI 视觉操作三种模式混用。

---

## 目录

- [特性](#特性)
- [框架架构](#框架架构)
- [快速开始](#快速开始)
- [用例格式](#用例格式)
- [操作类型体系](#操作类型体系)
- [关键字参考](#关键字参考)
- [POM 页面对象](#pom-页面对象)
- [AI 视觉操作](#ai-视觉操作)
- [配置说明](#配置说明)
- [命令行参数](#命令行参数)

---

## 特性

- **三模式混用** — 传统关键字 + POM (Page Object Model) + AI 视觉，同一用例可任意组合
- **Playwright 语义定位器** — role > label > placeholder > text > alt > testid > css > xpath，内置自动等待
- **双格式用例** — Excel (推荐) / YAML，零 Python 代码编写业务用例
- **数据驱动 (DDT)** — 用例模板 + 参数集 = 自动展开为多个测试实例
- **Jinja2 模板渲染** — `{{变量}}` 占位符自动替换上下文数据
- **Allure 可视化报告** — 自动截图 / AI prompt-response / 截图幻灯片回放
- **AI 智能降级** — AI 步骤失败不中断用例，降级为警告 + 截图
- **传统定位 AI 兜底** — 关键字定位失败可自动 fallback 到 AI 视觉定位 (`HAT_AI_FALLBACK`)
- **解析期验证** — Excel `操作类型` 错别字在浏览器启动前拦截

---

## 框架架构

```
main.py (CLI 入口 → argparse → pytest → Allure 报告)
  └─ HAT/plugin.py          pytest 插件 (--type, --cases, --keyDir)
       └─ HAT/parser.py      Excel/YAML 解析 → DDT 展开 → {case_infos, case_names}
            └─ HAT/runner.py  TestRunner.test_case() — pytest parametrize 每用例

HAT/
├── ai/                        AI 视觉模块
│   ├── __init__.py            AIMixin: AI操作 / AI断言 / AI执行
│   └── provider.py            AIVisionProvider Protocol + QwenVLProvider
├── keywords/
│   └── __init__.py            Keywords(AIMixin): 50+ 传统关键字 + AI 方法
├── pages/                     POM 页面对象
│   ├── base.py                BasePage: click/fill/assert 等基类方法
│   ├── login.py               reelmate.cn 登录页
│   └── video.py               reelmate.cn 视频生成页
├── locators/                  YAML 语义定位器文件
│   ├── login_page.yaml
│   └── video_page.yaml
├── utils/
│   ├── __init__.py            共享工具 (_safe_filename)
│   ├── step_logger.py         Allure 步骤上下文管理
│   └── script.py              前置/后置脚本动态执行
├── runner.py                  TestRunner: 五分类 dispatch + 用例生命周期
├── parser.py                  用例解析 + DDT + 操作类型验证
├── browser.py                 BrowserManager: Playwright 浏览器生命周期
├── config.py                  Config 单例: 全局上下文存储
├── locator.py                 LocatorBuilder: YAML → Playwright Locator
├── template.py                Jinja2 变量渲染
├── operation_types.py         操作类型注册表 (61 entries, 7 categories)
└── plugin.py                  pytest 钩子 + CasesPlugin
```

### 五级操作分类

操作类型通过 `HAT/operation_types.py` 单文件注册表统一分类和验证：

| 分类 | OpCategory | Excel 值示例 | 说明 |
|------|-----------|-------------|------|
| AI 原子操作 | `AI_ATOMIC` | `AI:操作` | 单步视觉定位 → 点击/输入/提取 |
| AI 断言 | `AI_ASSERTION` | `AI:断言` | 单步视觉判断 |
| AI 组合操作 | `AI_COMPOSITE` | `AI:执行` | 多轮 Agent 自主探索 |
| 传统操作 | `ACTION` | `点击元素`, `输入内容`, `访问网址` | 50+ 关键字方法 |
| 传统断言 | `ASSERTION` | `断言文本包含`, `断言元素存在` | 内置断言方法 |
| POM | `POM` | `LoginPage.login` | 页面对象点号调用 |
| 自定义 | `CUSTOM` | 任意 | `ex_invoke` 动态加载 |

可通过 `python main.py --list-operations` 列出全部可用操作。

---

## 快速开始

### 环境要求

- Python 3.8+
- Allure CLI ([下载](https://github.com/allure-framework/allure2/releases))

### 安装

```bash
pip install -r requirements.txt
playwright install chromium
# 安装 Allure CLI 并配置到 PATH
```

### 运行测试

```bash
# Excel 用例（推荐）
python main.py --type=excel --cases=./examples/reelmate-cases-excel

# 查看所有可用操作类型
python main.py --list-operations

# 自定义参数
python main.py --type=excel --cases=./examples/reelmate-cases-excel \
  --headless --browser=firefox --workers=4 \
  --alluredir=./test-results --report_html_path=./HTML测试报告
```

---

## 用例格式

### 目录结构

```
examples/reelmate-cases-excel/
├── context.xlsx             全局配置 (浏览器/元素/变量/数据库)
├── 1_登录模块测试.xlsx        用例文件 (按文件名数字前缀排序)
├── 2_视频模块测试.xlsx
└── ...
```

### Excel 用例 (9 列标准格式)

| 用例编号 | 模块 | 功能 | 用例标题 | 步骤 | 测试步骤 | 操作类型 | 数据内容 | 用例类型 |
|---------|------|------|---------|------|---------|---------|---------|---------|

**操作类型** 是核心字段，支持以下值：
- 传统操作: `访问网址`, `点击元素`, `输入内容`, `强制等待` 等
- 传统断言: `断言文本包含`, `断言元素存在`, `断言浏览器路径` 等
- AI 操作: `AI:操作`, `AI:断言`, `AI:执行`
- POM 方法: `LoginPage.login`, `VideoPage.select_ref_video` 等

### context.xlsx 工作表

| 工作表 | 用途 |
|--------|------|
| `浏览器配置` | browserName, 启动参数 (headless, args) |
| `WEB页面元素` | 元素名称 → 定位器类型/角色/名称/值 |
| `通用配置` | 测试变量 (base_url, username, password) + session_reuse |
| `数据库配置` | MySQL 数据库别名/连接信息 |

---

## 操作类型体系

### 查看可用操作

```bash
python main.py --list-operations
```

输出按 5 个分类分组列出所有可用操作名称。

### Excel 中区分 AI 和传统操作

通过 `操作类型` 列的值区分：

```
操作类型列:
  "访问网址"       → 蓝色 (传统操作 ACTION)
  "断言元素存在"    → 橙色 (断言 ASSERTION)
  "AI:操作"        → 绿色 (AI 操作 AI_ATOMIC)
  "AI:断言"        → 橙色 (AI 断言 AI_ASSERTION)
  "AI:执行"        → 绿色 (AI 组合 AI_COMPOSITE)
  "LoginPage.login" → POM 调用
```

框架在**解析阶段**即验证 `操作类型` 值有效性，AI 前缀错别字（如 `AI:caozuo`）会在浏览器启动前直接报错。

### API (供框架内部使用)

```python
from HAT.operation_types import categorize, is_ai, is_assertion, validate, OpCategory

categorize("AI:操作")     # → OpCategory.AI_ATOMIC
is_ai("AI:断言")          # → True
is_assertion("断言文本包含")  # → True
validate("AI:假动作")      # → (False, "Unknown AI operation: ...")
```

---

## 关键字参考

### 页面导航

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `访问网址` | 网址, 超时=30000, 等待方式=domcontentloaded | 打开 URL |
| `页面刷新` | — | 刷新页面 |
| `页面前进` | — | 浏览器前进 |
| `页面后退` | — | 浏览器后退 |

### 元素交互

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `点击元素` | _页面元素, 超时=10000, INDEX=0 | 点击 (定位失败→AI fallback) |
| `输入内容` | _页面元素, 数据内容, 超时=10000, 先清除=true | 输入 (定位失败→AI fallback) |
| `输入内容追加` | _页面元素, 数据内容 | 逐字符输入 |
| `清空输入框` | _页面元素 | 清空 |
| `鼠标悬停` | _页面元素 | hover |
| `双击元素` | _页面元素 | 双击 |
| `右键点击` | _页面元素 | 右键 |
| `滚动到元素` | _页面元素 | 滚动到可见 |
| `拖拽元素` | 源元素, 目标元素 | 拖拽 |

### 表单

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `选择下拉框选项` | _页面元素, 数据内容 | 按 label 选择 |
| `选择下拉框选项按值` | _页面元素, 数据内容 | 按 value 选择 |
| `勾选复选框` | _页面元素 | 勾选 |
| `取消勾选` | _页面元素 | 取消 |
| `上传文件` | _页面元素, 文件路径 | 上传 |

### 断言

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `断言文本` | 预期结果, 实际结果, 比较符(==/!=/in/>/</>=/<=) | 通用断言 |
| `断言文本相等` | 预期结果, 实际结果 | 相等 |
| `断言文本包含` | 预期结果, 实际结果 | 包含 |
| `断言文本不相等` | 预期结果, 实际结果 | 不等 |
| `断言数字相等` | 预期结果, 实际结果 | 数值等于 |
| `断言数字大于` | 预期结果, 实际结果 | 数值大于 |
| `断言元素存在` | _页面元素, 超时=5000 | 可见 |
| `断言元素不存在` | _页面元素, 超时=5000 | 不可见 |
| `断言浏览器路径` | 数据内容 | URL 包含 |
| `断言页面标题` | 预期结果 | 标题包含 |

### 窗口/iframe

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `iframe_switch_to` | _页面元素 | 切换到 iframe |
| `iframe_to_default_content` | — | 退出 iframe |
| `switch_to_latest_handle` | — | 切到最新标签页 |
| `switch_to_appoint_handle` | 数据内容 | 按索引切标签页 |
| `关闭当前页面` | — | 关闭当前标签 |

### 信息获取

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `获取元素文本` | _页面元素, 变量名 | 获取文本存变量 |
| `获取元素属性` | _页面元素, 属性名, 变量名 | 获取属性存变量 |
| `获取当前URL` | 变量名 | 获取 URL 存变量 |
| `获取页面标题` | 变量名 | 获取标题存变量 |

### 辅助

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `强制等待` | 数据内容 | 等待 N 秒 |
| `窗口最大化` | — | 1920×1080 |
| `键盘按键` | 数据内容 | e.g. "Enter" |
| `滚动页面` | X, Y | 像素滚动 |
| `执行JS` | 数据内容, 变量名 | eval JS |
| `接受弹窗` | — | dialog.accept() |
| `取消弹窗` | — | dialog.dismiss() |
| `获取弹窗文本` | 变量名 | 获取 dialog message |
| `store_text` | 变量名, 变量值 | 存变量 |
| `random_six_digit_number` | 变量名 | 6 位随机数 |
| `提取数据MYSQL` | _数据库, SQL, 变量名 | MySQL 查询 |
| `image_recognition` | _页面元素, 引用变量 | ddddocr 验证码识别 |
| `ex_invoke` | key, step_value | 自定义关键字动态加载 |

### AI 操作

| 操作类型 | 数据内容参数 | 说明 |
|---------|-------------|------|
| `AI:操作` | 操作描述 | AI 视觉定位 → 点击/输入/提取 |
| `AI:断言` | 操作描述 | AI 视觉判断通过/失败 |
| `AI:执行` | 操作描述, 最大步数=5 | 多轮 AI Agent 自主完成任务 |

---

## POM 页面对象

### 用法

POM 模式通过 `操作类型` 的点分表示法调用：

```
操作类型: LoginPage.login
数据内容: username=18318053665 password=qq111111
```

TestRunner 在运行时实例化并注册所有页面对象（见 `_init_pages()`），通过 `操作类型` 解析类名和方法名后执行。

### LoginPage

| 方法 | 参数 | 说明 |
|------|------|------|
| `navigate_to_login` | — | 打开首页→点登录入口→切换到密码登录 tab |
| `login` | username, password | 完整登录流程 (填充→同意→提交→等待) |
| `enter_username` | username | 输入用户名 |
| `enter_password` | password | 输入密码 |
| `click_login_button` | — | 点登录按钮 |
| `clear_username` / `clear_password` | — | 清空输入框 |
| `agree_to_terms` | — | 勾选同意协议 |
| `verify_login_page_elements` | — | 断言用户名/密码/登录按钮可见 |
| `verify_login_success` | login_url | 断言已离开登录页 |
| `verify_login_failed` | login_url | 断言仍停留在登录页 |
| `get_error_message` | timeout | 获取错误提示文本 |
| `is_on_login_page` / `is_logged_in` | — | 状态检查 |

### VideoPage

| 方法 | 参数 | 说明 |
|------|------|------|
| `navigate_to_video` | — | 打开视频页 |
| `select_ref_video` | — | 选择"参考生视频"tab |
| `select_multi_grid` | — | 选择多宫格模式 |
| `select_tgi2` | — | 选择 TGI2 模型 |
| `open_video_model_dropdown` | — | 打开模型下拉框 |
| `verify_seedance_option` | — | 验证下拉框有 Seedance 2.0VIP |

### 自定义页面对象

1. 在 `HAT/pages/` 创建 `my_page.py` 继承 `BasePage`
2. 创建 `HAT/locators/my_page.yaml` 定义元素定位器
3. 在 `TestRunner._init_pages()` 注册

---

## AI 视觉操作

### 配置

```bash
# 必需环境变量
HAT_LLM_API_KEY=sk-xxx          # API 密钥
HAT_LLM_BASE_URL=https://...     # API 地址 (OpenAI 兼容)
HAT_LLM_MODEL_NAME=qwen-vl-max   # 模型名称

# 可选
HAT_LLM_TIMEOUT=60               # 请求超时 (默认 60s)
HAT_LLM_MAX_RETRIES=2            # 重试次数 (默认 2)
HAT_AI_FALLBACK=true             # 传统定位失败自动 AI fallback (默认 true)
```

### 三种 AI 操作类型

```
AI:操作  — 截图→视觉模型→bbox→Playwright 点击/输入/提取 (单步)
AI:断言  — 截图→视觉模型→判断真/假 (单步)
AI:执行  — 自然语言目标→多轮 Agent 循环→直到完成/超步数 (多步)
```

### AI 降级策略

所有 AI 操作方法 (`AI操作`, `AI断言`, `AI执行`) 内部包装了 try/except，运行时异常**不中断用例**：
- 异常 → `logger.warning()` + Allure 附件 (错误信息)
- 配置错误 (缺 API Key / Model Name) → 硬错误，直接抛出中断

### 传统定位 AI Fallback

`点击元素` 和 `输入内容` 在传统定位器失败时，检查 `HAT_AI_FALLBACK` 环境变量：
- `true` (默认) → 自动降级调用 `AI操作()`
- `false` → 直接抛出原始异常

### 扩展 AI Provider

实现 `AIVisionProvider` Protocol 以支持不同 AI 厂商：

```python
from HAT.ai.provider import AIVisionProvider

class MyProvider:
    def resize(self, width: int, height: int) -> tuple[int, int]:
        return width, height  # 不缩放
    def get_min_max_pixels(self) -> tuple[int, int]:
        return 256*28*28, 2048*28*28
```

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HAT_LOG_LEVEL` | 日志级别 | INFO |
| `HAT_HEADLESS` | 无头模式 (`true`/`false`) | false |
| `HAT_BROWSER` | 浏览器 (chromium/firefox/webkit) | chromium |
| `HAT_LLM_API_KEY` | AI 视觉 API Key | — |
| `HAT_LLM_BASE_URL` | AI 视觉 API 地址 | — |
| `HAT_LLM_MODEL_NAME` | AI 视觉模型名 | — |
| `HAT_LLM_TIMEOUT` | AI 请求超时 (秒) | 60 |
| `HAT_LLM_MAX_RETRIES` | AI 请求重试次数 | 2 |
| `HAT_AI_FALLBACK` | 传统定位 AI 自动降级 | true |

### context.yaml 示例

```yaml
session_reuse: false

base_url: "https://www.reelmate.cn"
username: "18318053665"
password: "qq111111"
```

### context.xlsx

| 工作表 | 列 | 说明 |
|--------|---|------|
| 浏览器配置 | 浏览器名称, 启动参数(JSON) | `{"headless": false, "args": []}` |
| WEB页面元素 | 元素名称, 定位器类型, 角色, 名称, 值, Frame | Playwright 语义定位器定义 |
| 通用配置 | 配置名, 配置值 | `base_url`/`username`/`password`/`session_reuse` |
| 数据库配置 | 别名, 服务器IP, 端口号, 用户名, 密码, 数据库名称 | MySQL 连接信息 |

---

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--type` | 用例格式: excel \| yaml | excel |
| `--cases` | 用例目录 | examples/reelmate-cases-excel |
| `--keyDir` | 自定义关键字目录 | — |
| `--headless` | 无头模式 | false |
| `--browser` | 浏览器: chromium/firefox/webkit | chromium |
| `--workers` | 并行 workers (需 pytest-xdist) | 1 |
| `--alluredir` | Allure 结果目录 | ./test-results |
| `--report_html_path` | HTML 报告输出目录 | ./HTML测试报告 |
| `--list-operations` | 列出所有可用操作类型 (不执行测试) | — |
| `--version` | 打印版本号 | — |

---

## 项目版本

**v2026.5.0** — Playwright + pytest + DDT + POM + Allure + AI 混合框架。
