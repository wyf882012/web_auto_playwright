"""
Test-case parser — reads Excel / YAML case files and produces unified case dicts.

Data flow:
  directory/ → load context → scan case files → parse rows → DDT expand → [{caseinfo}, ...]

Excel case-file columns:
  用例编号 | 模块 | 功能 | 用例标题 | 用例类型 | 测试步骤 | 操作类型 | 数据内容

Excel context.xlsx sheets:
  浏览器配置 | WEB页面元素 | 通用配置 | 数据库配置

DDT: an optional "数据驱动" sheet in the case file or "数据驱动" list in YAML.
"""

import ast
import copy
import json
import os
import re
import uuid
from typing import List, Optional

import pandas as pd
import yaml

from HAT.operation_types import validate as validate_op

from HAT.config import cfg


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════

def _parse_kv(text: Optional[str]) -> dict:
    """Parse key=value pairs from a data-content string.

    Supports: key="val" key='val' key=val   (space-separated)
    """
    if not isinstance(text, str) or not text.strip():
        return {}
    pairs = re.findall(r"""(\w+)=(?:"([^"]*)"|'([^']*)'|(\S+))""",
                       text.replace("\\n", " ").strip())
    out = {}
    for k, dq, sq, uq in pairs:
        val = dq or sq or uq
        out[k] = _coerce(val) if val is not None else None
    return out


def _coerce(s: str):
    """Try to convert *s* to a Python literal; fall back to string."""
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return s



# ═══════════════════════════════════════════════════════════════
#  Context loading
# ═══════════════════════════════════════════════════════════════

def load_context(folder: str) -> None:
    """Load context.{xlsx,yaml} from *folder* into global config."""
    xlsx = os.path.join(folder, "context.xlsx")
    yml = os.path.join(folder, "context.yaml")
    if os.path.exists(xlsx):
        _load_excel_context(xlsx)
    elif os.path.exists(yml):
        _load_yaml_context(yml)


def _load_excel_context(path: str) -> None:
    xl = pd.ExcelFile(path)
    sheets = xl.sheet_names

    if "浏览器配置" in sheets:
        df = pd.read_excel(path, sheet_name="浏览器配置").fillna("")
        row = df.to_dict(orient="records")[0] if len(df) > 0 else {}
        cap = json.loads(row.get("启动参数", "{}")) if row.get("启动参数") else {}
        cfg.set("_browser", {
            "browserName": row.get("浏览器名称", "chromium"),
            "args": cap.get("args", []),
            "headless": cap.get("headless", False),
        })

    if "WEB页面元素" in sheets:
        df = pd.read_excel(path, sheet_name="WEB页面元素").fillna("")
        records = df.to_dict(orient="records")
        if records and "定位器类型" in records[0]:
            elems = _parse_semantic_elements(records)
        else:
            elems = {r["元素名称"]: {"定位方式": r.get("定位方式", "css"),
                                    "目标对象": r.get("目标对象", "")}
                     for r in records}
        cfg.set("_elements", elems)

    if "通用配置" in sheets:
        df = pd.read_excel(path, sheet_name="通用配置")
        for _, row in df.iterrows():
            val = row["配置值"]
            try:
                val = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                pass
            cfg.set(row["配置名"], val)

    if "数据库配置" in sheets:
        df = pd.read_excel(path, sheet_name="数据库配置").fillna("")
        dbs = {}
        for _, row in df.iterrows():
            dbs[row["别名"]] = {"host": row["服务器IP"], "port": row["端口号"],
                                "user": row["用户名"], "password": row["密码"],
                                "db": row["数据库名称"]}
        cfg.set("_database", dbs)


def _parse_semantic_elements(records: list) -> dict:
    """Parse new-style WEB页面元素 sheet (定位器类型 column present)."""
    elems = {}
    for r in records:
        name = r.get("元素名称", "")
        if not name:
            continue
        lt = str(r.get("定位器类型", "css")).strip().lower()
        meta = {"type": lt}
        if lt == "role":
            meta["role"] = str(r.get("角色", "button")).strip()
            if r.get("名称", "").strip():
                meta["name"] = str(r["名称"]).strip()
        elif lt in ("label", "placeholder", "text", "alt", "testid", "css", "xpath"):
            meta["value"] = str(r.get("值", r.get("名称", ""))).strip()
        else:
            meta["value"] = str(r.get("值", "")).strip()
        if r.get("Frame", "").strip():
            meta["frame"] = str(r["Frame"]).strip()
        elems[name] = meta
    return elems


