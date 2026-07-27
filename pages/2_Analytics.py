"""Analytics — standings, trends, leaders, greats, player cards."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.nav_state import remember_page
from utils.app_shell import page_setup, src_note, render_page_footer
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
team_cfg = enrich_team_cfg(team_key, team)

st.markdown(f"**{flavor.get('slogan','')}** — _{flavor.get('witty','')}_")
tabs = st.tabs(["Standings", "Form", "Leaders", "Greats", "Players"])

with tabs[0]:
    try:
        rows, src = cached_standings(team_key)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Standings unavailable.")
        src_note(src)
    except Exception as e:
        ui_error("Standings", e)

with tabs[1]:
    try:
        form, src = cached_form(team_key)
        if form:
            n = st.slider("Games", 3, max(3, len(form)), min(10, len(form)), key="form_n")
            rows = []
            for g in form[:n]:
                def _n(v):
                    s = format_score(v)
                    try:
                        return int(float(s)) if s not in ("–", "-", "") else 0
                    except Exception:
                        return 0
                hs, aws = _n(g.get("home_score")), _n(g.get("away_score"))
                rows.append({
                    "Matchup": (g.get("name") or "")[:40],
                    "Away": aws, "Home": hs, "Total": aws + hs,
                    "Date": (g.get("date") or "")[:10],
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if len(df) >= 2:
                fig = px.bar(df, x="Date", y="Total", title=f"{team.get('short')} combined points")
                fig.update_layout(height=320)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent form.")
        src_note(src)
    except Exception as e:
        ui_error("Form", e)

with tabs[2]:
    try:
        leaders, lsrc = get_all_time_leaders(team_key)
        if leaders:
            cat = st.selectbox("Category", list(leaders.keys()), key="lead_cat")
            st.dataframe(pd.DataFrame(leaders.get(cat) or []), use_container_width=True, hide_index=True)
        else:
            st.info("No leaders table.")
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
        pool = list(PLAYER_POOL.get(team_key, []) or [])
        names = []
        for p in roster or []:
            if p.get("name"):
                names.append(p["name"])
        names = sorted(set(names + pool))
        if not names:
            names = ["Jim Brown", "LeBron James", "José Ramírez"]  # safe demo names for CLE teams
            st.caption("Live roster empty — showing legend shortcuts.")
        player = st.selectbox("Select player", ["—"] + names, key=f"player_sel_{team_key}")
        if player and player != "—":
            with st.spinner(f"Building card for {player}…"):
                try:
                    card, csrc = get_player_card(player, team_cfg)
                except Exception as e:
                    card, csrc = {
                        "name": player,
                        "team": team.get("short"),
                        "position": "",
                        "description": str(e)[:200],
                        "anecdote": "",
                        "thumb": None,
                        "cutout": None,
                    }, f"error:{e}"
            thumb = card.get("cutout") or card.get("thumb")
            if not thumb:
                try:
                    thumb = cartoon_data_uri(
                        player,
                        card.get("position") or "",
                        (team.get("colors") or {}).get("primary", "#FF5A00"),
                    )
                except Exception:
                    thumb = None
            img = f'<img class="bb-photo" src="{thumb}" alt="{player}"/>' if thumb else ""
            anecdote = (card.get("anecdote") or "").replace('"', "'")
            desc = (card.get("description") or "")[:320].replace('"', "'")
            years = card.get("best_years") or ""
            pos = card.get("position") or "Player"
            num = card.get("number") or ""
            st.markdown(
                f'<div class="bb-card">{img}'
                f'<div class="bb-name">{card.get("name", player)}</div>'
                f'<div class="bb-team">{card.get("team") or team.get("short")} · {pos}'
                f'{(" · #" + str(num)) if num else ""}</div>'
                f'{f"<span class=bb-years>BEST YEARS · {years}</span>" if years else ""}'
                f'<div class="bb-stats">{desc}</div>'
                f'<div class="bb-anecdote"><strong>Fun fact:</strong> {anecdote}</div></div>',
                unsafe_allow_html=True,
            )
            stats = card.get("stats") or {}
            if isinstance(stats, dict) and stats:
                st.markdown("**Stats**")
                for k, v in list(stats.items())[:12]:
                    st.markdown(f"- **{k}:** {v}")
            extras = []
            for k in ("nationality", "birth"):
                if card.get(k):
                    extras.append(f"**{k.title()}:** {card[k]}")
            for line in extras:
                st.markdown(f"- {line}")
            src_note(csrc)
        src_note(rsrc)
    except Exception as e:
        ui_error("Players", e)
        if st.session_state.get("show_sources"):
            st.exception(e)

render_page_footer()
