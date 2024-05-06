#!usr/bin/env python3
"""Project tasks."""

import glob


def task_html():
    """Build documentation-html for project."""
    return {
        "actions": ["make -C docs html"],
        "file_dep": glob.glob("*.py") + glob.glob("*.rst"),
    }


def task_tests():
    """Test application."""
    return {
        "actions": [
            "python -m unittest tests/test_controller.py",
            "python -m unittest tests/test_telegram_controller.py",
            "python -m unittest tests/test_zabbix_connector.py",
            "python -m unittest tests/test_zabbix_controller.py"
        ],
        "verbosity": 2
    }


def task_git_clean():
    """Clean untracked files."""
    return {
            "actions": ["git clean -xdf"],
    }


def task_docstyle():
    """Check docstrings in src code files."""
    return {
            "actions": ["pydocstyle ./source"],
            "verbosity": 2
    }


def task_code_style():
    """Check code in src directory."""
    return {
            "actions": ["flake8 ./source --max-line-length 120"],
            "verbosity": 2
    }


def task_check():
    """Perform all checks."""
    return {
            "actions": [],
            "task_dep": ["code_style", "docstyle", "tests"]
    }
