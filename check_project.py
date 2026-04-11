# -*- coding: utf-8 -*-
"""
项目健康检查脚本
用于验证依赖安装、模块导入和基本功能
"""
import sys
import os

print("=" * 60)
print("开始项目健康检查...")
print("=" * 60)

# 1. 检查 Python 版本
print("\n[1/6] 检查 Python 版本...")
print(f"Python 版本: {sys.version}")
if sys.version_info < (3, 8):
    print("❌ 错误: Python 版本需要 >= 3.8")
    sys.exit(1)
else:
    print("✅ Python 版本检查通过")

# 2. 检查核心依赖
print("\n[2/6] 检查核心依赖...")
required_packages = [
    'pytest',
    'selenium',
    'allure_pytest',
    'pandas',
    'yaml',  # PyYAML 的导入名称
    'loguru',
    'openpyxl',
    'tqdm',
    'ddddocr',
    'pymysql'
]

missing_packages = []
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print(f"  ✅ {package}")
    except ImportError as e:
        print(f"  ❌ {package} - 未安装")
        missing_packages.append(package)

if missing_packages:
    print(f"\n❌ 缺少以下依赖包: {', '.join(missing_packages)}")
    print("请运行: pip install -r requeirement.txt")
    sys.exit(1)
else:
    print("✅ 所有核心依赖已安装")

# 3. 检查项目模块导入
print("\n[3/6] 检查项目模块导入...")
try:
    from HAT.core.globalContext import g_context
    print("  ✅ HAT.core.globalContext")
    
    from HAT.core.CasesPlugin import CasesPlugin
    print("  ✅ HAT.core.CasesPlugin")
    
    from HAT.parse.caseParser import case_parser
    print("  ✅ HAT.parse.caseParser")
    
    from HAT.keywords.web_keywords import Keywords
    print("  ✅ HAT.keywords.web_keywords")
    
    from HAT.context.WebCaseContext import WebCaseContext
    print("  ✅ HAT.context.WebCaseContext")
    
    from HAT.extend.allure_combine.combine import combine_allure
    print("  ✅ HAT.extend.allure_combine.combine")
    
    print("✅ 所有项目模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

# 4. 检查测试用例文件
print("\n[4/6] 检查测试用例文件...")
yaml_cases_dir = os.path.join(os.getcwd(), "examples", "web-cases-yaml")
if os.path.exists(yaml_cases_dir):
    yaml_files = [f for f in os.listdir(yaml_cases_dir) if f.endswith('.yaml')]
    print(f"  找到 {len(yaml_files)} 个 YAML 测试用例文件")
    for f in yaml_files:
        print(f"    - {f}")
    print("✅ YAML 测试用例目录存在")
else:
    print(f"⚠️  YAML 测试用例目录不存在: {yaml_cases_dir}")

excel_cases_dir = os.path.join(os.getcwd(), "examples", "web-cases-excel")
if os.path.exists(excel_cases_dir):
    excel_files = [f for f in os.listdir(excel_cases_dir) if f.endswith('.xlsx')]
    print(f"  找到 {len(excel_files)} 个 Excel 测试用例文件")
    for f in excel_files:
        print(f"    - {f}")
    print("✅ Excel 测试用例目录存在")
else:
    print(f"⚠️  Excel 测试用例目录不存在: {excel_cases_dir}")

# 5. 检查 Allure 工具
print("\n[5/6] 检查 Allure 工具...")
import shutil
if shutil.which("allure") is not None:
    print("✅ Allure 工具已安装并配置到环境变量")
else:
    print("⚠️  Allure 工具未找到，请确保已安装并配置环境变量")
    print("   下载地址: https://github.com/allure-framework/allure2/releases")

# 6. 检查全局上下文功能
print("\n[6/6] 检查全局上下文功能...")
try:
    ctx = g_context()
    ctx.set_dict("test_key", "test_value")
    value = ctx.get_dict("test_key")
    if value == "test_value":
        print("✅ 全局上下文功能正常")
    else:
        print("❌ 全局上下文功能异常")
        sys.exit(1)
except Exception as e:
    print(f"❌ 全局上下文测试失败: {e}")
    sys.exit(1)

# 总结
print("\n" + "=" * 60)
print("✅ 项目健康检查完成！所有检查项通过")
print("=" * 60)
print("\n提示:")
print("1. 如需运行测试，请使用命令:")
print("   python main.py --type=yaml --cases=examples/web-cases-yaml")
print("2. 或运行 Excel 测试:")
print("   python main.py --type=excel --cases=examples/web-cases-excel")
print("3. 确保已安装浏览器驱动（ChromeDriver 等）")
print("=" * 60)
