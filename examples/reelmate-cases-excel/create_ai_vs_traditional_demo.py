# -*- coding: utf-8 -*-
"""演示用例：AI操作 vs 传统操作 对比示例

在同一个用例中展示所有操作类型分类:
  - 传统操作 (ACTION)
  - 传统断言 (ASSERTION)
  - AI原子操作 (AI_ATOMIC)
  - AI断言 (AI_ASSERTION)
  - POM (PageClass.method)

生成后运行:
  python main.py --type=excel --cases=./examples/reelmate-cases-excel
  或先查看:
  python main.py --list-operations
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

HEADER_FONT = Font(bold=True, color="FFFFFF", size=11, name="微软雅黑")
HEADER_FILL = PatternFill("solid", fgColor="4472C4")
HEADER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
AI_FILL = PatternFill("solid", fgColor="E2EFDA")       # 绿色底 — AI操作
TRAD_FILL = PatternFill("solid", fgColor="DAEEF3")     # 蓝色底 — 传统操作
ASSERT_FILL = PatternFill("solid", fgColor="FDE9D9")   # 橙色底 — 断言
POM_FILL = PatternFill("solid", fgColor="E4DFEC")      # 紫色底 — POM
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)

CASE_HEADERS = ["用例编号", "模块", "功能", "用例标题", "步骤", "测试步骤",
                "操作类型", "数据内容", "用例类型"]
CASE_COL_WIDTHS = [14, 20, 14, 40, 8, 32, 26, 72, 10]


def category_fill(action_type: str) -> PatternFill | None:
    """根据操作类型返回对应的颜色填充。"""
    if action_type.startswith("AI:操作"):
        return AI_FILL
    if action_type.startswith("AI:断言"):
        return ASSERT_FILL
    if action_type.startswith("AI:执行"):
        return AI_FILL
    if "." in action_type:
        return POM_FILL
    if "断言" in action_type or action_type.startswith("断言"):
        return ASSERT_FILL
    return TRAD_FILL


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "AIvs传统操作对比演示"

    # ── 表头 ──
    for col_idx, h in enumerate(CASE_HEADERS, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGN

    # ── 步骤定义 (按分类标注) ──
    # fmt: (操作类型, 数据内容, 步骤描述, 分类标签)
    steps: list[tuple[str, str, str, str]] = [
        # ── 传统操作 ──
        ("LoginPage.navigate_to_login", "",
         "[POM] 导航到登录页", "POM"),
        ("LoginPage.login",
         "username=18318053665\npassword=qq111111",
         "[POM] 输入账号密码登录", "POM"),
        ("强制等待", "数据内容=5",
         "[传统操作] 等待页面跳转", "传统操作"),

        # ── 传统断言 ──
        ("断言浏览器路径", "数据内容=home",
         "[传统断言] 验证URL包含'home'", "传统断言"),
        ("断言元素存在",
         "定位器类型=role\n角色=button\n名称=创作",
         "[传统断言] 验证'创作'按钮可见", "传统断言"),

        # ── AI原子操作 ──
        ("AI:操作",
         "操作描述=点击页面中的参考生视频入口",
         "[AI:操作] 视觉定位并点击参考生视频入口", "AI原子操作"),

        # ── AI断言 ──
        ("AI:断言",
         "操作描述=视频模型下拉框中存在Seedance 2.0VIP选项",
         "[AI:断言] 视觉判断下拉框是否有Seedance选项", "AI断言"),

        # ── AI组合操作 (多轮Agent) ──
        ("AI:执行",
         "操作描述=选择多宫格模式，然后选择TGI2模型\n最大步数=3",
         "[AI:执行] 多轮Agent: 选多宫格→选TGI2", "AI组合操作"),

        # ── 传统操作收尾 ──
        ("获取当前URL", "变量名=final_url",
         "[传统操作] 获取最终URL存入变量", "传统操作"),
    ]

    # ── 写入数据 ──
    for step_idx, (action_type, data_content, step_desc, cat_label) in enumerate(steps):
        row = step_idx + 2
        fill = category_fill(action_type)

        if step_idx == 0:
            ws.cell(row=row, column=1, value="DEMO-001")
            ws.cell(row=row, column=2, value="演示模块")
            ws.cell(row=row, column=3, value="AIvs传统对比")
            ws.cell(row=row, column=4, value="混合演示-AI操作vs传统操作-分类识别示例")
            ws.cell(row=row, column=9, value="WebCase")

        ws.cell(row=row, column=5, value=step_idx + 1)
        ws.cell(row=row, column=6, value=step_desc)
        ws.cell(row=row, column=7, value=action_type)
        ws.cell(row=row, column=8, value=data_content)

        # 按分类着色
        for col in range(1, 10):
            cell = ws.cell(row=row, column=col)
            if fill:
                cell.fill = fill

    max_row = len(steps) + 1

    # ── 列宽 ──
    for i, w in enumerate(CASE_COL_WIDTHS):
        ws.column_dimensions[chr(65 + i)].width = w

    # ── 边框 + 对齐 ──
    for row in ws.iter_rows(min_row=1, max_row=max_row, max_col=9):
        for cell in row:
            cell.border = THIN_BORDER
            if cell.row > 1:
                cell.alignment = Alignment(vertical="center", wrap_text=True)

    # ── 图例行 (在数据下方) ──
    legend_start = max_row + 2
    legends = [
        (TRAD_FILL, "蓝色 — 传统操作 (ACTION)    例: 强制等待 / 点击元素 / 输入内容"),
        (ASSERT_FILL, "橙色 — 断言 (ASSERTION)    例: 断言元素存在 / AI:断言"),
        (AI_FILL, "绿色 — AI操作 (AI_ATOMIC / AI_COMPOSITE)  例: AI:操作 / AI:执行"),
        (POM_FILL, "紫色 — POM (PageClass.method) 例: LoginPage.login"),
    ]
    for i, (fill, desc) in enumerate(legends):
        row = legend_start + i
        ws.cell(row=row, column=1, value="▇").fill = fill
        ws.cell(row=row, column=2, value=desc)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)

    # ── 保存 ──
    path = os.path.join(OUT_DIR, "0_AIvs传统操作对比演示.xlsx")
    wb.save(path)
    print(f"[OK] Generated: {path}")
    print()
    print("颜色图例（在Excel中可见）:")
    print("  蓝色 — 传统操作 (ACTION)")
    print("  橙色 — 断言 (ASSERTION / AI_ASSERTION)")
    print("  绿色 — AI操作 (AI_ATOMIC / AI_COMPOSITE)")
    print("  紫色 — POM")
    print()
    print("验证分类:")
    print("  python -c \"from HAT.operation_types import categorize, OpCategory; print(categorize('AI:操作'))\"")
    print("  python main.py --list-operations")


if __name__ == "__main__":
    main()
