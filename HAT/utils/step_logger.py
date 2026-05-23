"""
Allure step context — tracks current step name for screenshot captions.
"""

import contextlib
import threading

import allure

_current_step_name = threading.local()


def set_step_name(name: str):
    _current_step_name.value = name



@contextlib.contextmanager
def allure_step_with_log(step_name: str):
    """Context manager that wraps a test step with Allure reporting."""
    set_step_name(step_name)
    with allure.step(step_name):
        yield
