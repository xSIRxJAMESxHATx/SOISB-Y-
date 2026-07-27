"""Centralized UI error handling + lightweight log ring."""
from __future__ import annotations
import time
import traceback
from typing import Any, Callable, Optional

_LOG: list = []


def log_exception(feature: str, exc: BaseException, extra: str = "") -> None:
    _LOG.append({
        "ts": time.time(),
        "feature": feature,
        "error": str(exc)[:300],
        "trace": traceback.format_exc()[-800:],
        "extra": extra,
    })
    if len(_LOG) > 80:
        del _LOG[:40]


def recent_logs(n: int = 12) -> list:
    return list(_LOG[-n:])


def ui_error(feature: str, exc: Optional[BaseException] = None, detail: str = "") -> None:
    """Friendly Streamlit error with owl personality."""
    import streamlit as st
    if exc is not None:
        log_exception(feature, exc, detail)
    st.warning(f"🦉 Couldn't load **{feature}**. Try ↻ Refresh — or open another tab.")
    if detail:
        st.caption(detail)
    if exc is not None and st.session_state.get("show_sources"):
        st.caption(str(exc)[:240])


def safe_ui(feature: str, fn: Callable[[], Any], fallback: Any = None) -> Any:
    try:
        return fn()
    except Exception as e:
        ui_error(feature, e)
        return fallback
