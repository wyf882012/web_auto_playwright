# -*- coding: utf-8 -*-
"""
自动生成 reelmate.cn (万兴剧厂) 登录模块 Excel 测试用例

使用 Playwright 原生选择器引擎（优先级从高到低）:
  text        — 文本精确匹配，最简洁
  placeholder — 占位符文本匹配
  role        — 语义角色定位
  testid      — data-testid 属性
  css         — CSS 选择器
  xpath       — 兜底方案
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_context_xlsx():
    """
    创建 context.xlsx 配置文件，包含:
      - 浏览器配置页签
      - WEB页面元素页签（使用 Playwright 原生选择器）
      - 通用配置页签
    """
    wb = Workbook()

    # ===== Sheet 1: 浏览器配置 =====
    ws = wb.active
    ws.title = "浏览器配置"
    ws.append(["浏览器名称", "Grid服务器地址(二选一)", "本地驱动地址(二选一)", "启动参数"])
    ws.append(["chromium", "", "", '{"browserName": "chromium"}'])
    # 设置列宽
    for i, w in enumerate([14, 22, 22, 30], 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # ===== Sheet 2: WEB页面元素（Playwright 原生选择器）=====
    ws2 = wb.create_sheet("WEB页面元素")
    ws2.append(["元素名称", "定位方式", "目标对象"])
    elements = [
        # ---- 首页登录入口: text 选择器 ----
        ["登录入口按钮", "text", "登录"],

        # ---- 登录页表单: css 选择器组合 ----
        # Playwright 支持 CSS 逗号分隔的多选择器，按顺序匹配第一个可见的
        ["用户名输入框", "css",
         'input[type="email"], input[name="email"], input[name="username"], input[type="text"][placeholder*="邮箱"], input[type="text"][placeholder*="账号"]'],
        ["密码输入框", "css", 'input[type="password"]'],
        ["登录提交按钮", "css",
         'button[type="submit"], input[type="submit"], button:has-text("登录"), button:has-text("登錄")'],
        ["登录错误提示", "css", '[class*="error"], [class*="alert"], [class*="message"]'],
        ["用户头像或昵称", "css", '[class*="avatar"], [class*="user"]'],
    ]
    for row in elements:
        ws2.append(row)
    ws2.column_dimensions["A"].width = 16
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 70

    # ===== Sheet 3: 通用配置 =====
    ws3 = wb.create_sheet("通用配置")
    ws3.append(["配置名", "配置值"])
    configs = [
        ["session_reuse", "false"],
        ["username", "18318053665"],
        ["password", "qq111111"],
        ["base_url", "https://www.reelmate.cn"],
        ["login_url", "https://accounts.wondershare.cn/login"],
    ]
    for row in configs:
        ws3.append(row)
    ws3.column_dimensions["A"].width = 16
    ws3.column_dimensions["B"].width = 44

    path = os.path.join(OUT_DIR, "context.xlsx")
    wb.save(path)
    print(f"[OK] 已生成 context.xlsx")


def create_case_xlsx():
    """
    创建登录模块测试用例 Excel (1_登录模块测试.xlsx)

    用例列表:
      1. 登录页面元素完整性验证
      2. 正确账号密码登录成功
      3. 错误密码登录失败
      4. 空账号校验
      5. 空密码校验
      6. 格式错误账号校验
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "登录模块测试"

    # ---------- 表头样式 ----------
    headers = ["模块", "功能", "用例标题", "用例类型", "测试步骤", "操作类型", "数据内容"]
    header_font = Font(bold=True, color="FFFFFF", size=11, name="微软雅黑")
    header_fill = PatternFill("solid", fgColor="4472C4")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    # ---------- 用例数据 ----------
    cases = [
        # ==============================
        # 用例1: 登录页面元素验证
        # ==============================
        ("登录模块", "登录页面", "TC001-登录页面元素完整性验证", "WebCase", [
            ("访问首页", "访问网址", '网址="https://www.reelmate.cn" 等待方式="load"'),
            ("等待页面渲染完成", "强制等待", '数据内容="3"'),
            ("点击登录入口按钮", "点击元素", '_页面元素="登录入口按钮"'),
            ("等待登录页加载", "强制等待", '数据内容="3"'),
            ("验证用户名输入框存在", "断言元素存在", '_页面元素="用户名输入框" 超时="10000"'),
            ("验证密码输入框存在", "断言元素存在", '_页面元素="密码输入框"'),
            ("验证登录按钮存在", "断言元素存在", '_页面元素="登录提交按钮"'),
        ]),
        # ==============================
        # 用例2: 正确账号登录成功
        # ==============================
        ("登录模块", "登录功能", "TC002-正确账号密码登录成功", "WebCase", [
            ("访问首页", "访问网址", '网址="https://www.reelmate.cn" 等待方式="load"'),
            ("等待页面渲染完成", "强制等待", '数据内容="3"'),
            ("点击登录入口按钮", "点击元素", '_页面元素="登录入口按钮"'),
            ("等待登录页加载", "强制等待", '数据内容="3"'),
            ("输入正确的账号", "输入内容", '数据内容="18318053665" _页面元素="用户名输入框"'),
            ("输入正确的密码", "输入内容", '数据内容="qq111111" _页面元素="密码输入框"'),
            ("点击登录按钮提交", "点击元素", '_页面元素="登录提交按钮"'),
            ("等待登录响应与跳转", "强制等待", '数据内容="5"'),
            ("获取登录后当前URL", "获取当前URL", '变量名="after_login_url"'),
            ("验证已离开登录页面", "断言文本不相等",
             '预期结果="https://accounts.wondershare.cn/login" 实际结果="{{after_login_url}}" 错误信息="登录失败-仍在登录页面"'),
        ]),
        # ==============================
        # 用例3: 错误密码登录失败
        # ==============================
        ("登录模块", "登录功能", "TC003-错误密码登录失败", "WebCase", [
            ("访问首页", "访问网址", '网址="https://www.reelmate.cn" 等待方式="load"'),
            ("等待页面渲染完成", "强制等待", '数据内容="3"'),
            ("点击登录入口按钮", "点击元素", '_页面元素="登录入口按钮"'),
            ("等待登录页加载", "强制等待", '数据内容="3"'),
            ("输入正确的账号", "输入内容", '数据内容="18318053665" _页面元素="用户名输入框"'),
            ("输入错误的密码", "输入内容", '数据内容="wrongpassword123" _页面元素="密码输入框"'),
            ("点击登录按钮提交", "点击元素", '_页面元素="登录提交按钮"'),
            ("等待登录响应", "强制等待", '数据内容="3"'),
            ("获取当前页面URL", "获取当前URL", '变量名="current_url"'),
            ("验证仍在登录页面", "断言文本包含",
             '预期结果="accounts.wondershare.cn" 实际结果="{{current_url}}" 错误信息="错误密码登录不应该成功"'),
        ]),
        # ==============================
        # 用例4: 空账号校验
        # ==============================
        ("登录模块", "登录功能", "TC004-空账号登录校验", "WebCase", [
            ("访问首页", "访问网址", '网址="https://www.reelmate.cn" 等待方式="load"'),
            ("等待页面渲染完成", "强制等待", '数据内容="3"'),
            ("点击登录入口按钮", "点击元素", '_页面元素="登录入口按钮"'),
            ("等待登录页加载", "强制等待", '数据内容="3"'),
            ("清空用户名输入框", "清空输入框", '_页面元素="用户名输入框"'),
            ("输入密码", "输入内容", '数据内容="qq111111" _页面元素="密码输入框"'),
            ("点击登录按钮提交", "点击元素", '_页面元素="登录提交按钮"'),
            ("等待响应", "强制等待", '数据内容="2"'),
            ("获取当前页面URL", "获取当前URL", '变量名="current_url"'),
            ("验证仍在登录页面", "断言文本包含",
             '预期结果="accounts.wondershare.cn" 实际结果="{{current_url}}" 错误信息="空账号登录不应该成功"'),
        ]),
        # ==============================
        # 用例5: 空密码校验
        # ==============================
        ("登录模块", "登录功能", "TC005-空密码登录校验", "WebCase", [
            ("访问首页", "访问网址", '网址="https://www.reelmate.cn" 等待方式="load"'),
            ("等待页面渲染完成", "强制等待", '数据内容="3"'),
            ("点击登录入口按钮", "点击元素", '_页面元素="登录入口按钮"'),
            ("等待登录页加载", "强制等待", '数据内容="3"'),
            ("输入账号", "输入内容", '数据内容="18318053665" _页面元素="用户名输入框"'),
            ("清空密码输入框", "清空输入框", '_页面元素="密码输入框"'),
            ("点击登录按钮提交", "点击元素", '_页面元素="登录提交按钮"'),
            ("等待响应", "强制等待", '数据内容="2"'),
            ("获取当前页面URL", "获取当前URL", '变量名="current_url"'),
            ("验证仍在登录页面", "断言文本包含",
             '预期结果="accounts.wondershare.cn" 实际结果="{{current_url}}" 错误信息="空密码登录不应该成功"'),
        ]),
        # ==============================
        # 用例6: 格式错误账号校验
        # ==============================
        ("登录模块", "登录功能", "TC006-格式错误账号登录校验", "WebCase", [
            ("访问首页", "访问网址", '网址="https://www.reelmate.cn" 等待方式="load"'),
            ("等待页面渲染完成", "强制等待", '数据内容="3"'),
            ("点击登录入口按钮", "点击元素", '_页面元素="登录入口按钮"'),
            ("等待登录页加载", "强制等待", '数据内容="3"'),
            ("输入非法格式账号", "输入内容", '数据内容="!@#$%^&*()" _页面元素="用户名输入框"'),
            ("输入密码", "输入内容", '数据内容="qq111111" _页面元素="密码输入框"'),
            ("点击登录按钮提交", "点击元素", '_页面元素="登录提交按钮"'),
            ("等待响应", "强制等待", '数据内容="2"'),
            ("获取当前页面URL", "获取当前URL", '变量名="current_url"'),
            ("验证仍在登录页面", "断言文本包含",
             '预期结果="accounts.wondershare.cn" 实际结果="{{current_url}}" 错误信息="非法格式账号登录不应该成功"'),
        ]),
    ]

    # ---------- 写入数据 ----------
    row_num = 2
    for module, func, title, case_type, steps in cases:
        for step_desc, action_type, data_content in steps:
            ws.cell(row=row_num, column=1, value=module)
            ws.cell(row=row_num, column=2, value=func)
            ws.cell(row=row_num, column=3, value=title)
            ws.cell(row=row_num, column=4, value=case_type)
            ws.cell(row=row_num, column=5, value=step_desc)
            ws.cell(row=row_num, column=6, value=action_type)
            ws.cell(row=row_num, column=7, value=data_content)
            row_num += 1

    # ---------- 列宽 ----------
    col_widths = [12, 12, 28, 10, 20, 20, 60]
    for i, w in enumerate(col_widths):
        ws.column_dimensions[chr(65 + i)].width = w

    # ---------- 边框 ----------
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    for row in ws.iter_rows(min_row=1, max_row=row_num - 1, max_col=7):
        for cell in row:
            cell.border = thin_border
            if cell.row > 1:
                cell.alignment = Alignment(vertical="center", wrap_text=True)

    path = os.path.join(OUT_DIR, "1_登录模块测试.xlsx")
    wb.save(path)
    print(f"[OK] 已生成 1_登录模块测试.xlsx")


if __name__ == "__main__":
    create_context_xlsx()
    create_case_xlsx()
    print(f"\n运行测试命令:")
    print(f'  python main.py --type=excel --cases="{OUT_DIR}"')
