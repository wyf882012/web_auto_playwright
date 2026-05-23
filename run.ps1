# HAT 自动化测试框架运行脚本 (Playwright版)
# =============================================
# 用法:
#   .\run.ps1                                    → 显示帮助
#   .\run.ps1 excel                               → Excel 模式运行默认用例
#   .\run.ps1 yaml                                → YAML 模式运行默认用例
#   .\run.ps1 excel reelmate-cases-excel         → 指定用例目录
#   .\run.ps1 yaml pom-login-test                → POM 模式示例
#
# 首次使用请确保:
#   1. pip install -r requirements.txt
#   2. playwright install chromium
#   3. 安装 Allure CLI: https://github.com/allure-framework/allure2/releases

chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 自动查找 Python 解释器
$PYTHON = $null
# 1) 优先使用当前目录下的 venv
if (Test-Path ".\venv\Scripts\python.exe") {
    $PYTHON = ".\venv\Scripts\python.exe"
}
elseif (Test-Path ".\\.venv\\Scripts\\python.exe") {
    $PYTHON = ".\.venv\Scripts\python.exe"
}
# 2) 回退到系统 PATH 中的 python
else {
    $PYTHON = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PYTHON) {
    Write-Host "[错误] 未找到 Python 解释器！请安装 Python 3.8+ 或创建虚拟环境。" -ForegroundColor Red
    exit 1
}
Write-Host "[信息] 使用 Python: $PYTHON" -ForegroundColor DarkGray

# 默认配置
$TYPE = "excel"
$CASES = "./examples/reelmate-cases-excel"

# 解析参数
if ($args.Count -ge 1) {
    # 第一个参数: 用例类型 (excel / yaml)
    $arg1 = $args[0].ToLower()
    if ($arg1 -eq "yaml" -or $arg1 -eq "excel") {
        $TYPE = $arg1
    }
    else {
        Write-Host "[提示] 第一个参数应为 yaml 或 excel，将使用默认: $TYPE" -ForegroundColor Yellow
    }
}
if ($args.Count -ge 2) {
    # 第二个参数: 用例目录名 (在 examples/ 下)
    $CASES = "./examples/$($args[1])"
}
if ($args[0] -eq "--help" -or $args[0] -eq "-h" -or $args[0] -eq "help") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " HAT 自动化测试工具 (Playwright版)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法: .\run.ps1 [类型] [用例目录]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "参数:" -ForegroundColor Green
    Write-Host "  类型       yaml 或 excel（默认: excel）" -ForegroundColor White
    Write-Host "  用例目录   examples/ 下的子目录名（默认: reelmate-cases-excel）" -ForegroundColor White
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Green
    Write-Host "  .\run.ps1                                    # 默认 Excel 模式" -ForegroundColor White
    Write-Host "  .\run.ps1 yaml                               # YAML 模式" -ForegroundColor White
    Write-Host "  .\run.ps1 excel reelmate-cases-excel         # 指定用例目录" -ForegroundColor White
    Write-Host "  .\run.ps1 yaml pom-login-test                # POM 模式示例" -ForegroundColor White
    Write-Host "  .\run.ps1 yaml quickstart-template           # 新手模板" -ForegroundColor White
    Write-Host ""
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " HAT 自动化测试工具 (Playwright版)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  类型: $TYPE" -ForegroundColor White
Write-Host "  用例: $CASES" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

& $PYTHON main.py --type=$TYPE --cases=$CASES
