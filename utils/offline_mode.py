"""
Offline / cache preference helpers.

Streamlit Community Cloud cannot install a Service Worker on the parent origin
the way a custom PWA can. Offline behavior here = disk/memory cache + explicit
user messaging when live APIs fail.
"""
from __future__ import annotations
from typing import Any, Callable, Optional, Tuple

import streamlit as st

OFFLINE_BANNER = (
    "📦 **Offline / cache mode** — showing saved data when available. "
    "Live scores may lag until you turn this off and refresh."
)

FALLBACK_MSGS = {
    "scores": "🦉 Offline fallback: no live scoreboard in cache. Open Game Day after connectivity returns, or turn off Prefer cached / offline and hit ↻ Refresh.",
    "schedule": "🦉 Offline fallback: schedule not in cache. Try again online.",
    "standings": "🦉 Offline fallback: standings not in cache.",
    "news": "🦉 Offline fallback: headlines not in cache.",
    "odds": "🦉 Offline fallback: odds snapshot unavailable offline.",
    "generic": "🦉 Offline fallback: this feed is empty in cache. Reconnect and refresh.",
}


def offline_enabled() -> bool:
    return bool(st.session_state.get("offline_mode"))


def show_offline_banner() -> None:
    if offline_enabled():
        st.info(OFFLINE_BANNER)


def offline_empty(feature: str = "generic") -> None:
    st.warning(FALLBACK_MSGS.get(feature) or FALLBACK_MSGS["generic"])


def try_cached_or_message(
    feature: str,
    loader: Callable[[], Tuple[Any, str]],
    empty_test: Optional[Callable[[Any], bool]] = None,
) -> Tuple[Any, str]:
    """
    Run loader; on failure or empty while offline, show explicit fallback message.
    """
    try:
        data, src = loader()
    except Exception as e:
        if offline_enabled():
            offline_empty(feature)
            st.caption(f"cache miss · {type(e).__name__}")
            return ([] if feature != "info" else {}), f"offline-error:{feature}"
        raise
    is_empty = empty_test(data) if empty_test else (not data)
    if is_empty and offline_enabled():
        offline_empty(feature)
        return data, src or f"offline-empty:{feature}"
    return data, src
