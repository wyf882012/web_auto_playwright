# HAT 自动化测试框架运行脚本 (Playwright版)
# 用法:
#   .\run.ps1                                    → 默认运行 reelmate 登录模块测试(Excel)
#   .\run.ps1 --type=yaml                         → 使用 YAML 格式
#   .\run.ps1 --type=excel --cases=./examples/reelmate-cases-excel
#
# 首次使用请确保:
#   1. pip install playwright
#   2. playwright install chromium

chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$PYTHON = "e:\CODE\web_auto\venv\Scripts\python.exe"

if ($args.Count -eq 0) {
    # 默认运行 reelmate.cn 登录模块 Excel 测试
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " 自动化测试工具 (Playwright版)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法: .\run.ps1 [--type=yaml|excel] [--cases=路径]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Green
    Write-Host "  .\run.ps1 --type=excel --cases=./examples/reelmate-cases-excel   # Excel用例(推荐)" -ForegroundColor White
    Write-Host "  .\run.ps1 --type=yaml --cases=./examples/reelmate-cases          # YAML用例" -ForegroundColor White
    exit
}

& $PYTHON main.py @args
