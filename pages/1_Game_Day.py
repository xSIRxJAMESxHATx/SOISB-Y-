"""Game Day — scores, schedule, news, watch, weather."""
from __future__ import annotations
import streamlit as st
import pandas as pd

from utils.nav_state import remember_page
from utils.app_shell import page_setup, src_note
from utils.cached_feeds import cached_scoreboard, cached_schedule, cached_news
from utils.scorecard import render_score_card, format_score_pair
from utils.api_client import reddit_url
from utils.weather import fetch_weather, map_links
from utils.media_sources import get_media_for_team
from utils.ws_feeds import live_score_tick, merge_ws_payload_into_games
from utils.error_handler import ui_error

remember_page("game_day")
team_key, team, client, flavor = page_setup("Game Day · SO!SB!Y!")
try:
    from streamlit_autorefresh import st_autorefresh
    if st.session_state.get("auto_refresh") and st_autorefresh:
        st_autorefresh(interval=int(st.session_state.refresh_sec) * 1000, key="gd_auto")
except Exception:
    pass

live = False
try:
    live = client.any_live_games(team_key)
except Exception:
    pass
st.markdown(f"**{flavor.get('slogan','')}** — _{flavor.get('witty','')}_")
tabs = st.tabs(["Scores", "Schedule", "News", "Watch", "Weather"])

with tabs[0]:
    st.caption("Last final + next game when nothing is live")
    try:
        st.markdown(f"[Reddit: {team.get('short')}]({reddit_url(team_key)})")
    except Exception:
        pass
    try:
        if st.session_state.get("auto_refresh") and not st.session_state.get("offline_mode"):
            tick = live_score_tick(client, team_key)
            games, src = tick.get("games") or [], tick.get("source") or "tick"
        else:
            games, src = cached_scoreboard(team_key)
        try:
            games = merge_ws_payload_into_games(games or [])
        except Exception:
            pass
        if not games:
            st.info("No score rows — try Refresh.")
        for g in games or []:
            st.markdown(render_score_card(g), unsafe_allow_html=True)
        src_note(src)
    except Exception as e:
        ui_error("Scores", e)

with tabs[1]:
    try:
        games, src = cached_schedule(team_key)
        rows = []
        for g in games or []:
            rows.append({
                "When": (g.get("date") or "")[:16].replace("T", " "),
                "Matchup": g.get("name") or f"{g.get('away_team','')} @ {g.get('home_team','')}",
                "Venue": g.get("venue") or "",
                "Status": g.get("status") or "",
                "Score": format_score_pair(g.get("away_score"), g.get("home_score")),
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Schedule empty.")
        src_note(src)
    except Exception as e:
        ui_error("Schedule", e)

with tabs[2]:
    try:
        arts, src = cached_news(team_key, 16)
        for a in arts or []:
            st.markdown(f"**[{a.get('headline')}]({a.get('url') or '#'})**")
            st.caption(" · ".join(filter(None, [a.get("source") or "", (a.get("published") or "")[:16]])))
        if not arts:
            st.info("No headlines.")
        src_note(src)
    except Exception as e:
        ui_error("News", e)

with tabs[3]:
    try:
        media = get_media_for_team(team_key, team.get("name") or "")
        for cat, items in (media or {}).items():
            st.markdown(f"#### {cat}")
            for it in items:
                st.markdown(f"- [{it.get('name')}]({it.get('url')}) — {it.get('note','')}")
    except Exception as e:
        ui_error("Watch", e)

with tabs[4]:
    try:
        wx, wsrc = fetch_weather(team_key)
        st.metric("Temperature", f"{wx.get('temp_f')} °F")
        st.metric("Conditions", str(wx.get("summary") or "—"))
        for m in map_links(float(wx.get("lat") or 41.5), float(wx.get("lon") or -81.7)):
            st.markdown(f"- [{m['name']}]({m['url']})")
        src_note(wsrc)
    except Exception as e:
        ui_error("Weather", e)
