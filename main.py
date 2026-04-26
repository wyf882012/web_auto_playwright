# -*- coding: utf-8 -*-
"""
HAT 混合型企业级自动化测试框架 —— 入口文件
==============================================

运行方式:
  # Excel 用例模式
  python main.py --type=excel --cases=./examples/reelmate-cases-excel

  # YAML 用例模式
  python main.py --type=yaml --cases=./examples/reelmate-cases

  # 指定 Allure 报告输出路径
  python main.py --type=excel --cases=./examples/reelmate-cases-excel --alluredir=./test-results --report_html_path=./HTML测试报告

架构说明:
  命令行参数 -> CasesPlugin(解析用例) -> TestRunner(执行用例) -> Keywords(操作浏览器)
                                -> Allure 报告生成
"""
import os
import shutil
import sys
import time
import subprocess
import pytest
import argparse
from _pytest.config import ExitCode

from HAT.core.CasesPlugin import CasesPlugin
from loguru import logger
from HAT.extend.allure_combine.combine import combine_allure

# ---- 修复 Windows 控制台中文乱码 ----
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ---- 日志配置 ----
if not os.path.exists("logs"):
    os.mkdir("logs")
log_level = os.getenv("HAT_LOG_LEVEL", "INFO").upper()
time_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
logger.configure(
    handlers=[
        {"sink": sys.stdout, "level": "WARNING"},  # 控制台只输出 WARNING 及以上
        {"sink": os.path.join("./logs", f"hat_{time_str}.log"), "level": log_level},  # 文件记录完整日志
    ]
)


def parse_args():
    """
    解析命令行参数。

    :return: 包含测试类型、用例路径、报告路径等配置的命名空间对象
    """
    parser = argparse.ArgumentParser(description="HAT 自动化测试工具 (Playwright版)")
    parser.add_argument("--version", action="version", version="v2026.4-playwright")
    parser.add_argument("--type", type=str, default="yaml", help="用例类型: yaml | excel", required=False)
    parser.add_argument("--cases", type=str, default="examples/web-cases-yaml", help="测试用例文件夹路径", required=False)
    parser.add_argument("--keyDir", type=str, help="扩展关键字代码文件夹路径", required=False)
    parser.add_argument("--alluredir", type=str, default=os.path.join(os.getcwd(), "test-results"),
                        help="Allure 结果数据保存路径", required=False)
    parser.add_argument("--report_html_path", type=str, default=os.path.join(os.getcwd(), "HTML测试报告"),
                        help="HTML 测试报告输出路径", required=False)
    return parser.parse_args()


cmd_args = parse_args()


def run():
    """
    自动化测试主运行函数。

    流程:
      1. 解析命令行参数，转换为 pytest 兼容格式
      2. 检查必备依赖（allure-pytest、allure CLI 工具）
      3. 调用 pytest 执行测试（CasesPlugin 负责动态生成用例数据）
      4. 生成 Allure 可视化 HTML 报告
      5. 自动打开浏览器展示报告
    """
    print("###############################################")
    print("######## HAT 自动化测试工具 (Playwright版) ########")
    print("########     版本 v2026.4.playwright     ########")
    print("################################################")

    # 1. 构建 pytest 命令行参数
    pytest_args = ["-v", "--no-header", "-s", "--clean-alluredir", "-W", "ignore"]
    if cmd_args.type:
        pytest_args.append(f"--type={cmd_args.type}")
    if cmd_args.cases:
        pytest_args.append(f"--cases={cmd_args.cases}")
    if cmd_args.keyDir:
        pytest_args.append(f"--keyDir={cmd_args.keyDir}")
    if cmd_args.alluredir:
        pytest_args.append(f"--alluredir={cmd_args.alluredir}")

    # 指定 TestRunner 作为 pytest 测试目标
    import HAT.core.TestRunner as TestRunner
    if TestRunner.__file__:
        pytest_args.append(TestRunner.__file__)

    # 2. 环境检查
    logger.info("######## 开始环境检查 ########")
    logger.info("1. 检查 allure-pytest 是否存在")
    from allure_pytest import plugin as allure_plugin
    logger.info(f"   allure-pytest 加载成功: {allure_plugin}")

    logger.info("2. 检查 allure CLI 工具")
    if shutil.which("allure") is not None:
        logger.info("   allure CLI 检查通过")
    else:
        logger.error("请确保已安装 allure 命令行工具并配置到环境变量 PATH 中")
        logger.error("下载地址: https://github.com/allure-framework/allure2/releases")
        sys.exit(1)

    # 3. 执行测试
    exit_code = pytest.main(pytest_args, plugins=[CasesPlugin()])
    print("测试执行完毕，开始生成测试报告...")

    # 4. 生成 Allure 报告
    if ExitCode.OK == exit_code or ExitCode.TESTS_FAILED == exit_code:
        try:
            # 调用 allure CLI 生成报告
            subprocess.check_output(
                f"allure generate --lang zh {cmd_args.alluredir} -c -o {cmd_args.report_html_path}",
                shell=True, universal_newlines=True,
            )
            # 合并并美化报告（单文件 HTML）
            combine_allure(cmd_args.report_html_path)
            # 自动打开浏览器查看报告
            import webbrowser
            webbrowser.open(os.path.join(cmd_args.report_html_path, "report.html"))
        except subprocess.CalledProcessError as e:
            logger.exception(e)
            logger.error(f"生成测试报告失败！{e}")
    else:
        if ExitCode.NO_TESTS_COLLECTED == exit_code:
            logger.error("没有发现任何测试用例，请检查 --cases 路径是否正确")
        else:
            logger.error("测试用例执行失败！")
    print("##################### 执行结束 ##########################")


if __name__ == "__main__":
    run()
