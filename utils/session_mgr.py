"""Central session-state helpers for SO!SB!Y! multipage app."""
from __future__ import annotations
from typing import Any, Optional

import streamlit as st

DEFAULTS = {
    "team_key": "browns",
    "ephemeral_team": None,  # full cfg when not in TEAMS
    "dark_mode": False,
    "auto_refresh": True,
    "refresh_sec": 45,
    "odds_key_input": "",
    "show_sources": False,
    "username": "Fan",
    "avatar_preset": "initials",
    "offline_mode": False,
    "sidebar_expanded": True,
    "custom_sidebar_open": True,
}


def ensure_defaults() -> None:
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_active_team_cfg(teams_dict: dict) -> tuple:
    """
    Returns (team_key, team_cfg).
    Uses ephemeral catalog team when selected.
    """
    ensure_defaults()
    eph = st.session_state.get("ephemeral_team")
    key = st.session_state.get("team_key") or "browns"
    if eph and isinstance(eph, dict) and eph.get("espn_id"):
        # active external team
        return f"ext_{eph.get('espn_id')}", eph
    if key in teams_dict:
        return key, teams_dict[key]
    return "browns", teams_dict.get("browns") or {}


def set_core_team(key: str) -> None:
    st.session_state.team_key = key
    st.session_state.ephemeral_team = None


def set_ephemeral_team(cfg: dict) -> None:
    st.session_state.ephemeral_team = cfg
    st.session_state.team_key = f"ext_{cfg.get('espn_id')}"
