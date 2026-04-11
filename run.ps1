# 华测教育自动化测试运行脚本
# 修复中文乱码并运行测试

# 设置控制台编码为 UTF-8
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 运行项目
$PYTHON = "e:\CODE\web_auto\venv\Scripts\python.exe"

if ($args.Count -eq 0) {
    Write-Host "用法: .\run.ps1 [--type=yaml|excel] [--cases=路径]" -ForegroundColor Cyan
    Write-Host "示例: .\run.ps1 --type=yaml --cases=./examples/web-cases-yaml" -ForegroundColor Cyan
    exit
}

& $PYTHON main.py @args
