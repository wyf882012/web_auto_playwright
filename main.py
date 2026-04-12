# -*- coding: utf-8 -*-
import os, shutil, sys, time
import subprocess
import pytest
import argparse
from _pytest.config import ExitCode

from HAT.core.CasesPlugin import CasesPlugin
### 日志配置
from loguru import logger

from HAT.extend.allure_combine.combine import combine_allure

# 修复 Windows 控制台中文乱码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 创建 logs 文件夹
if not os.path.exists("logs"):
    os.mkdir("logs")
log_level = os.getenv('HAT_LOG_LEVEL', "INFO").upper()
# 获取当前时间 字符串格式
time_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
logger.configure(
    handlers=[
        {"sink": sys.stdout,"level": "WARNING"},# 控制台输出
        {"sink": os.path.join("./logs",f"hat_{time_str}.log"),"level": log_level},# 日志文件
    ]
)
#### 日志配置end
def parse_args():
    """
    解析命令行参数。
    
    :return: 包含测试类型、用例路径等配置的命名空间对象
    """
    parser = argparse.ArgumentParser(description="自动化测试工具。")
    parser.add_argument('--version', action="version", version="v202507.1")
    parser.add_argument('--type', type=str, default='yaml', help='测试用例类型: yaml | excel', required=False)
    parser.add_argument('--cases', type=str, default='examples/web-cases-yaml',help='指定测试用例的文件夹路径.', required=False)
    parser.add_argument('--keyDir', type=str, help='拓展关键字代码文件夹路径.', required=False)
    parser.add_argument('--alluredir', type=str,default=os.path.join(os.getcwd(),"test-results"), help='文件夹路径，用于保存测试执行后的结果数据.', required=False)
    parser.add_argument('--report_html_path', type=str,default=os.path.join(os.getcwd(),"HTML测试报告"), help='HTML测试报告的保存位置.', required=False)
    args_result = parser.parse_args() # 解析参数
    return args_result
    print(args_result)
cmd_args = parse_args()

def run():
    """
    自动化测试主运行函数。
    
    负责环境检查、调用 pytest 执行测试以及生成 Allure 可视化报告。
    """
    print(f"###############################################")
    print(f"######## 自动化测试工具(版本v2026.4) ########")
    print(f"################################################")
    # 1. 读取命令行传入的参数，转换为 pytest 兼容的写法
    pytest_args = ["-v","--no-header","-s","--clean-alluredir", "-W", "ignore"]
    if cmd_args.type: pytest_args.append(f"--type={cmd_args.type}")
    if cmd_args.cases: pytest_args.append(f"--cases={cmd_args.cases}")
    if cmd_args.keyDir: pytest_args.append(f"--keyDir={cmd_args.keyDir}")
    if cmd_args.alluredir: pytest_args.append(f"--alluredir={cmd_args.alluredir}")
    import HAT.core.TestRunner as TestRunner
    if TestRunner.__file__:
        pytest_args.append(TestRunner.__file__)

    # 2. 检查必备依赖
    logger.info(f"########开始环境检查#######")
    logger.info(f"1. 检查allure-pytest是否存在")
    from allure_pytest import plugin as allure_plugin
    logger.info(f"allure-pytest加载成功{allure_plugin}")

    logger.info(f"2. 检查当前环境中是否存在 allure 工具")
    if shutil.which("allure") is not None:
        logger.info(f"allure 检查通过")
    else:
        logger.error(f"请确保您的计算机中已安装 allure，并配置环境变量")
        sys.exit(1)

    # 3. 运行pytest
    exit_code = pytest.main(pytest_args, plugins=[ CasesPlugin()])
    print("测试结束，开始生成测试报告...")
    # 4. 执行结果
    if ExitCode.OK == exit_code or ExitCode.TESTS_FAILED == exit_code:
        try:
            # 集成 allure 示例
            subprocess.check_output(f"allure generate --lang zh {cmd_args.alluredir}  -c -o {cmd_args.report_html_path}",
                                             shell=True, universal_newlines=True)
            # 合并 allure 报告
            combine_allure(cmd_args.report_html_path)
            # 调用浏览器 打开测试报告
            import webbrowser
            webbrowser.open(os.path.join(cmd_args.report_html_path, "report.html"))
        except subprocess.CalledProcessError as e:
            logger.exception(e)
            logger.error(f"测试报告出现问题！{e}")
    else:
        if ExitCode.NO_TESTS_COLLECTED == exit_code:
            logger.error("没有发现任何测试用例！")
        else:
            logger.error("测试用例执行失败！")
    print(f"##################### 执行结束 ##########################")

if __name__ == '__main__':
    run()

# huace-test --type=yaml --cases=D:\huace_ai_project\exe_webproject\examples\web-cases-yaml