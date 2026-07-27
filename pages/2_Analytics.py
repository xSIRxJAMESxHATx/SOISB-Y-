"""Analytics — standings, trends, leaders, greats, players."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.nav_state import remember_page
from utils.app_shell import page_setup, src_note, header_bar
from utils.cached_feeds import cached_standings, cached_form
from utils.api_extras import (
    get_roster, get_all_time_leaders, get_championship_greats,
    get_player_card, enrich_team_cfg,
)
from utils.curated_data import PLAYER_POOL
from utils.cartoon import cartoon_data_uri
from utils.error_handler import ui_error
from utils.scorecard import format_score

remember_page("analytics")
team_key, team, client, flavor = page_setup("Analytics · SO!SB!Y!")
header_bar(team, flavor)
team_cfg = enrich_team_cfg(team_key, team)
tabs = st.tabs(["Standings", "Trends", "Leaders", "Greats", "Players"])

with tabs[0]:
    try:
        rows, src = cached_standings(team_key)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Standings unavailable.")
        src_note(src)
    except Exception as e:
        ui_error("Standings", e)

with tabs[1]:
    try:
        form, src = cached_form(team_key)
        if form:
            rows = []
            for g in form:
                def _n(v):
                    s = format_score(v)
                    try:
                        return int(float(s)) if s != "–" else 0
                    except Exception:
                        return 0
                hs, aws = _n(g.get("home_score")), _n(g.get("away_score"))
                rows.append({
                    "Matchup": g.get("name") or "",
                    "Away": aws, "Home": hs, "Total": aws + hs,
                    "Date": (g.get("date") or "")[:10],
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if len(df) >= 2:
                fig = px.bar(df, x="Date", y="Total", title=f"{team.get('short')} points")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent form.")
        src_note(src)
    except Exception as e:
        ui_error("Trends", e)

with tabs[2]:
    try:
        leaders, lsrc = get_all_time_leaders(team_key)
        if leaders:
            cat = st.selectbox("Category", list(leaders.keys()))
            st.dataframe(pd.DataFrame(leaders.get(cat) or []), use_container_width=True, hide_index=True)
        src_note(lsrc)
    except Exception as e:
        ui_error("Leaders", e)

with tabs[3]:
    try:
        greats, gsrc = get_championship_greats(team_key)
        for g in greats or []:
            st.markdown(f"**{g.get('player')}** · {g.get('era','')} — {g.get('titles','')} · _{g.get('why','')}_")
        src_note(gsrc)
    except Exception as e:
        ui_error("Greats", e)

with tabs[4]:
    try:
        roster, rsrc = get_roster(team_cfg)
        pool = PLAYER_POOL.get(team_key, [])
        options = sorted(set([p.get("name") for p in roster if p.get("name")] + list(pool or []))) or ["(none)"]
        player = st.selectbox("Player", options)
        if player and player != "(none)":
            card, csrc = get_player_card(player, team_cfg)
            thumb = card.get("cutout") or card.get("thumb")
            if not thumb:
                try:
                    thumb = cartoon_data_uri(
                        player, card.get("position") or "",
                        team.get("colors", {}).get("primary", "#311D00"),
                    )
                except Exception:
                    thumb = None
            img = f'<img class="bb-photo" src="{thumb}" alt="p"/>' if thumb else ""
            anecdote = (card.get("anecdote") or "").replace('"', "'")
            st.markdown(
                f'<div class="bb-card">{img}'
                f'<div class="bb-name">{card.get("name", player)}</div>'
                f'<div class="bb-team">{card.get("team") or team.get("short")}</div>'
                f'<div class="bb-stats">{(card.get("description") or "")[:280]}</div>'
                f'<div class="bb-anecdote">{anecdote}</div></div>',
                unsafe_allow_html=True,
            )
            src_note(csrc)
        src_note(rsrc)
    except Exception as e:
        ui_error("Players", e)
