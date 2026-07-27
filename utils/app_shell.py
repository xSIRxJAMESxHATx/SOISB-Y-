"""Shared multipage shell: sidebar, theme, client, offline banner."""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional

import streamlit as st

from utils.api_client import TEAMS, get_client
from utils.theme import inject_css
from utils.api_extras import enrich_team_cfg
from utils.team_flavor import get_flavor
from utils.community import AVATAR_PRESETS, avatar_url
from utils.offline_mode import show_offline_banner
from utils.nav_state import remember_page


def bootstrap_secrets() -> None:
    for key in (
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER",
        "MOD_PASSWORD", "ODDS_API_KEY", "SUPABASE_URL", "SUPABASE_KEY",
        "SUPABASE_ANON_KEY", "REDIS_URL",
    ):
        try:
            val = st.secrets.get(key, "")
            if val and not os.environ.get(key):
                os.environ[key] = str(val)
        except Exception:
            pass


def init_state() -> None:
    defaults = {
        "team_key": "browns",
        "dark_mode": False,
        "auto_refresh": True,
        "refresh_sec": 45,
        "odds_key_input": "",
        "selected_player": None,
        "rushmore_picks": None,
        "show_sources": False,
        "username": "Fan",
        "avatar_preset": "initials",
        "offline_mode": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar() -> str:
    """Always-available sidebar (Streamlit ☰). Returns team_key."""
    with st.sidebar:
        st.markdown("## 🦉 SO!SB!Y!")
        try:
            st.image("assets/favicon.png", width=56)
        except Exception:
            try:
                st.image("assets/icons/favicon-32.png", width=48)
            except Exception:
                st.write("🦉")
        st.caption("☰ Always open this menu on phone for team & settings")

        st.page_link("app.py", label="🏠 Home", icon="🏠")
        st.page_link("pages/1_Game_Day.py", label="🏈 Game Day", icon="🏈")
        st.page_link("pages/2_Analytics.py", label="📊 Analytics", icon="📊")
        st.page_link("pages/3_Betting_Lab.py", label="🧪 Betting Lab", icon="🧪")
        st.page_link("pages/4_Fan_Zone.py", label="🦉 Fan Zone", icon="🦉")
        st.page_link("pages/5_Alerts.py", label="🔔 Alerts", icon="🔔")

        st.divider()
        team_options = {v["short"]: k for k, v in TEAMS.items()}
        labels = list(team_options.keys())
        try:
            idx = list(team_options.values()).index(st.session_state.team_key)
        except ValueError:
            idx = 0
        sel = st.selectbox("🏈 Team", labels, index=idx, key="sidebar_team")
        st.session_state.team_key = team_options[sel]

        st.session_state.dark_mode = st.toggle("🌙 Dark", st.session_state.dark_mode, key="sb_dark")
        st.session_state.auto_refresh = st.toggle("🔄 Auto-refresh", st.session_state.auto_refresh, key="sb_auto")
        st.session_state.refresh_sec = st.slider("Refresh sec", 30, 90, st.session_state.refresh_sec, 5, key="sb_ref")
        st.session_state.offline_mode = st.toggle(
            "📦 Prefer cached / offline",
            st.session_state.get("offline_mode", False),
            key="sb_off",
            help="When on, show disk-cached data and skip some live calls when possible.",
        )

        with st.expander("👤 Profile"):
            st.session_state.username = st.text_input("Username", st.session_state.username, max_chars=40, key="sb_user")
            opts = ["initials"] + list(AVATAR_PRESETS)
            try:
                ai = opts.index(st.session_state.avatar_preset)
            except ValueError:
                ai = 0
            st.session_state.avatar_preset = st.selectbox("Avatar", opts, index=ai, key="sb_av")
            try:
                st.image(avatar_url(st.session_state.username, st.session_state.avatar_preset), width=56)
            except Exception:
                pass

        with st.expander("⚙️ Settings / API"):
            st.session_state.odds_key_input = st.text_input(
                "Odds API key",
                value=st.session_state.odds_key_input,
                type="password",
                key="sb_odds",
            )
            st.session_state.show_sources = st.toggle("Show sources", st.session_state.show_sources, key="sb_src")
            st.caption("Educational sandbox only — not a bookmaker.")

        st.caption("Read-only app · Community posts only")
    return st.session_state.team_key


def page_setup(title: str = "SO!SB!Y!") -> tuple:
    """Call at top of every page. Returns (team_key, team, client, flavor)."""
    st.set_page_config(
        page_title=title,
        page_icon="assets/favicon.png",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    bootstrap_secrets()
    init_state()
    team_key = render_sidebar()
    inject_css(team_key, st.session_state.dark_mode)
    client = get_client()
    odds = st.session_state.odds_key_input or os.environ.get("ODDS_API_KEY", "")
    if odds:
        try:
            client.set_odds_key(odds)
        except Exception:
            pass
    team = TEAMS.get(team_key) or TEAMS["browns"]
    flavor = get_flavor(team_key)
    show_offline_banner()
    return team_key, team, client, flavor


def src_note(s: str) -> None:
    if st.session_state.get("show_sources"):
        st.caption(f"source: {s}")


def header_bar(team: dict, flavor: dict, live: bool = False) -> None:
    live_h = "🔴 LIVE" if live else (flavor.get("icon") or "🦉")
    c1, c2, c3 = st.columns([1, 3.5, 1.2])
    with c1:
        try:
            st.image("assets/superb_owl_icon.png", width=88)
        except Exception:
            st.write("🦉")
    with c2:
        st.markdown(
            f'<div class="sbsby-banner"><h1>Superb Owl! Super Browns! Yeah!</h1>'
            f'<p class="subtitle">SO!SB!Y! · {team.get("name","")} · {live_h}</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.caption(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
        if st.button("↻ Refresh", use_container_width=True, key="hdr_ref"):
            try:
                get_client().clear_cache()
            except Exception:
                pass
            st.rerun()
