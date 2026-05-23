# -*- coding: utf-8 -*-
"""Playwright CLI 模式演示：百度搜索 "AI测试" 全流程"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    # 启动浏览器（有头模式，可以看到操作过程）
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(locale="zh-CN")
    page = context.new_page()

    print("[1] 打开百度首页...")
    page.goto("https://www.baidu.com", wait_until="domcontentloaded")
    time.sleep(1)

    print("[2] 输入搜索关键词: AI测试")
    page.fill("#kw", "AI测试")

    print("[3] 点击搜索按钮")
    page.click("#su")

    print("[4] 等待搜索结果加载...")
    page.wait_for_selector("#content_left", timeout=10000)
    time.sleep(1)

    # 提取标题验证
    title = page.title()
    print(f"[5] 当前页面标题: {title}")
    assert "AI测试" in title, f"标题未包含搜索关键词"
    print("[OK] 搜索成功！")

    # 截图保存
    page.screenshot(path="demo_result.png", full_page=True)
    print("[6] 截图已保存: demo_result.png")

    time.sleep(2)
    browser.close()
    print("[Done] 测试完成")
