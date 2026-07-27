"""st.cache_data wrappers around pure fetch helpers for faster multipage loads."""
from __future__ import annotations
from typing import Any, List, Tuple

import streamlit as st

from utils.api_client import get_client
from utils.offline_mode import offline_enabled, offline_empty


@st.cache_data(ttl=45, show_spinner=False)
def _scoreboard_raw(team_key: str) -> Tuple[List[dict], str]:
    return get_client().get_scoreboard(team_key)


def cached_scoreboard(team_key: str) -> Tuple[List[dict], str]:
    try:
        data, src = _scoreboard_raw(team_key)
    except Exception:
        if offline_enabled():
            offline_empty("scores")
            return [], "offline-error:scores"
        raise
    if not data and offline_enabled():
        offline_empty("scores")
    return data, src


@st.cache_data(ttl=180, show_spinner=False)
def cached_schedule(team_key: str) -> Tuple[List[dict], str]:
    return get_client().get_schedule(team_key)


@st.cache_data(ttl=300, show_spinner=False)
def cached_standings(team_key: str) -> Tuple[List[dict], str]:
    return get_client().get_standings(team_key)


@st.cache_data(ttl=120, show_spinner=False)
def cached_news(team_key: str, limit: int = 16) -> Tuple[List[dict], str]:
    return get_client().get_news(team_key, limit)


@st.cache_data(ttl=120, show_spinner=False)
def cached_team_info(team_key: str) -> Tuple[dict, str]:
    return get_client().get_team_info(team_key)


@st.cache_data(ttl=90, show_spinner=False)
def cached_form(team_key: str) -> Tuple[List[dict], str]:
    return get_client().get_recent_form(team_key)


@st.cache_data(ttl=60, show_spinner=False)
def cached_betting_dashboard(team_key: str) -> Tuple[dict, str]:
    return get_client().get_betting_dashboard(team_key)


def clear_feed_caches() -> None:
    cached_scoreboard.clear()
    cached_schedule.clear()
    cached_standings.clear()
    cached_news.clear()
    cached_team_info.clear()
    cached_form.clear()
    cached_betting_dashboard.clear()
