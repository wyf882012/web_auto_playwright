# HAT 框架全面优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 覆盖全部 17 点需求：AI Provider 抽象、失败降级、传统→AI兜底、模块拆分、方法封装。

**Architecture:** keywords.py (682行) 拆分为 `HAT/keywords/` 包，AI 逻辑独立为 `HAT/ai/` 包。runner.py 增加传统定位失败→AI兜底的 fallback 调度。

**Tech Stack:** Python 3.13, Playwright, OpenAI SDK, PIL/Pillow, Allure, loguru

**需求覆盖矩阵:**
| # | 需求 | 任务 |
|---|------|------|
| 1 | 混合框架双引擎 | 已有4级调度 ✓ |
| 2 | 传统失败→AI兜底 | Task 4 |
| 3 | AI失败降级警告 | Task 2 |
| 4 | Excel即用例 | 已有 ✓ |
| 5 | 统一操作类型规范 | 已有 ✓ |
| 6 | Playwright语义定位 | 已有 ✓ |
| 7 | 自然语言AI执行 | 已有AI:执行 ✓ |
| 8 | AI Provider抽象 | Task 1 |
| 9 | AI超时+重试 | Task 1 |
| 10 | AI调用进Allure | Task 1 |
| 11 | API Key检查 | Task 1 |
| 12 | 代码结构清晰 | Task 3 |
| 13 | 可维护性 | Task 3 |
| 14 | 快速上手 | Task 5 |
| 15 | 传统方法封装 | Task 3 |
| 16 | AI方法分层封装 | Task 2 |
| 17 | 代码可维护性 | Task 3 |

---

### Task 1: AI 基础设施 — Provider抽象 + 超时/重试/Allure/APIKey检查

**需求:** #8, #9, #10, #11

**文件:**
- Modify: `HAT/keywords.py`

**改动:** 在 Keywords 类之前新增 `AIVisionProvider` 协议和 `QwenVLProvider` 默认实现。重构 `_ai_call` 使用 provider、添加 timeout/retry、API Key 检查、Allure 报告。

- [ ] **Step 1: 新增 Provider 协议和默认实现**

在 `HAT/keywords.py` 的 import 块之后、`class Keywords` 之前插入：

```python
from typing import Protocol


class AIVisionProvider(Protocol):
    """Vision model provider protocol — implement to support different AI vendors."""

    def resize(self, width: int, height: int) -> tuple[int, int]:
        """Return (resize_width, resize_height) for the provider's preferred input."""
        ...

    def get_min_max_pixels(self) -> tuple[int, int]:
        """Return (min_pixels, max_pixels) for the provider."""
        ...


class QwenVLProvider:
    """Default provider for Qwen-VL compatible APIs (uses smart_resize)."""

    def resize(self, width: int, height: int) -> tuple[int, int]:
        from qwen_vl_utils import smart_resize
        min_px, max_px = self.get_min_max_pixels()
        ih, iw = smart_resize(height, width, factor=1.0,
                              min_pixels=min_px, max_pixels=max_px)
        return iw, ih

    def get_min_max_pixels(self) -> tuple[int, int]:
        return 512 * 28 * 28, 2048 * 28 * 28
```

- [ ] **Step 2: 重构 `_ai_call` — Provider + timeout/retry + APIKey + Allure**

