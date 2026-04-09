"""Context-aware suggestions engine for common Python exceptions."""

from typing import List, Optional
from stacktrace_lens.parser import StackTrace


SUGGESTION_RULES: List[dict] = [
    {
        "exception": "AttributeError",
        "hint": "Check that the object has the attribute you're accessing. "
                "Use `dir(obj)` or `hasattr(obj, name)` to inspect it.",
    },
    {
        "exception": "ImportError",
        "hint": "Ensure the module is installed (`pip install <package>`) "
                "and the import path is correct.",
    },
    {
        "exception": "ModuleNotFoundError",
        "hint": "The module could not be found. Run `pip install <package>` "
                "or verify your PYTHONPATH.",
    },
    {
        "exception": "KeyError",
        "hint": "The key does not exist in the dictionary. "
                "Use `.get(key, default)` or check with `key in d` first.",
    },
    {
        "exception": "IndexError",
        "hint": "List index is out of range. Verify the list length with `len()` "
                "before accessing by index.",
    },
    {
        "exception": "TypeError",
        "hint": "A function received an argument of the wrong type. "
                "Check function signatures and the types of values being passed.",
    },
    {
        "exception": "ValueError",
        "hint": "A function received an argument with the right type but an "
                "inappropriate value. Validate input before passing it.",
    },
    {
        "exception": "FileNotFoundError",
        "hint": "The file path does not exist. Use `pathlib.Path.exists()` "
                "to verify the path before opening.",
    },
    {
        "exception": "RecursionError",
        "hint": "Maximum recursion depth exceeded. Check for missing base cases "
                "or consider an iterative approach.",
    },
    {
        "exception": "ZeroDivisionError",
        "hint": "Division by zero detected. Guard with an `if divisor != 0` check.",
    },
    {
        "exception": "NameError",
        "hint": "A variable or name is not defined. Check for typos or ensure "
                "the variable is assigned before use.",
    },
]


def get_suggestion(stacktrace: StackTrace) -> Optional[str]:
    """Return a suggestion string for the given StackTrace, or None."""
    exc_type = stacktrace.exception_type.strip()
    for rule in SUGGESTION_RULES:
        if rule["exception"] == exc_type:
            return rule["hint"]
    return None


def get_all_suggestions(stacktrace: StackTrace) -> List[str]:
    """Return all matching suggestions (useful if subclass names are checked)."""
    exc_type = stacktrace.exception_type.strip()
    return [
        rule["hint"]
        for rule in SUGGESTION_RULES
        if rule["exception"] in exc_type
    ]
