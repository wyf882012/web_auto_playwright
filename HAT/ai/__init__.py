"""AI-driven automation mixin — vision model calls and multi-turn agent."""
import base64
import json
import os
import re
import time
import uuid

import allure
from loguru import logger

from HAT.ai.provider import QwenVLProvider
from HAT.config import cfg


class AIMixin:
    """Mix into Keywords class to add AI vision capabilities."""

    @staticmethod
    def _scale_bbox(bbox, w, h, iw, ih):
        """Scale bbox from model-input size to original screenshot size."""
        return [bbox[0] / iw * w, bbox[1] / ih * h,
                bbox[2] / iw * w, bbox[3] / ih * h]

    @staticmethod
    def _bbox_center(bbox):
        """Return (center_x, center_y) of a bbox."""
        return (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2

    def _ai_call(self, prompt: str):
        """Screenshot + prompt → vision model → parsed JSON + image dimensions."""
        # ── Config check: fail early with clear message ──
        if not cfg.get("HAT_LLM_API_KEY"):
            raise RuntimeError(
                "HAT_LLM_API_KEY not configured. "
                "Set env var HAT_LLM_API_KEY or add to context config."
            )
        if not cfg.get("HAT_LLM_MODEL_NAME"):
            raise RuntimeError(
                "HAT_LLM_MODEL_NAME not configured. "
                "Set env var HAT_LLM_MODEL_NAME or add to context config."
            )
        from openai import OpenAI
        from PIL import Image

        client = OpenAI(
            api_key=cfg.get("HAT_LLM_API_KEY"),
            base_url=cfg.get("HAT_LLM_BASE_URL"),
            timeout=float(cfg.get("HAT_LLM_TIMEOUT", 60)),
            max_retries=int(cfg.get("HAT_LLM_MAX_RETRIES", 2)),
        )
        # ── Screenshot → base64 ──
        img_bytes = self.page.screenshot(full_page=False)
        b64 = base64.b64encode(img_bytes).decode("ascii")

        # ── Save temp file → PIL dimensions → cleanup ──
        tmp = os.path.join(os.path.dirname(__file__), f"{uuid.uuid4().hex}.png")
        try:
            with open(tmp, "wb") as f:
                f.write(img_bytes)
            with Image.open(tmp) as img:
                width, height = img.size
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

        # ── Provider resize: adapt image to model's preferred input size ──
        provider = cfg.get("_ai_provider")
        if not callable(getattr(provider, "resize", None)):
            provider = QwenVLProvider()
        iw, ih = provider.resize(width, height)
        min_px, max_px = provider.get_min_max_pixels()

        # ── Vision API call ──
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
        content = resp["choices"][0]["message"]["content"] or ""

        # ── Allure attachments for debugging ──
        allure.attach(prompt[:2000], "AI Prompt", allure.attachment_type.TEXT)
        allure.attach(content[:2000], "AI Response", allure.attachment_type.TEXT)
        allure.attach(f"{elapsed:.2f}s", "AI Latency", allure.attachment_type.TEXT)

        # ── Extract JSON from markdown code block ──
        m = re.search(r"```json\n(.*?)```", content, re.DOTALL)
        if m is None:
            logger.warning(f"No JSON block in AI response: {content[:200]}")
            return {}, width, height, iw, ih
        try:
            return json.loads(m.group(1)), width, height, iw, ih
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in AI response: {e}")
            return {}, width, height, iw, ih

    def _ai_vision(self, prompt_template: str, user_text: str, extra_vars=None):
        vars_ = {"user_text": user_text}
        if extra_vars:
            vars_.update(extra_vars)
        return self._ai_call(prompt_template.format(**vars_))

    @allure.step("AI Click/Input/Extract")
    def AI操作(self, **kwargs):
        """Single-step AI action: vision locates element → click/input/extract."""
        # Hard-fail on config errors (missing API key / model name)
        if not cfg.get("HAT_LLM_API_KEY"):
            raise RuntimeError("HAT_LLM_API_KEY not configured")
        if not cfg.get("HAT_LLM_MODEL_NAME"):
            raise RuntimeError("HAT_LLM_MODEL_NAME not configured")

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
            # Guard: empty result or all-zero bbox means AI couldn't locate the element
            if not result or bbox == [0, 0, 0, 0]:
                logger.warning("AI操作: AI returned no valid bbox, skipping action")
                allure.attach(str(result), "AI Empty Result", allure.attachment_type.TEXT)
                self.screenshot()
                return
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

    @allure.step("AI Assert")
    def AI断言(self, **kwargs):
        """Single-step AI assertion: vision judges whether assertion is true."""
        if not cfg.get("HAT_LLM_API_KEY"):
            raise RuntimeError("HAT_LLM_API_KEY not configured")
        if not cfg.get("HAT_LLM_MODEL_NAME"):
            raise RuntimeError("HAT_LLM_MODEL_NAME not configured")

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

    @allure.step("AI Execute (multi-turn)")
    def AI执行(self, **kwargs):
        """Multi-turn AI agent: natural language goal → looped screenshot+act until done."""
        if not cfg.get("HAT_LLM_API_KEY"):
            raise RuntimeError("HAT_LLM_API_KEY not configured")
        if not cfg.get("HAT_LLM_MODEL_NAME"):
            raise RuntimeError("HAT_LLM_MODEL_NAME not configured")

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

    @allure.step("AI Click at coordinates")
    def click_location(self, **kwargs):
        x, y = [float(v.strip()) for v in str(kwargs.get("坐标", "0,0")).split(",")]
        self.page.mouse.click(x, y)
        self.screenshot()

    @allure.step("AI Input at coordinates")
    def input_location(self, **kwargs):
        self.click_location(**kwargs)
        self.page.keyboard.type(str(kwargs.get("文本", "")), delay=30)
        self.screenshot()
