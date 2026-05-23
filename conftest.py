"""
pytest configuration — environment info, hooks, and fixtures.
"""

import os
import platform
import sys

import allure
import pytest
from loguru import logger

pytest_plugins = ["HAT.plugin"]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        logger.error(f"TEST FAILED: {item.nodeid}")
        if call.excinfo:
            logger.error(f"  {call.excinfo.typename}: {call.excinfo.value}")


def pytest_configure(config):
    os.makedirs("test-results", exist_ok=True)

    env_info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Python": sys.version.split()[0],
        "pytest": pytest.__version__,
        "CWD": os.getcwd(),
    }
    try:
        import playwright
        env_info["Playwright"] = getattr(playwright, "__version__", "installed")
    except Exception:
        env_info["Playwright"] = "not installed"

    try:
        with open(os.path.join("test-results", "environment.properties"),
                  "w", encoding="utf-8") as f:
            for k, v in env_info.items():
                f.write(f"{k}={v}\n")
    except Exception as e:
        logger.warning(f"Failed to write allure environment: {e}")


def pytest_collection_modifyitems(items):
    """Fix unicode-escaped Chinese test names."""
    for item in items:
        try:
            item.name = item.name.encode("utf-8").decode("unicode_escape")
            item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")
        except Exception:
            pass


@pytest.fixture(scope="session")
def hat_version():
    return "2026.5.0"
