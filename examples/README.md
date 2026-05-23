# HAT 测试用例示例

## 目录

| 目录 | 格式 | 说明 |
|------|------|------|
| `reelmate-cases-excel/` | Excel | 核心示例：关键字/POM/AI混合用例 |
| `reelmate-cases/` | YAML | YAML格式登录+Web用例 |
| `pom-login-test/` | YAML | POM模式最小示例 |
| `web-cases-ai/` | YAML | AI驱动用例示例 |
| `web-test-cases/` | Excel | Excel关键字驱动示例 |

## 运行

```bash
# Excel 用例
python main.py --type=excel --cases=./examples/reelmate-cases-excel

# YAML 用例
python main.py --type=yaml --cases=./examples/reelmate-cases

# 指定报告目录
python main.py --type=excel --cases=./examples/reelmate-cases-excel --alluredir=./results --report_html_path=./reports
```

## 操作类型

| 类型 | 格式 | 说明 |
|------|------|------|
| 关键字 | `点击元素` `输入内容` `断言文本包含` | 传统关键字驱动 |
| POM | `LoginPage.login` `LoginPage.navigate_to_login` | Page Object Model |
| AI原子 | `AI:操作` `AI:断言` | 单个AI视觉操作/断言 |
| AI组合 | `AI:执行` | 多轮AI代理,自然语言描述目标 |

## 用例格式 (Excel)

列: 用例编号 | 模块 | 功能 | 用例标题 | 步骤 | 测试步骤 | 操作类型 | 数据内容 | 用例类型

- **数据内容列** 支持 `key=value` 格式, 支持 `{{变量}}` Jinja2模板
- 多组数据驱动需在 Sheet2 "数据驱动" 中定义参数集

## context 配置

`context.xlsx` (或 `context.yaml`) 中配置:
- `_浏览器` — browser类型/chromium/firefox/webkit, headless, args
- `session_reuse` — 是否跨用例复用浏览器
- `_WEB页面元素` — 关键字模式的元素定位器注册表
- 测试变量: `base_url` `username` `password` 等

### AI 配置 (环境变量)

| 变量 | 说明 |
|------|------|
| `HAT_LLM_API_KEY` | AI视觉模型API Key (必填) |
| `HAT_LLM_BASE_URL` | API Base URL |
| `HAT_LLM_MODEL_NAME` | 模型名称 (必填) |
| `HAT_LLM_TIMEOUT` | 超时秒数 (默认60) |
| `HAT_LLM_MAX_RETRIES` | 最大重试 (默认2) |
| `HAT_AI_FALLBACK` | 传统定位失败时AI兜底 (默认true) |
