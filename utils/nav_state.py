"""Session-state navigation helpers for multipage SO!SB!Y!"""
from __future__ import annotations
from typing import Optional

import streamlit as st

# Canonical page keys → paths (relative to app root)
PAGE_PATHS = {
    "home": "app.py",
    "game_day": "pages/1_Game_Day.py",
    "analytics": "pages/2_Analytics.py",
    "betting": "pages/3_Betting_Lab.py",
    "fan": "pages/4_Fan_Zone.py",
    "alerts": "pages/5_Alerts.py",
}


def remember_page(key: str) -> None:
    st.session_state["last_page"] = key
    hist = st.session_state.get("nav_history") or []
    if not hist or hist[-1] != key:
        hist = (hist + [key])[-12:]
    st.session_state["nav_history"] = hist


def last_page() -> str:
    return st.session_state.get("last_page") or "home"


def nav_history() -> list:
    return list(st.session_state.get("nav_history") or [])


def switch_to(key: str) -> None:
    """Navigate using Streamlit's switch_page when available."""
    path = PAGE_PATHS.get(key)
    if not path:
        st.error(f"Unknown page key: {key}")
        return
    remember_page(key)
    try:
        st.switch_page(path)
    except Exception:
        st.page_link(path, label=f"Open {key}")
        st.info(f"Use the link above or the sidebar to open **{key}**.")
