# ============================================================
# HAT 快速入门模板 — 使用说明
# ============================================================

## 运行此模板

在项目根目录执行:

```bash
# Windows PowerShell
.\run.ps1 yaml quickstart-template

# 或直接使用 Python
python main.py --type=yaml --cases=./examples/quickstart-template
```

## 目录结构

```
quickstart-template/
  ├── context.yaml        # 全局配置（浏览器 + 页面元素 + 测试变量）
  ├── 1_百度搜索测试.yaml   # 用例文件（以数字开头，按数字排序）
  └── README.txt          # 本说明文件
```

## 如何适配到你的项目？

### 第1步: 修改 context.yaml

```yaml
# 1. 修改测试地址
base_url: "https://你的测试网站地址.com"

# 2. 修改测试账号
username: "你的测试账号"
password: "你的测试密码"

# 3. 添加你的页面元素
_WEB页面元素:
  登录按钮:
    定位方式: text           # 定位方式: text / placeholder / role / css / xpath
    目标对象: "登录"         # 定位目标

  用户名输入框:
    定位方式: placeholder
    目标对象: "请输入用户名"
```

### 第2步: 复制用例文件

- 复制 `1_百度搜索测试.yaml` → `2_你的新用例.yaml`
- 修改 `基础配置` 和 `用例步骤`

### 第3步: 运行

```bash
python main.py --type=yaml --cases=./examples/quickstart-template
```

## 常用操作类型速查

| 操作类型 | 说明 | 常用参数 |
|---------|------|---------|
| 访问网址 | 打开URL | 网址, 等待方式 |
| 点击元素 | 点击元素 | _页面元素 |
| 输入内容 | 输入文字 | _页面元素, 数据内容 |
| 强制等待 | 暂停N秒 | 数据内容 |
| 断言文本包含 | 验证包含 | 预期结果, 实际结果, 错误信息 |
| 断言文本相等 | 验证相等 | 预期结果, 实际结果 |
| 断言元素存在 | 验证可见 | _页面元素 |
| 获取当前URL | 获取URL | 变量名 |
| 获取页面标题 | 获取标题 | 变量名 |
| 获取元素文本 | 获取文本 | _页面元素, 变量名 |

## 下一步

1. 阅读完整文档: docs/QUICKSTART.md
2. 查看 POM 示例: examples/pom-login-test/
3. 查看 Excel 示例: examples/reelmate-cases-excel/
