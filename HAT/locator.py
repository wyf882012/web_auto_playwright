"""
Semantic locator builder — YAML / dict → Playwright Locator objects.

Playwright best-practice priority:
  role > label > placeholder > text > alt > testid > css > xpath

YAML format:
  login_btn:
    type: role
    role: button
    name: "Sign in"
    frame: "#dialog iframe"   # optional iframe selector
"""

import os
from typing import Optional

import yaml
from playwright.sync_api import Locator, Page


class LocatorBuilder:
    """Build Playwright Locator objects from YAML files or definition dicts."""

    _BUILDERS = {
        "role": "_build_role",
        "label": "_build_label",
        "placeholder": "_build_placeholder",
        "text": "_build_text",
        "alt": "_build_alt",
        "testid": "_build_testid",
        "css": "_build_css",
        "xpath": "_build_xpath",
    }

    # ── public API ──────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, page: Page, yaml_path: str) -> dict[str, Locator]:
        """Load locator definitions from a YAML file."""
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Locator file not found: {yaml_path}")
        with open(yaml_path, encoding="utf-8") as f:
            return cls.from_dict(page, yaml.safe_load(f) or {})

    @classmethod
    def from_dict(cls, page: Page, definitions: dict) -> dict[str, Locator]:
        """Build locators from a {name: {type, ...}} dict."""
        result = {}
        for name, meta in definitions.items():
            if not isinstance(meta, dict):
                continue
            result[name] = cls._create(page, meta)
        return result

    @classmethod
    def from_legacy(cls, page: Page, elements: dict) -> dict[str, Locator]:
        """
        Convert old-style {定位方式, 目标对象} elements to semantic Locators.
        """
        converted = {}
        type_map = {
            "role": "role", "text": "text", "placeholder": "placeholder",
            "testid": "testid", "css": "css", "css selector": "css",
            "xpath": "xpath", "id": "css", "name": "css", "class": "css",
            "tag": "css",
        }
        for name, old in elements.items():
            if not isinstance(old, dict):
                continue
            loc_type = str(old.get("定位方式", "css")).lower()
            target = old.get("目标对象", "")
            new_type = type_map.get(loc_type, "css")

            meta = {"type": new_type}
            if new_type == "role":
                meta["role"] = "button"
                meta["name"] = target
            elif new_type == "css":
                if loc_type == "id":
                    meta["value"] = f"#{target}"
                elif loc_type == "name":
                    meta["value"] = f'[name="{target}"]'
                elif loc_type == "class":
                    meta["value"] = f".{target}"
                else:
                    meta["value"] = target
            elif new_type == "xpath":
                meta["value"] = target
            else:
                meta["value"] = target
            converted[name] = meta
        return cls.from_dict(page, converted)

    # ── internal ────────────────────────────────────────────────

    @classmethod
    def _create(cls, page: Page, meta: dict) -> Locator:
        loc_type = meta.get("type", "css").lower()
        frame_sel = meta.get("frame")
        target = page.locator(frame_sel).content_frame if frame_sel else page
        builder_name = cls._BUILDERS.get(loc_type)
        if builder_name is None:
            raise ValueError(f"Unsupported locator type: '{loc_type}'. "
                             f"Supported: {', '.join(cls._BUILDERS)}")
        return getattr(cls, builder_name)(target, meta)

    # ── per-type builders ───────────────────────────────────────

    @staticmethod
    def _build_role(page, m): return page.get_by_role(m.get("role", "button"), name=m.get("name"))
    @staticmethod
    def _build_label(page, m): return page.get_by_label(_val(m))
    @staticmethod
    def _build_placeholder(page, m): return page.get_by_placeholder(_val(m))
    @staticmethod
    def _build_text(page, m): return page.get_by_text(_val(m))
    @staticmethod
    def _build_alt(page, m): return page.get_by_alt_text(_val(m))
    @staticmethod
    def _build_testid(page, m): return page.get_by_test_id(_val(m))
    @staticmethod
    def _build_css(page, m): return page.locator(_val(m))
    @staticmethod
    def _build_xpath(page, m): return page.locator(f"xpath={_val(m)}")


def _val(m: dict) -> str:
    return m.get("value") or m.get("name", "")
