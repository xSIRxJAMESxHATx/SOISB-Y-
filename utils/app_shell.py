"""Shared multipage shell — banner above nav, on-page odds key, reliable navigation."""
from __future__ import annotations
import os
from datetime import datetime, timezone

import streamlit as st

from utils.api_client import TEAMS, get_client, register_team
from utils.theme import inject_css
from utils.team_flavor import get_flavor
from utils.community import AVATAR_PRESETS, avatar_url
from utils.offline_mode import show_offline_banner
from utils.nav_state import last_page
from utils.client_store import inject_client_store
from utils.session_mgr import ensure_defaults, get_active_team_cfg, set_core_team, set_ephemeral_team
from utils.league_catalog import search_catalog, catalog_to_team_cfg
from utils.team_search import search_teams

QUICK_TEAMS = [
    ("browns", "Browns"),
    ("guardians", "Guardians"),
    ("cavaliers", "Cavs"),
    ("osu_football", "OSU FB"),
    ("osu_mbb", "OSU MBB"),
    ("crew", "Crew"),
    ("bluejackets", "CBJ"),
]


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


def header_bar(team: dict, flavor: dict, live: bool = False) -> None:
    """Banner strip — call FIRST so it sits above navigation."""
    live_h = "LIVE" if live else (flavor.get("icon") or "OWL")
    c1, c2, c3 = st.columns([1.1, 3.4, 1.2])
    with c1:
        try:
            st.image("assets/superb_owl_icon.png", width=120)
        except Exception:
            st.write("OWL")
    with c2:
        st.markdown(
            f'<div class="sbsby-banner"><h1>Superb Owl! Super Browns! Yeah!</h1>'
            f'<p class="subtitle">SO!SB!Y! · {team.get("name","")} · {live_h}</p></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.caption(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
        if st.button("Refresh", use_container_width=True, key="hdr_ref"):
            try:
                get_client().clear_cache()
            except Exception:
                pass
            st.rerun()
        st.page_link("app.py", label="Back to Home")


def render_main_nav() -> None:
    """Always-on navigation (works when Streamlit sidebar is collapsed)."""
    st.markdown("##### Menu · pages")
    cols = st.columns(6)
    for col, (path, label) in zip(cols, [
        ("app.py", "Home"),
        ("pages/1_Game_Day.py", "Game Day"),
        ("pages/2_Analytics.py", "Analytics"),
        ("pages/3_Betting_Lab.py", "Betting Lab"),
        ("pages/4_Fan_Zone.py", "Fan Zone"),
        ("pages/5_Alerts.py", "Alerts"),
    ]):
        with col:
            st.page_link(path, label=label)

    with st.expander("Show menu help (if sidebar vanished)", expanded=False):
        st.markdown(
            """
**Phone / desktop:** Streamlit's **☰** is usually top-right of the app chrome.
This **Menu · pages** row always stays on the page — you never need the sidebar to move around.

**Sidebar** still holds profile + advanced toggles. Use **Menu · pages** for navigation.
            """
        )

    st.markdown("**Quick teams**")
    qcols = st.columns(len(QUICK_TEAMS))
    for i, (key, label) in enumerate(QUICK_TEAMS):
        with qcols[i]:
            if st.button(label, key=f"qt_{key}", use_container_width=True):
                set_core_team(key)
                st.rerun()

    with st.expander("Search league teams (NFL/MLB/NBA/NHL/MLS/NCAA)", expanded=False):
        q = st.text_input("Search team name", key="cat_q", placeholder="Penguins, Galaxy, Wolverines…")
        if q and len(q) >= 2:
            try:
                hits = search_catalog(q, limit=25)
            except Exception as e:
                st.warning(f"Catalog unavailable: {e}")
                hits = []
            if hits:
                labels = [f"{h.get('name')} · {h.get('league_key')}" for h in hits]
                pick = st.selectbox("Matches", labels, key="cat_pick")
                if st.button("Load team", key="cat_go"):
                    row = hits[labels.index(pick)]
                    cfg = catalog_to_team_cfg(row)
                    key = f"ext_{cfg['espn_id']}"
                    register_team(key, cfg)
                    set_ephemeral_team(cfg)
                    st.success(f"Loaded {cfg['name']}")
                    st.rerun()

    with st.expander("Core roster search", expanded=False):
        q2 = st.text_input("Core teams only", key="core_q")
        hits2 = search_teams(q2) if q2 else []
        if hits2:
            lab2 = [h[1] for h in hits2]
            p2 = st.selectbox("Core results", lab2, key="core_pick")
            if st.button("Go core team", key="core_go"):
                for k, lab in hits2:
                    if lab == p2:
                        set_core_team(k)
                        st.rerun()
                        break


def render_odds_key_panel() -> None:
    """Odds API key on the main page — not buried in sidebar."""
    with st.container():
        st.markdown("##### Odds API (Betting Lab)")
        a, b = st.columns([3, 2])
        with a:
            st.session_state.odds_key_input = st.text_input(
                "Paste free key from the-odds-api.com",
                value=st.session_state.get("odds_key_input") or "",
                type="password",
                key="main_odds_key",
                help="Free tier available. Used only for educational lab lines.",
            )
        with b:
            st.markdown("[Get free Odds API key](https://the-odds-api.com/)")
            st.caption("Also works via Streamlit Secrets → ODDS_API_KEY")


def render_sidebar() -> None:
    with st.sidebar:
        try:
            st.image("assets/superb_owl_icon.png", width=80)
        except Exception:
            st.write("OWL")
        st.markdown("## SO!SB!Y!")
        st.caption("Optional panel · main Menu is on the page")

        st.page_link("app.py", label="Home")
        st.page_link("pages/1_Game_Day.py", label="Game Day")
        st.page_link("pages/2_Analytics.py", label="Analytics")
        st.page_link("pages/3_Betting_Lab.py", label="Betting Lab")
        st.page_link("pages/4_Fan_Zone.py", label="Fan Zone")
        st.page_link("pages/5_Alerts.py", label="Alerts")

        st.divider()
        team_options = {v["short"]: k for k, v in TEAMS.items()}
        labels = list(team_options.keys())
        cur = st.session_state.get("team_key") or "browns"
        try:
            idx = list(team_options.values()).index(cur) if not str(cur).startswith("ext_") else 0
        except ValueError:
            idx = 0
        sel = st.selectbox("Core list", labels, index=idx, key="sidebar_core")
        if st.button("Apply core team", key="sb_apply"):
            set_core_team(team_options[sel])
            st.rerun()

        st.session_state.dark_mode = st.toggle("Dark", st.session_state.dark_mode, key="sb_dark")
        st.session_state.auto_refresh = st.toggle("Auto-refresh", st.session_state.auto_refresh, key="sb_auto")
        st.session_state.refresh_sec = st.slider("Refresh sec", 30, 90, st.session_state.refresh_sec, 5, key="sb_ref")
        st.session_state.offline_mode = st.toggle("Prefer cached / offline", st.session_state.offline_mode, key="sb_off")

        with st.expander("Profile"):
            st.session_state.username = st.text_input("Username", st.session_state.username, max_chars=40, key="sb_user")
            opts = ["initials"] + list(AVATAR_PRESETS)
            try:
                ai = opts.index(st.session_state.avatar_preset)
            except ValueError:
                ai = 0
            st.session_state.avatar_preset = st.selectbox("Avatar", opts, index=ai, key="sb_av")

        st.caption("Educational lab · read-only shell")


def page_setup(title: str = "SO!SB!Y!") -> tuple:
    bootstrap_secrets()
    ensure_defaults()
    st.set_page_config(
        page_title=title,
        page_icon="assets/favicon.png",
        layout="wide",
        initial_sidebar_state="collapsed",  # page Menu is primary; sidebar optional
    )
    render_sidebar()
    team_key, team = get_active_team_cfg(TEAMS)
    if team_key.startswith("ext_") and team:
        register_team(team_key, team)
    inject_css("browns" if team_key.startswith("ext_") else (team_key if team_key in TEAMS else "browns"), st.session_state.dark_mode)

    flavor = get_flavor(team_key if team_key in TEAMS else "browns")
    if team.get("ephemeral"):
        flavor = {
            **flavor,
            "slogan": team.get("name"),
            "witty": "League catalog team · same feeds when ESPN allows",
            "phrases": [team.get("short") or "", team.get("league") or ""],
        }

    # Order: BANNER → NAV → ODDS KEY
    live = False
    client = get_client()
    try:
        live = client.any_live_games(team_key)
    except Exception:
        pass
    header_bar(team, flavor, live)
    render_main_nav()
    render_odds_key_panel()
    show_offline_banner()

    try:
        inject_client_store(team_key, last_page())
    except Exception:
        pass

    odds = st.session_state.odds_key_input or os.environ.get("ODDS_API_KEY", "")
    if odds:
        try:
            client.set_odds_key(odds)
        except Exception:
            pass
    return team_key, team, client, flavor


def src_note(s: str) -> None:
    if st.session_state.get("show_sources"):
        st.caption(f"source: {s}")
