"""Operation type registry — single source of truth for categorizing 操作类型 values."""

from enum import Enum, auto


class OpCategory(Enum):
    """Classification of every 操作类型 value used in Excel/YAML test cases."""
    AI_ATOMIC    = auto()  # AI:操作 — single-step vision action (click/input/extract)
    AI_ASSERTION = auto()  # AI:断言 — single-step vision assertion
    AI_COMPOSITE = auto()  # AI:执行 — multi-turn agent loop
    ACTION       = auto()  # Traditional keyword that performs an action
    ASSERTION    = auto()  # Traditional keyword that checks a condition
    POM          = auto()  # PageClass.method dot-notation
    CUSTOM       = auto()  # ex_invoke — user-provided keyword module


# ── Whitelist of known operation types ──────────────────────────

_REGISTRY: dict[str, OpCategory] = {
    # ── AI operations (prefixed "AI:" in Excel) ──
    "AI:操作": OpCategory.AI_ATOMIC,
    "AI:断言": OpCategory.AI_ASSERTION,
    "AI:执行": OpCategory.AI_COMPOSITE,

    # ── Traditional actions ──
    # Page navigation
    "访问网址": OpCategory.ACTION,
    "页面刷新": OpCategory.ACTION,
    "页面前进": OpCategory.ACTION,
    "页面后退": OpCategory.ACTION,
    # Element interaction
    "点击元素": OpCategory.ACTION,
    "输入内容": OpCategory.ACTION,
    "输入内容追加": OpCategory.ACTION,
    "清空输入框": OpCategory.ACTION,
    "鼠标悬停": OpCategory.ACTION,
    "双击元素": OpCategory.ACTION,
    "右键点击": OpCategory.ACTION,
    "滚动到元素": OpCategory.ACTION,
    # Form controls
    "选择下拉框选项": OpCategory.ACTION,
    "选择下拉框选项按值": OpCategory.ACTION,
    "勾选复选框": OpCategory.ACTION,
    "取消勾选": OpCategory.ACTION,
    "上传文件": OpCategory.ACTION,
    # Retrieval
    "获取元素文本": OpCategory.ACTION,
    "获取元素属性": OpCategory.ACTION,
    "获取当前URL": OpCategory.ACTION,
    "获取页面标题": OpCategory.ACTION,
    # Window / tab / iframe
    "iframe_switch_to": OpCategory.ACTION,
    "iframe_to_default_content": OpCategory.ACTION,
    "switch_to_latest_handle": OpCategory.ACTION,
    "switch_to_appoint_handle": OpCategory.ACTION,
    "关闭当前页面": OpCategory.ACTION,
    # Misc
    "强制等待": OpCategory.ACTION,
    "窗口最大化": OpCategory.ACTION,
    "关闭浏览器": OpCategory.ACTION,
    "键盘按键": OpCategory.ACTION,
    "拖拽元素": OpCategory.ACTION,
    "滚动页面": OpCategory.ACTION,
    "执行JS": OpCategory.ACTION,
    "接受弹窗": OpCategory.ACTION,
    "取消弹窗": OpCategory.ACTION,
    "获取弹窗文本": OpCategory.ACTION,
    # Variables
    "store_text": OpCategory.ACTION,
    "random_six_digit_number": OpCategory.ACTION,
    # Database
    "提取数据MYSQL": OpCategory.ACTION,
    # CAPTCHA
    "image_recognition": OpCategory.ACTION,
    # Coordinate-based (from AIMixin)
    "click_location": OpCategory.ACTION,
    "input_location": OpCategory.ACTION,
    # Built-in
    "screenshot": OpCategory.ACTION,
    "ex_invoke": OpCategory.ACTION,

    # ── Traditional assertions ──
    "断言文本": OpCategory.ASSERTION,
    "断言文本相等": OpCategory.ASSERTION,
    "断言文本包含": OpCategory.ASSERTION,
    "断言文本不相等": OpCategory.ASSERTION,
    "断言数字相等": OpCategory.ASSERTION,
    "断言数字不相等": OpCategory.ASSERTION,
    "断言数字大于": OpCategory.ASSERTION,
    "断言数字小于": OpCategory.ASSERTION,
    "断言数字大于等于": OpCategory.ASSERTION,
    "断言数字小于等于": OpCategory.ASSERTION,
    "断言浏览器路径": OpCategory.ASSERTION,
    "断言元素存在": OpCategory.ASSERTION,
    "断言元素不存在": OpCategory.ASSERTION,
    "断言页面标题": OpCategory.ASSERTION,
}


# ── Public API ──────────────────────────────────────────────────

def categorize(op_type: str) -> OpCategory:
    """Classify an 操作类型 string into its OpCategory."""
    if not op_type or not str(op_type).strip():
        return OpCategory.CUSTOM
    op_type = str(op_type).strip()
    if op_type in _REGISTRY:
        return _REGISTRY[op_type]
    if "." in op_type:
        return OpCategory.POM
    return OpCategory.CUSTOM


def is_ai(op_type: str) -> bool:
    """True if op_type is any AI-driven category."""
    return categorize(op_type) in (OpCategory.AI_ATOMIC, OpCategory.AI_ASSERTION,
                                   OpCategory.AI_COMPOSITE)


def is_assertion(op_type: str) -> bool:
    """True if op_type is any assertion (AI or traditional)."""
    return categorize(op_type) in (OpCategory.AI_ASSERTION, OpCategory.ASSERTION)


def validate(op_type: str) -> tuple[bool, str | None]:
    """Return (is_valid, error_message_or_None). Catches known typos early."""
    if not op_type or not str(op_type).strip():
        return False, "操作类型 cannot be empty"
    op_type = str(op_type).strip()
    cat = categorize(op_type)

    # AI prefix but unknown suffix → hard error (Excel typo, catch early)
    if op_type.startswith("AI:") and cat == OpCategory.CUSTOM:
        known = [k for k in _REGISTRY if k.startswith("AI:")]
        return False, f"Unknown AI operation: '{op_type}'. Valid: {known}"

    # POM dot-notation format check
    if "." in op_type:
        parts = op_type.split(".")
        if not parts[0] or len(parts) < 2 or not parts[1]:
            return False, f"Invalid POM format: '{op_type}'. Expected 'PageClass.method'"

    return True, None


def list_by_category() -> dict[OpCategory, list[str]]:
    """Group all known operations by category. Excludes POM/CUSTOM (dynamic)."""
    result: dict[OpCategory, list[str]] = {}
    for name, cat in _REGISTRY.items():
        result.setdefault(cat, []).append(name)
    return result
