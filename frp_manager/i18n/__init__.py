"""Translation dispatcher.

Usage:
    t("key", defaults)
    t("key_with_var", defaults, n=5)
"""
from typing import Any

from ..config import Defaults

_FINGLISH = None
_EN = None


def _load():
    global _FINGLISH, _EN
    if _FINGLISH is None:
        from . import finglish as f, en as e
        _FINGLISH = f.STRINGS
        _EN = e.STRINGS


def t(key: str, defaults: Defaults, **kwargs: Any) -> str:
    """Return translation for `key`, formatted with kwargs if any."""
    _load()
    lang = (defaults.ui_lang or "finglish").lower()
    table = _EN if lang == "english" else _FINGLISH
    raw = table.get(key, key)
    if kwargs:
        try:
            return raw.format(**kwargs)
        except (KeyError, IndexError):
            return raw
    return raw