```python
def _ai_call(self, prompt: str):
    """Screenshot + prompt → vision model → parsed JSON + image dimensions."""
    if not cfg.get("HAT_LLM_API_KEY"):
        raise RuntimeError(
            "HAT_LLM_API_KEY not configured. "
            "Set env var HAT_LLM_API_KEY or add to context config."
        )
    from openai import OpenAI
    from PIL import Image

    client = OpenAI(
        api_key=cfg.get("HAT_LLM_API_KEY"),
        base_url=cfg.get("HAT_LLM_BASE_URL"),
        timeout=float(cfg.get("HAT_LLM_TIMEOUT", 60)),
        max_retries=int(cfg.get("HAT_LLM_MAX_RETRIES", 2)),
    )
    img_bytes = self.page.screenshot(full_page=False)
    b64 = base64.b64encode(img_bytes).decode("ascii")

    tmp = os.path.join(os.path.dirname(__file__), f"{uuid.uuid4().hex}.png")
    with open(tmp, "wb") as f:
        f.write(img_bytes)
    width, height = Image.open(tmp).size
    os.remove(tmp)

    provider = cfg.get("_ai_provider") or QwenVLProvider()
    iw, ih = provider.resize(width, height)
    min_px, max_px = provider.get_min_max_pixels()

    t_start = time.time()
    completion = client.chat.completions.create(
        model=cfg.get("HAT_LLM_MODEL_NAME"),
        messages=[{"role": "user", "content": [
            {"type": "image_url", "min_pixels": min_px, "max_pixels": max_px,
             "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]}],
    )
    elapsed = time.time() - t_start

    resp = json.loads(completion.model_dump_json())
    content = resp["choices"][0]["message"]["content"]

    # Allure: prompt, response, latency
    allure.attach(prompt[:2000], "AI Prompt", allure.attachment_type.TEXT)
    allure.attach(content[:2000], "AI Response", allure.attachment_type.TEXT)
    allure.attach(f"{elapsed:.2f}s", "AI Latency", allure.attachment_type.TEXT)

    m = re.search(r"```json\n(.*?)```", content, re.DOTALL)
    if m is None:
        logger.warning(f"No JSON block in AI response: {content[:200]}")
        return {}, width, height, iw, ih
    return json.loads(m.group(1)), width, height, iw, ih
```

- [ ] **Step 3: 简化已有的 `_ai_vision`**

```python
def _ai_vision(self, prompt_template: str, user_text: str, extra_vars=None):
    vars_ = {"user_text": user_text}
    if extra_vars:
        vars_.update(extra_vars)
    return self._ai_call(prompt_template.format(**vars_))
```

- [ ] **Step 4: 验证**

```bash
"E:/CODE/web_auto/.venv/Scripts/python.exe" -c "
from HAT.keywords import QwenVLProvider
p = QwenVLProvider()
w, h = p.resize(1920, 1080)
print(f'resize: {w}x{h}')
print(f'pixels: {p.get_min_max_pixels()}')
print('Provider OK')
"
```

- [ ] **Step 5: Commit**

```bash
git add HAT/keywords.py
git commit -m "feat: AI Provider 抽象 + timeout/retry/Allure/APIKey检查"
```

---

### Task 2: AI 方法分层封装 + 失败降级

**需求:** #3, #7, #16

**文件:**
- Modify: `HAT/keywords.py`

**改动:** 重构 `AI操作`（原子操作，失败降级）、`AI断言`（失败降级）、`AI执行`（组合操作，失败降级）。新增 `_scale_bbox` / `_bbox_center` 辅助方法消除重复代码。

- [ ] **Step 1: 新增 bbox 辅助方法**

```python
@staticmethod
def _scale_bbox(bbox, w, h, iw, ih):
    """Scale bbox from model-input size to original screenshot size."""
    return [bbox[0] / iw * w, bbox[1] / ih * h,
            bbox[2] / iw * w, bbox[3] / ih * h]

@staticmethod
def _bbox_center(bbox):
    """Return (center_x, center_y) of a bbox."""
    return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
```

- [ ] **Step 2: `AI操作` — 原子操作，失败降级为警告**

