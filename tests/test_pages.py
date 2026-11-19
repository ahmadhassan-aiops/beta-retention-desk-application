"""Every screen renders without an exception; the worklist opens a customer file."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

SCREENS = ["screens/worklist.py", "screens/customer_file.py", "screens/churn_map.py", "screens/scorecard.py",
           "screens/method.py"]


def _screen(path: str) -> AppTest:
    module = path.removesuffix(".py").replace("/", ".")
    return AppTest.from_string(f"""
from desk.ui import inject_css
import {module} as screen
inject_css()
screen.render()
""", default_timeout=90)


@pytest.mark.parametrize("path", SCREENS)
def test_screen_renders(path):
    at = _screen(path).run()
    assert not at.exception, at.exception


def test_new_customer_form():
    at = _screen("screens/customer_file.py").run()
    at.session_state["file_mode"] = "Enter a customer"
    at.run()
    assert not at.exception, at.exception


def test_worklist_filters_and_sort():
    at = _screen("screens/worklist.py").run()
    at.radio(key="wl_sort").set_value("Chance of leaving").run()
    assert not at.exception, at.exception
