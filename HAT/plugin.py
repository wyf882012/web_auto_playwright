"""
Pytest plugin — registers CLI options and generates parametrized test cases.

Auto-discovered via conftest.py's pytest_plugins.
Also usable as standalone: pytest.main(..., plugins=[HAT.plugin.plugin_instance])
"""

from HAT.config import cfg
from HAT.parser import parse


# ── Module-level hook functions (auto-discovered by pytest) ─────

def pytest_addoption(parser):
    parser.addoption("--type", action="store", default="excel",
                     help="Case format: excel | yaml")
    parser.addoption("--cases", action="store", help="Case directory")
    parser.addoption("--keyDir", action="store", help="Custom keyword directory")


def pytest_generate_tests(metafunc):
    case_type = metafunc.config.getoption("type")
    cases_dir = metafunc.config.getoption("cases")
    key_dir = metafunc.config.getoption("keyDir")
    cfg.set("key_dir", key_dir)

    data = parse(cases_dir)

    if "caseinfo" in metafunc.fixturenames:
        metafunc.parametrize(
            "caseinfo", data["case_infos"],
            ids=data["case_names"],
        )


def pytest_collection_modifyitems(items):
    """Fix Chinese unicode display in test names."""
    for item in items:
        try:
            item.name = item.name.encode("utf-8").decode("unicode_escape")
            item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")
        except Exception:
            pass


# ── Class wrapper (for explicit plugin registration in main.py) ─

class CasesPlugin:
    """Explicit plugin class for pytest.main(plugins=[CasesPlugin()])."""

    pytest_addoption = staticmethod(pytest_addoption)
    pytest_generate_tests = staticmethod(pytest_generate_tests)
    pytest_collection_modifyitems = staticmethod(pytest_collection_modifyitems)


plugin_instance = CasesPlugin()
