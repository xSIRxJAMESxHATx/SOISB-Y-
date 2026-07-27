"""
SO!SB!Y! Home — Superb Owl! Super Browns! Yeah!
"""
from __future__ import annotations

import streamlit as st

from utils.nav_state import remember_page
from utils.app_shell import page_setup, src_note, render_page_footer
from utils.cached_feeds import cached_scoreboard, cached_team_info
from utils.scorecard import render_score_card
from utils.error_handler import ui_error
from utils.fan_links import fan_links_for

remember_page("home")
team_key, team, client, flavor = page_setup("SO!SB!Y!")
try:
    from streamlit_autorefresh import st_autorefresh
    if st.session_state.get("auto_refresh") and st_autorefresh:
        st_autorefresh(interval=int(st.session_state.refresh_sec) * 1000, key="home_auto")
except Exception:
    pass

st.markdown(f"**{flavor.get('slogan','')}** — _{flavor.get('witty','')}_")

try:
    info, isrc = cached_team_info(team_key)
except Exception:
    info, isrc = {"record": "—", "logo": None}, "err"

m1, m2, m3, m4 = st.columns(4)
m1.markdown(
    f'<div class="metric-pill"><div class="label">Record</div>'
    f'<div class="value">{info.get("record") or "—"}</div></div>',
    unsafe_allow_html=True,
)
m2.markdown(
    f'<div class="metric-pill"><div class="label">League</div>'
    f'<div class="value">{(team.get("league") or "").replace("-", " ").upper()[:16]}</div></div>',
    unsafe_allow_html=True,
)
m3.markdown(
    '<div class="metric-pill"><div class="label">Access</div>'
    '<div class="value">READ-ONLY</div></div>',
    unsafe_allow_html=True,
)
with m4:
    if info.get("logo"):
        try:
            st.image(info["logo"], width=48)
        except Exception:
            st.write(team.get("short"))
    else:
        st.write(team.get("short"))
src_note(isrc)

st.markdown("#### Live / latest scores")
try:
    games, src = cached_scoreboard(team_key)
    if not games:
        st.info("No games in snapshot — open Game Day.")
    for g in (games or [])[:4]:
        st.markdown(render_score_card(g), unsafe_allow_html=True)
    src_note(src)
except Exception as e:
    ui_error("Home scores", e)

st.markdown("#### Fan pages & Reddit")
for link in fan_links_for(team_key):
    st.markdown(f"- [{link['name']}]({link['url']})")

render_page_footer()