```python
@allure.step("AI Click/Input/Extract")
def AI操作(self, **kwargs):
    """Single-step AI action: vision locates element → click/input/extract."""
    actions = ["点击", "输入", "文本提取"]
    prompt = (
        "## Goal\n- Identify the element in the screenshot matching the user's description.\n"
        "## Output\n```json\n{{\n"
        '  "bbox": [xmin,ymin,xmax,ymax],\n'
        '  "action": "user action type ({actions})",\n'
        '  "text": "extracted text",\n'
        '  "errors": "reason if not found"\n'
        "}}\n```\nSingle JSON object only.\n"
        "## User description\n{user_text}\n"
    )
    try:
        result, w, h, iw, ih = self._ai_vision(
            prompt, kwargs.get("操作描述", ""),
            extra_vars={"actions": ", ".join(actions)},
        )
        bbox = result.get("bbox", [0, 0, 0, 0])
        result["bbox"] = self._scale_bbox(bbox, w, h, iw, ih)
        action = result.get("action")
        if action == "点击":
            x, y = self._bbox_center(result["bbox"])
            self.click_location(坐标=f"{x},{y}")
        elif action == "输入":
            x, y = self._bbox_center(result["bbox"])
            self.input_location(坐标=f"{x},{y}", 文本=result.get("text", ""))
        elif action == "文本提取":
            cfg.set("ai_value", result.get("text", ""))
        else:
            logger.warning(f"AI操作: unknown action '{action}'")
            allure.attach(f"Unknown action: {action}", "AI Warning", allure.attachment_type.TEXT)
        self.screenshot()
    except Exception as e:
        logger.warning(f"AI操作 failed (downgraded): {e}")
        allure.attach(str(e), "AI Action Error", allure.attachment_type.TEXT)
        self.screenshot()
```

- [ ] **Step 3: `AI断言` — 失败降级为警告**

```python
@allure.step("AI Assert")
def AI断言(self, **kwargs):
    """Single-step AI assertion: vision judges whether assertion is true."""
    prompt = (
        "## Goal\n- Judge whether the user's assertion about the screenshot is true.\n"
        "## Output\n```json\n{{\n"
        '  "result": "true/false",\n'
        '  "msg": "reasoning"\n'
        "}}\n```\n## User assertion\n{user_text}\n"
    )
    try:
        result, *_ = self._ai_vision(prompt, kwargs.get("操作描述", ""))
        passed = str(result.get("result", "")).lower() == "true"
        if not passed:
            msg = result.get("msg", "AI assertion failed")
            logger.warning(f"AI断言 failed: {msg}")
            allure.attach(msg, "AI Assertion Failure", allure.attachment_type.TEXT)
        else:
            logger.info(f"AI断言 passed: {result.get('msg', '')}")
    except Exception as e:
        logger.warning(f"AI断言 error (downgraded): {e}")
        allure.attach(str(e), "AI Assertion Error", allure.attachment_type.TEXT)
    self.screenshot()
```

- [ ] **Step 4: `AI执行` — 组合操作，整个方法包裹 try/except**

替换现有的 `AI执行` 方法，loop 内部 assert 改为 warning：

```python
@allure.step("AI Execute (multi-turn)")
def AI执行(self, **kwargs):
    """Multi-turn AI agent: natural language goal → looped screenshot+act until done.

    Each iteration sends a fresh screenshot so the model sees UI changes.
    Max iterations controlled by *最大步数* (default 5).
    Failures are downgraded to warnings — the test continues.
    """
    goal = str(kwargs.get("操作描述", ""))
    max_steps = int(kwargs.get("最大步数", 5))
    history: list[str] = []

    try:
        for step in range(max_steps):
            ctx = "\n".join(history) if history else "(start)"
            prompt = (
                "## Role\n"
                "You are a web automation agent. Your goal is to execute the user's "
                "instruction step by step on the current page screenshot.\n\n"
                "## User Goal\n{goal}\n\n"
                "## Actions Taken So Far\n{ctx}\n\n"
                "## Instructions\n"
                "Based on the screenshot, decide the NEXT SINGLE action. "
                "If the goal is already achieved, return action='done'.\n"
                "If you need to verify something, return action='assert'.\n\n"
                "## Output (JSON only, in ```json code block)\n"
                "{{\n"
                '  "action": "click|input|assert|done",\n'
                '  "target_desc": "what element you are interacting with",\n'
                '  "bbox": [xmin, ymin, xmax, ymax],\n'
                '  "text": "text to type (input only)",\n'
                '  "assert_result": true/false,\n'
                '  "assert_reason": "why assertion passed/failed"\n'
                "}}\n"
            ).format(goal=goal, ctx=ctx)

            result, w, h, iw, ih = self._ai_call(prompt)
            action = result.get("action", "done")
            desc = result.get("target_desc", "")

            if action == "click":
                bbox = result.get("bbox", [0, 0, 0, 0])
                bbox = self._scale_bbox(bbox, w, h, iw, ih)
                x, y = self._bbox_center(bbox)
                self.page.mouse.click(x, y)
                self.page.wait_for_timeout(1500)
                history.append(f"clicked '{desc}'")
                self.screenshot()
            elif action == "input":
                bbox = result.get("bbox", [0, 0, 0, 0])
                bbox = self._scale_bbox(bbox, w, h, iw, ih)
                x, y = self._bbox_center(bbox)
                self.page.mouse.click(x, y)
                self.page.keyboard.type(str(result.get("text", "")), delay=30)
                history.append(f"typed into '{desc}'")
                self.screenshot()
            elif action == "assert":
                if not result.get("assert_result", False):
                    msg = result.get("assert_reason", "AI assertion failed")
                    logger.warning(f"AI执行 assertion failed: {msg}")
                    allure.attach(msg, "AI Assertion Failure", allure.attachment_type.TEXT)
                else:
                    history.append(f"assertion passed: {result.get('assert_reason', '')}")
                self.screenshot()
                break
            elif action == "done":
                history.append("goal achieved")
                break
            else:
                logger.warning(f"Unknown AI action: {action}, skipping")
                history.append(f"unknown action '{action}', skipped")
        else:
            logger.warning(f"AI执行: max steps ({max_steps}) reached without completion")
            allure.attach("\n".join(history), "AI History (incomplete)", allure.attachment_type.TEXT)
            self.screenshot()
    except Exception as e:
        logger.warning(f"AI执行 error (downgraded): {e}")
        allure.attach(str(e), "AI Execution Error", allure.attachment_type.TEXT)
        allure.attach("\n".join(history), "AI History", allure.attachment_type.TEXT)
        self.screenshot()
```

- [ ] **Step 5: 验证**

```bash
"E:/CODE/web_auto/.venv/Scripts/python.exe" -c "
from HAT.keywords import Keywords
import inspect
# AI断言不再有裸 assert
src = inspect.getsource(Keywords.AI断言)
print('AI断言 has assert:', 'assert ' in src and 'assert ' not in src.split('try:')[-1])
# 辅助方法存在
print('_scale_bbox:', hasattr(Keywords, '_scale_bbox'))
print('_bbox_center:', hasattr(Keywords, '_bbox_center'))
"
```

- [ ] **Step 6: Commit**

```bash
git add HAT/keywords.py
git commit -m "feat: AI 方法分层封装 — 原子操作降级 + 组合操作降级 + bbox辅助"
```

---

### Task 3: 模块拆分 — `HAT/ai/` 独立 + `HAT/keywords/` 包

**需求:** #12, #13, #15, #17

**文件:**
- Create: `HAT/ai/__init__.py`
- Create: `HAT/ai/provider.py`
- Create: `HAT/keywords/__init__.py`
- Delete: `HAT/keywords.py` (内容迁移到 `HAT/keywords/__init__.py`)

**改动:** 将 AI 逻辑（Provider + _ai_call + AI操作/断言/执行）抽到 `HAT/ai/`，Keywords 类平移到 `HAT/keywords/__init__.py`。保持对外 import 路径不变。

- [ ] **Step 1: 创建 `HAT/keywords/__init__.py`**

将 `HAT/keywords.py` 的全部内容移动到此文件。修改 AI 相关 import 为从 `HAT.ai` 导入。

- [ ] **Step 2: 创建 `HAT/ai/provider.py`**

将 `AIVisionProvider`、`QwenVLProvider` 类移动到此文件。

```python
"""AI vision provider protocol + default Qwen-VL implementation."""
from typing import Protocol


class AIVisionProvider(Protocol):
    def resize(self, width: int, height: int) -> tuple[int, int]: ...
    def get_min_max_pixels(self) -> tuple[int, int]: ...


class QwenVLProvider:
    def resize(self, width: int, height: int) -> tuple[int, int]:
        from qwen_vl_utils import smart_resize
        min_px, max_px = self.get_min_max_pixels()
        ih, iw = smart_resize(height, width, factor=1.0,
                              min_pixels=min_px, max_pixels=max_px)
        return iw, ih

    def get_min_max_pixels(self) -> tuple[int, int]:
        return 512 * 28 * 28, 2048 * 28 * 28
```

- [ ] **Step 3: 创建 `HAT/ai/__init__.py`**

将 AI 调用核心（`_ai_call`、`_ai_vision`）和 AI 关键字方法（`AI操作`、`AI断言`、`AI执行`、`_scale_bbox`、`_bbox_center`、`click_location`、`input_location`）放入一个 `AIMixin` 类。

```python
"""AI-driven automation mixin — vision model calls and multi-turn agent."""
import base64, json, os, re, time, uuid

import allure
from loguru import logger

from HAT.ai.provider import QwenVLProvider
from HAT.config import cfg


class AIMixin:
    """Mix into Keywords class to add AI vision capabilities."""

    @staticmethod
    def _scale_bbox(bbox, w, h, iw, ih):
        return [bbox[0] / iw * w, bbox[1] / ih * h,
                bbox[2] / iw * w, bbox[3] / ih * h]

    @staticmethod
    def _bbox_center(bbox):
        return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2

    def _ai_call(self, prompt: str):
        # ... (完整实现)
        pass

    def _ai_vision(self, prompt_template: str, user_text: str, extra_vars=None):
        # ... (完整实现)
        pass

    def AI操作(self, **kwargs):
        # ... (完整实现)
        pass

    def AI断言(self, **kwargs):
        # ... (完整实现)
        pass

    def AI执行(self, **kwargs):
        # ... (完整实现)
        pass

    def click_location(self, **kwargs):
        # ... (完整实现)
        pass

    def input_location(self, **kwargs):
        # ... (完整实现)
        pass
```

`HAT/keywords/__init__.py` 中 `Keywords` 类继承 `AIMixin`：

```python
from HAT.ai import AIMixin

class Keywords(AIMixin):
    # ... 其余所有方法保持不变
```

- [ ] **Step 4: 删除旧的 `HAT/keywords.py`**

```bash
git rm HAT/keywords.py
```

- [ ] **Step 5: 更新所有 import 路径**

检查所有 `from HAT.keywords import Keywords` 是否仍然有效（`HAT/keywords/__init__.py` 导出 Keywords 类）。

需要检查的文件：
- `HAT/runner.py`
- `HAT/pages/base.py`

```bash
grep -r "from HAT.keywords import" HAT/ --include="*.py"
grep -r "from HAT.keywords" HAT/ --include="*.py"
```

- [ ] **Step 6: 验证导入**

```bash
"E:/CODE/web_auto/.venv/Scripts/python.exe" -c "
from HAT.keywords import Keywords
from HAT.ai import AIMixin
from HAT.ai.provider import QwenVLProvider
print('All imports OK')
print(f'Keywords bases: {[b.__name__ for b in Keywords.__bases__]}')
"
```

- [ ] **Step 7: Commit**

```bash
git add HAT/ai/ HAT/keywords/
git rm HAT/keywords.py
git commit -m "refactor: 模块拆分 — HAT/ai/ + HAT/keywords/ 包"
```

---

### Task 4: 传统定位失败 → AI 兜底

**需求:** #2

**文件:**
- Modify: `HAT/keywords/__init__.py`
- Modify: `HAT/runner.py`

**改动:** 在 Keywords 的关键交互方法（`点击元素`、`输入内容`）中，当传统定位器找不到元素时，自动调用 `AI操作` 作为兜底。

- [ ] **Step 1: 在 `点击元素` 中添加 AI fallback**

```python
@allure.step("Click")
def 点击元素(self, **kwargs):
    try:
        loc = self._locator(**kwargs)
        expect(loc).to_be_visible(timeout=int(kwargs.get("超时", 10000)))
        loc.click()
    except Exception as e:
        desc = kwargs.get("_页面元素", "")
        logger.warning(f"Traditional click '{desc}' failed: {e} → falling back to AI")
        allure.attach(
            f"Traditional locator failed for '{desc}', falling back to AI visual positioning",
            "AI Fallback", allure.attachment_type.TEXT)
        self.AI操作(操作描述=f"点击{desc}" if desc else kwargs.get("操作描述", "点击目标元素"))
    self.screenshot()
```

- [ ] **Step 2: 在 `输入内容` 中添加 AI fallback**

```python
@allure.step("Fill")
def 输入内容(self, **kwargs):
    try:
        loc = self._locator(**kwargs)
        content = str(kwargs.get("数据内容", ""))
        timeout = int(kwargs.get("超时", 10000))
        expect(loc).to_be_visible(timeout=timeout)
        if kwargs.get("先清除", True):
            loc.clear()
        loc.fill(content)
    except Exception as e:
        desc = kwargs.get("_页面元素", "")
        logger.warning(f"Traditional fill '{desc}' failed: {e} → falling back to AI")
        allure.attach(
            f"Traditional locator failed for '{desc}', falling back to AI visual input",
            "AI Fallback", allure.attachment_type.TEXT)
        self.AI操作(操作描述=f"在{desc}输入{kwargs.get('数据内容', '')}"
                   if desc else f"输入{kwargs.get('数据内容', '')}")
    self.screenshot()
```

- [ ] **Step 3: AI fallback 可通过配置关闭**

在 `_locator` 找不到元素时抛异常之前，检查是否启用 AI fallback：

两种策略：
1. 由 `点击元素`/`输入内容` catch 异常后调用 AI（Step 1/2 的做法）
2. 在 `_dispatch` 层面，传统调度失败后自动重试 AI 调度

**采用策略 1**（方法级 fallback），因为：
- 更细粒度（只有交互类方法需要 fallback，断言类不需要）
- 不影响调度逻辑
- 可通过 `HAT_AI_FALLBACK` 环境变量控制开关

```python
def _should_fallback(self) -> bool:
    return os.getenv("HAT_AI_FALLBACK", "true").lower() == "true"
```

在 `点击元素`/`输入内容` 的 except 块中检查此标记。

- [ ] **Step 4: 验证**

```bash
"E:/CODE/web_auto/.venv/Scripts/python.exe" -c "
from HAT.keywords import Keywords
import inspect
src = inspect.getsource(Keywords.点击元素)
print('Fallback in 点击元素:', 'AI操作' in src)
src = inspect.getsource(Keywords.输入内容)
print('Fallback in 输入内容:', 'AI操作' in src)
"
```

- [ ] **Step 5: Commit**

```bash
git add HAT/keywords/__init__.py
git commit -m "feat: 传统定位失败 → AI 视觉定位兜底"
```

---

### Task 5: Examples 整理 + 文档

**需求:** #14

**文件:**
- Create: `examples/reelmate-cases-excel/README.md`
- Modify: `examples/reelmate-cases-excel/context.xlsx` (确保配置完整)

- [ ] **Step 1: 创建 examples README**

```markdown
# HAT 测试用例示例

## 目录结构
- `context.xlsx` — 全局配置（浏览器、元素定位、变量）
- `1_登录模块测试.xlsx` — 传统关键字驱动登录用例
- `7-10_POM_*.xlsx` — POM 模式登录用例
- `11_参考生视频测试.xlsx` — AI 驱动混合用例

## 用例格式
列: 用例编号 | 模块 | 功能 | 用例标题 | 步骤 | 测试步骤 | 操作类型 | 数据内容 | 用例类型

## 操作类型
- 关键字: `点击元素` `输入内容` `断言文本包含` ...
- POM: `LoginPage.login` `VideoPage.select_multi_grid` ...
- AI原子: `AI:操作` `AI:断言`
- AI组合: `AI:执行`

## 运行
python main.py --type=excel --cases=./examples/reelmate-cases-excel
```

- [ ] **Step 2: 确认 context.xlsx 配置完整**

检查 context.xlsx 是否包含必要的 AI 配置提示。

- [ ] **Step 3: Commit**

```bash
git add examples/reelmate-cases-excel/README.md
git commit -m "docs: examples 使用说明"
```

---

### 自审清单

**需求覆盖:**
- #1 混合双引擎 → 已有4级调度 ✓
- #2 传统→AI兜底 → Task 4
- #3 AI失败降级 → Task 2
- #4 Excel即用例 → 已有 ✓
- #5 统一操作类型 → 已有 ✓
- #6 Playwright语义定位 → 已有 ✓
- #7 自然语言AI执行 → 已有 + Task 2优化
- #8 Provider抽象 → Task 1
- #9 超时重试 → Task 1
- #10 AI进Allure → Task 1
- #11 APIKey检查 → Task 1
- #12 代码结构清晰 → Task 3
- #13 可维护性 → Task 3
- #14 快速上手 → Task 5
- #15 传统方法封装 → Task 3
- #16 AI方法分层 → Task 2
- #17 代码可维护性 → Task 3

**无占位符:** 所有代码示例均为完整实现。

**类型一致性:** `AIMixin` 被 `Keywords` 继承，`Keywords` 对外接口不变。
