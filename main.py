#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HAT — Hybrid Automation Testing framework
Python + Playwright + pytest + POM + DDT + Allure

Usage:
  python main.py --cases=./examples/reelmate-cases-excel
  python main.py --cases=./examples/reelmate-cases-excel --headless
  python main.py --cases=./examples/reelmate-cases-excel --headless --browser=firefox
  python main.py --cases=./examples/reelmate-cases-excel --headless --workers=4
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

import pytest
from _pytest.config import ExitCode
from loguru import logger

from HAT.extend.allure_combine.combine import combine_allure

# ── Windows console UTF-8 fix ──────────────────────────────────
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ── Logging ────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logger.configure(handlers=[
    {"sink": sys.stdout, "level": "WARNING"},
    {"sink": os.path.join("logs", f"hat_{time.strftime('%Y%m%d_%H%M%S')}.log"),
     "level": os.getenv("HAT_LOG_LEVEL", "INFO").upper()},
])


def _print_operations():
    """List all available operation types grouped by category."""
    from HAT.core.operation_types import list_by_category, OpCategory

    grouped = list_by_category()
    print()
    print("=== HAT Operation Types ===")
    print()
    for cat in (OpCategory.AI_ATOMIC, OpCategory.AI_ASSERTION, OpCategory.AI_COMPOSITE,
                OpCategory.ACTION, OpCategory.ASSERTION):
        ops = grouped.get(cat, [])
        if not ops:
            continue
        labels = {
            OpCategory.AI_ATOMIC:    "AI 原子操作 (AI:操作)",
            OpCategory.AI_ASSERTION: "AI 断言 (AI:断言)",
            OpCategory.AI_COMPOSITE: "AI 组合操作 (AI:执行)",
            OpCategory.ACTION:       "传统操作",
            OpCategory.ASSERTION:    "传统断言",
        }
        print(f"[{labels.get(cat, cat.name)}] ({len(ops)} operations)")
        for op in sorted(ops):
            print(f"  {op}")
        print()
    print("POM operations: dot-notation 'PageClass.method' (e.g., LoginPage.login)")
    print("Custom operations: configure --keyDir with your keyword module")
    print()


def parse_args():
    p = argparse.ArgumentParser(description="HAT Automation Testing Tool")
    p.add_argument("--version", action="version", version="2026.5.0")
    p.add_argument("--type", default="excel", help="Case format: excel | yaml")
    p.add_argument("--cases", default="examples/reelmate-cases-excel",
                   help="Case directory path")
    p.add_argument("--keyDir", help="Custom keyword directory")
    p.add_argument("--headless", action="store_true",
                   help="Headless mode (no browser UI)")
    p.add_argument("--browser", default="chromium",
                   choices=["chromium", "firefox", "webkit"],
                   help="Browser type")
    p.add_argument("--workers", type=int, default=1,
                   help="Parallel workers (requires pytest-xdist)")
    p.add_argument("--alluredir", default=os.path.join(os.getcwd(), "test-results"),
                   help="Allure results directory")
    p.add_argument("--report_html_path", default=os.path.join(os.getcwd(), "HTML测试报告"),
                   help="HTML report output directory")
    p.add_argument("--list-operations", action="store_true",
                   help="List all available operation types grouped by category")
    return p.parse_args()


def run():
    args = parse_args()

    print("=" * 50)
    print("   HAT Automation Testing Tool")
    print("   v2026.5.0 — Playwright + pytest + POM + DDT")
    print("=" * 50)

    if args.list_operations:
        _print_operations()
        return

    # Inject CLI config as env vars (highest priority)
    if args.headless:
        os.environ["HAT_HEADLESS"] = "true"
        logger.info("Headless mode enabled")
    os.environ["HAT_BROWSER"] = args.browser

    # Build pytest args
    pytest_args = ["-v", "--no-header", "-s", "--clean-alluredir", "-W", "ignore"]
    pytest_args.append(f"--type={args.type}")
    pytest_args.append(f"--cases={args.cases}")
    if args.keyDir:
        pytest_args.append(f"--keyDir={args.keyDir}")
    pytest_args.append(f"--alluredir={args.alluredir}")

    if args.workers > 1:
        pytest_args.extend(["-n", str(args.workers)])
        logger.info(f"Parallel workers: {args.workers}")

    # Target: TestRunner.test_case in runner.py
    import HAT.core.runner
    pytest_args.append(HAT.core.runner.__file__)

    # Environment checks
    logger.info("── Environment checks ──")
    try:
        import allure_pytest
        logger.info(f"  allure-pytest: OK")
    except ImportError:
        logger.error("  allure-pytest not installed!  pip install allure-pytest")
        sys.exit(1)

    if shutil.which("allure"):
        logger.info("  allure CLI: OK")
    else:
        logger.error("  allure CLI not found!  Install from: "
                     "https://github.com/allure-framework/allure2/releases")
        sys.exit(1)

    # Run tests
    exit_code = pytest.main(pytest_args)
    print("\nTests complete. Generating report...")

    # Generate Allure report
    if exit_code in (ExitCode.OK, ExitCode.TESTS_FAILED):
        try:
            subprocess.check_output(
                ["allure", "generate", "--lang", "zh", args.alluredir,
                 "-c", "-o", args.report_html_path],
                universal_newlines=True,
            )
            combine_allure(args.report_html_path)
            if not args.headless:
                import webbrowser
                webbrowser.open(os.path.join(args.report_html_path, "report.html"))
        except subprocess.CalledProcessError as e:
            logger.exception(e)
            logger.error(f"Report generation failed: {e}")
    elif exit_code == ExitCode.NO_TESTS_COLLECTED:
        logger.error("No test cases collected — check --cases path")
    else:
        logger.error("Test execution failed!")

    print("=" * 50)
    print("   Execution finished")
    print("=" * 50)


if __name__ == "__main__":
    run()