def _load_yaml_context(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg.update(data)


# ═══════════════════════════════════════════════════════════════
#  Case-file loading
# ═══════════════════════════════════════════════════════════════

def parse(folder: str) -> dict:
    """Main entry: parse all case files in *folder*, return {case_infos, case_names}."""
    load_context(folder)
    raw = _load_case_files(folder)
    return _expand_ddt(raw)


def _load_case_files(folder: str) -> List[dict]:
    """Scan *folder* for case files, return list of raw case dicts."""
    # Sort by numeric prefix: 1_xxx, 2_yyy, ...
    files = sorted(
        [f for f in os.listdir(folder)
         if f.endswith((".xlsx", ".yaml", ".yml"))
         and f.split("_")[0].isdigit() and f != "context.yaml"],
        key=lambda f: int(f.split("_")[0]),
    )

    cases = []
    for fn in files:
        path = os.path.join(folder, fn)
        if fn.endswith(".xlsx"):
            cases.extend(_load_excel_file(path))
        else:
            cases.extend(_load_yaml_file(path))
    return cases


def _load_excel_file(path: str) -> List[dict]:
    """Parse one Excel case file → list of grouped case dicts."""
    df = pd.read_excel(path, sheet_name=0).where(pd.notnull, None)
    rows = df.to_dict(orient="records")
    grouped = _group_rows(rows)

    # Attach DDT sheet data if present
    ddt_map = _load_ddt_sheet(path)
    for case in grouped:
        title = case.get("基础配置", {}).get("用例标题", "")
        if title in ddt_map:
            case["_ddt_data"] = ddt_map[title]
    return grouped


def _load_yaml_file(path: str) -> List[dict]:
    """Parse one YAML case file → list of case dicts."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # YAML may hold a single dict or list of dicts
    items = data if isinstance(data, list) else [data]
    for item in items:
        ddts = item.pop("数据驱动", [])
        if ddts:
            item["_ddt_data"] = ddts
    return items


def _group_rows(rows: List[dict]) -> List[dict]:
    """Group flat Excel rows into cases keyed by 用例标题."""
    result = []
    current = None
    for row in rows:
        title = row.get("用例标题")
        if title and str(title).strip():
            if current:
                result.append(current)
            current = {"基础配置": {
                "用例标题": str(title).strip(),
                "用例类型": row.get("用例类型") or cfg.get("用例类型", "WebCase"),
                "一级模块": row.get("模块", ""),
                "二级模块": row.get("功能", ""),
            }, "用例步骤": []}
            cid = row.get("用例编号")
            if cid and str(cid).strip():
                current["基础配置"]["用例编号"] = str(cid).strip()
        if current is None:
            continue
        step_name = row.get("测试步骤", "")
        action = row.get("操作类型", "")
        if not action or not str(action).strip():
            continue  # skip blank/legend rows
        params = _parse_kv(row.get("数据内容"))
        params["操作类型"] = action

        ok, err = validate_op(action)
        if not ok:
            raise ValueError(
                f"Invalid 操作类型 in case '{title}', step '{step_name}': {err}\n"
                f"  Tip: Run 'python main.py --list-operations' to see all valid operations."
            )

        current["用例步骤"].append({step_name: params})
    if current:
        result.append(current)
    return result


def _load_ddt_sheet(path: str) -> dict:
    """Load DDT data from an optional '数据驱动' sheet."""
    try:
        xl = pd.ExcelFile(path)
    except Exception:
        return {}
    if "数据驱动" not in xl.sheet_names:
        return {}

    df = pd.read_excel(path, sheet_name="数据驱动", dtype=str)
    df = df.where(df.notnull(), None)
    ddt_map = {}
    for _, row in df.iterrows():
        d = row.to_dict()
        case_title = d.pop("用例标题", None)
        if not case_title:
            continue
        params = {k: _coerce(v) for k, v in d.items() if v is not None}
        ddt_map.setdefault(case_title, []).append(params)
    return ddt_map


# ═══════════════════════════════════════════════════════════════
#  DDT expansion (shared by Excel & YAML paths)
# ═══════════════════════════════════════════════════════════════

def _expand_ddt(raw_cases: List[dict]) -> dict:
    """Expand DDT templates into individual test instances."""
    case_infos, case_names = [], []
    for template in raw_cases:
        ddt_data = template.pop("_ddt_data", None)
        if not ddt_data:
            case_infos.append(template)
            case_names.append(_case_title(template))
        else:
            for params in ddt_data:
                instance = copy.deepcopy(template)
                instance["local_context"] = params
                new_title = _ddt_title(template, params)
                instance.setdefault("基础配置", {})["用例标题"] = new_title
                case_infos.append(instance)
                case_names.append(new_title)
    return {"case_infos": case_infos, "case_names": case_names}


def _case_title(case: dict) -> str:
    return case.get("基础配置", {}).get("用例标题", str(uuid.uuid4()))


def _ddt_title(template: dict, params: dict) -> str:
    base = _case_title(template)
    desc = params.get("描述标题", str(uuid.uuid4()))
    cid = template.get("基础配置", {}).get("用例编号", "")
    return f"{cid}-{base}-{desc}" if cid else f"{base}-{desc}"
