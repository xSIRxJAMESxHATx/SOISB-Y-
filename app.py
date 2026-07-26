"""
SO!SB!Y! — Superb Owl! Super Browns! Yeah!
Read-only public UI (users cannot modify app code). Owner updates via GitHub.
Auto-refresh ~45s for live scores. Optional Twilio SMS via secrets.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

from utils.api_client import TEAMS, get_client, reddit_url
from utils.theme import inject_css
from utils.api_extras import (
    get_roster, get_all_time_leaders, get_championship_greats,
    get_player_card, enrich_team_cfg,
)
from utils.curated_data import DEFAULT_RUSHMORE, PLAYER_POOL
from utils.rushmore import rushmore_to_bytes
from utils.betting_tools import (
    detect_arbitrage, bankroll_plan, kelly_fraction, full_kelly_table,
    LIVE_ARB_STRATEGIES, STAT_ARB_MODELS, price_dispersion, implied_edge_table,
)
from utils.media_sources import get_media_for_team
from utils.cartoon import cartoon_data_uri
from utils.team_flavor import get_flavor
from utils.weather import fetch_weather, map_links, weather_cartoon
from utils.community import (
    list_topics, create_topic, add_post, vote, delete_post, delete_topic,
    list_users, avatar_url, AVATAR_PRESETS, moderate_text, supabase_configured,
)
from utils.twilio_sms import twilio_configured, send_sms, SETUP_HELP
from utils.chatbot import reply as bot_reply
from utils.moments_tickets import moments_for, ticket_links
from utils.betting_sandbox import sandbox_single_summary, parlay_monte_carlo
from utils.bet_journal import add_entry, list_entries, clear_all, summary_stats, to_csv
from utils.betting_sandbox import (
    poisson_score_matrix, poisson_total_over_prob, monte_carlo,
    lambdas_from_form, kalman_1d,
)
from utils.pdf_export import export_team_pdf
from utils.ws_feeds import probe_websocket, sports_ws_candidates, get_owner_ws, merge_ws_payload_into_games, live_score_tick
from utils.viz3d import form_3d_scatter, poisson_surface
from utils.errors import safe_call, format_feed_status
from utils.bayes_poisson import (
    gamma_poisson_update, empirical_bayes_rates,
    hierarchical_match_preview, rates_from_form_games,
)


st.set_page_config(page_title="SO!SB!Y!", page_icon="🦉", layout="wide", initial_sidebar_state="expanded")

# Inject Twilio + mod secrets into env for helper modules
for key in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "MOD_PASSWORD", "ODDS_API_KEY", "SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_ANON_KEY"):
    try:
        val = st.secrets.get(key, "")
        if val and not os.environ.get(key):
            os.environ[key] = str(val)
    except Exception:
        pass

for k, v in {
    "team_key": "browns", "dark_mode": False, "auto_refresh": True,
    "refresh_sec": 45, "odds_key_input": "", "selected_player": None,
    "rushmore_picks": None, "show_sources": False, "username": "Fan",
    "avatar_preset": "initials",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----- Sidebar -----
with st.sidebar:
    st.markdown("## 🦉 SO!SB!Y!")
    try:
        st.image("assets/superb_owl_icon.png", width=72)
    except Exception:
        pass
    st.caption("☰ menu on mobile · team switcher · Superb Owl")
    team_options = {v["short"]: k for k, v in TEAMS.items()}
    labels = list(team_options.keys())
    try:
        idx = list(team_options.values()).index(st.session_state.team_key)
    except ValueError:
        idx = 0
    sel = st.selectbox("🏈 Team", labels, index=idx)
    st.session_state.team_key = team_options[sel]
    st.session_state.dark_mode = st.toggle("🌙 Dark Mode", st.session_state.dark_mode)
    st.session_state.auto_refresh = st.toggle("🔄 Auto-update (~45s)", st.session_state.auto_refresh)
    st.session_state.refresh_sec = st.slider("Refresh seconds", 30, 90, st.session_state.refresh_sec, 5)
    st.divider()
    st.markdown("### Profile")
    st.session_state.username = st.text_input("Username", st.session_state.username, max_chars=40)
    st.session_state.avatar_preset = st.selectbox(
        "Avatar theme", ["initials"] + AVATAR_PRESETS,
        index=(["initials"] + AVATAR_PRESETS).index(st.session_state.avatar_preset)
        if st.session_state.avatar_preset in (["initials"] + AVATAR_PRESETS) else 0,
    )
    st.image(avatar_url(st.session_state.username, st.session_state.avatar_preset), width=64)
    st.divider()
    st.markdown("### 🔑 Odds API")
    st.session_state.odds_key_input = st.text_input(
        "The Odds API key", value=st.session_state.odds_key_input, type="password",
        placeholder="the-odds-api.com",
    )
    st.session_state.show_sources = st.toggle("Show data sources", st.session_state.show_sources)
    st.caption("Public users: navigate & post in Community only. App code is read-only.")

team_key = st.session_state.team_key
inject_css(team_key, st.session_state.dark_mode)

if st.session_state.auto_refresh and st_autorefresh:
    st_autorefresh(interval=int(st.session_state.refresh_sec) * 1000, key="sbsby_auto")

client = get_client()
odds_key = st.session_state.odds_key_input or os.environ.get("ODDS_API_KEY", "")
if odds_key:
    client.set_odds_key(odds_key)

team = TEAMS[team_key]
team_cfg = enrich_team_cfg(team_key, team)
flavor = get_flavor(team_key)

def src_note(s: str) -> None:
    if st.session_state.show_sources:
        st.caption(f"source: {s}")

# Banner + always-visible team switcher (works when sidebar collapsed)
live = False
try:
    live = client.any_live_games(team_key)
except Exception:
    pass
live_h = '<span class="live-dot"></span>LIVE' if live else (flavor.get("icon") or "🦉") + " Hub"

b_left, b_mid, b_right = st.columns([1, 3.2, 1.4])
with b_left:
    try:
        st.image("assets/superb_owl_icon.png", width=96)
    except Exception:
        st.write("🦉")
    st.caption("Superb Owl")
with b_mid:
    st.markdown(f"""
    <div class="sbsby-banner">
      <h1>Superb Owl! Super Browns! Yeah!</h1>
      <p class="subtitle">SO!SB!Y! · {team['name']} · {live_h}</p>
    </div>""", unsafe_allow_html=True)
with b_right:
    st.markdown("##### Switch team")
    team_options = {v["short"]: k for k, v in TEAMS.items()}
    labels = list(team_options.keys())
    try:
        cur_i = list(team_options.values()).index(team_key)
    except ValueError:
        cur_i = 0
    pick = st.selectbox("Team", labels, index=cur_i, key="main_team_switch", label_visibility="collapsed")
    new_key = team_options[pick]
    if new_key != st.session_state.team_key:
        st.session_state.team_key = new_key
        st.session_state.selected_player = None
        st.rerun()

st.markdown(f"**{flavor.get('slogan','')}** — _{flavor.get('witty','')}_")
if flavor.get("phrases"):
    st.caption(" · ".join(flavor["phrases"][:8]))

c1, c2, c3 = st.columns([2.2, 1, 1])
with c1:
    st.markdown(f"### {team['name']}")
with c2:
    if st.button("↻ Refresh now", use_container_width=True):
        try:
            client.clear_cache()
        except Exception:
            pass
        st.rerun()
with c3:
    st.caption(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

try:
    info, info_src = client.get_team_info(team_key)
except Exception:
    info, info_src = {"record": "—", "logo": None}, "err"
record = info.get("record") or "—"

# PDF export (after record/scores sources are available)
try:
    _games_pdf, _ = client.get_scoreboard(team_key)
    _std_pdf, _ = client.get_standings(team_key)
    _news_pdf, _ = client.get_news(team_key, 8)
    try:
        _j = list_entries(50)
    except Exception:
        _j = []
    pdf_bytes = export_team_pdf(
        team.get("name") or team_key,
        record,
        _games_pdf,
        _std_pdf,
        _news_pdf,
        _j,
    )
    st.download_button(
        "📄 Export PDF report",
        data=pdf_bytes,
        file_name=f"sosby_{team_key}_report.pdf",
        mime="application/pdf",
    )
except Exception:
    pass

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-pill"><div class="label">Record</div><div class="value">{record}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-pill"><div class="label">League</div><div class="value">{team["league"].replace("-"," ").upper()[:18]}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-pill"><div class="label">Access</div><div class="value">READ-ONLY</div></div>', unsafe_allow_html=True)
with m4:
    logo = info.get("logo")
    if logo:
        try:
            st.image(logo, width=52)
        except Exception:
            st.write(team["short"])
    else:
        st.write(team["short"])
src_note(info_src)

# Team iconography / lingo strip
ph = flavor.get("phrases") or []
icon = flavor.get("icon") or "🦉"
st.markdown(
    f'<div class="sbsby-card" style="padding:.65rem 1rem;display:flex;flex-wrap:wrap;gap:.4rem;align-items:center">'
    f'<span style="font-size:1.6rem">{icon}</span>'
    f'<strong style="color:inherit">{team.get("short")}</strong>'
    + "".join(f'<span class="odds-chip">{p}</span>' for p in ph[:8])
    + '</div>',
    unsafe_allow_html=True,
)
if info.get("logo"):
    try:
        lc1, lc2, lc3 = st.columns([1, 1, 4])
        with lc1:
            st.image(info["logo"], width=64)
            st.caption("Primary mark")
        with lc2:
            # secondary: reuse logo as badge treatment via caption
            st.image(info["logo"], width=40)
            st.caption("Secondary / badge")
    except Exception:
        pass

tabs = st.tabs([
    "🏈 Scores + Weather", "🎰 Betting HQ", "🧪 Sandbox", "💰 Odds", "📺 Watch", "📰 News",
    "📊 Standings", "📅 Schedule", "📈 Trends", "🏆 Leaders", "⭐ Greats",
    "👤 Players", "💬 Community", "🤖 Desk Bot", "🎬 Moments", "🎫 Tickets",
    "🗻 Rushmore", "📒 Journal", "🎯 Markets", "🔔 Alerts / SMS",
])

# ===== Scores + Weather =====
with tabs[0]:
    st.markdown('<div class="section-title">Live Scores</div>', unsafe_allow_html=True)
    st.caption("Auto-refreshes · last final + next game when nothing is live today")
    try:
        st.markdown(f"[Reddit: {team.get('short')}]({reddit_url(team_key)})")
    except Exception:
        pass
    try:
        # WS-style tick: refresh score cache each load when auto-refresh is on
        if st.session_state.get("auto_refresh"):
            tick = live_score_tick(client, team_key)
            games, src = tick.get("games") or [], tick.get("source") or "tick"
            if tick.get("empty"):
                st.caption("Waiting for score feed…")
        else:
            games, src = client.get_scoreboard(team_key)
        try:
            games = merge_ws_payload_into_games(games or [])
        except Exception:
            pass
        if not games:
            st.markdown('<div class="sbsby-card empty-state">Scores temporarily unavailable — try Refresh.</div>', unsafe_allow_html=True)
        for g in (games or []):
            st_state = (g.get("status_state") or "").lower()
            st_live = st_state == "in"
            is_final = st_state in ("post", "final") or "final" in str(g.get("status") or "").lower()
            label = "LIVE" if st_live else ("FINAL" if is_final else "UPCOMING")
            badge = "status-badge live" if st_live else "status-badge"
            status = g.get("detail") or g.get("status") or label
            when = (g.get("date") or "")[:16].replace("T", " ")
            venue = g.get("venue") or ""
            bcast = g.get("broadcast") or ""
            meta = " · ".join(x for x in [label, when, venue, bcast] if x)
            # link fallback detail
            detail = g.get("detail") or ""
            if str(detail).startswith("http"):
                st.markdown(f"**[{g.get('name') or 'Scores'}]({detail})**")
            st.markdown(f"""
            <div class="sbsby-card"><div class="score-card">
              <div class="team-block"><div class="score">{g.get('away_score','–')}</div><div class="name">{g.get('away_team','Away')}</div></div>
              <div style="text-align:center"><div class="vs-pill">VS</div><div class="{badge}">{status}</div></div>
              <div class="team-block"><div class="score">{g.get('home_score','–')}</div><div class="name">{g.get('home_team','Home')}</div></div>
            </div>
            <div class="source-badge">{meta}</div></div>""", unsafe_allow_html=True)
        src_note(src)
    except Exception as e:
        st.error("Scores unavailable after failover.")
        if st.session_state.show_sources:
            st.caption(str(e))

    st.markdown('<div class="section-title">Venue Weather</div>', unsafe_allow_html=True)
    try:
        wx, wsrc = fetch_weather(team_key)
        wc1, wc2 = st.columns([1, 1])
        with wc1:
            st.metric("Temperature", f"{wx.get('temp_f')} °F")
            st.metric("Conditions", str(wx.get("summary") or "—"))
            st.caption(wx.get("label") or "")
            st.caption(f"Wind {wx.get('wind_mph')} mph · Humidity {wx.get('humidity')}% · Precip {wx.get('precip')}")
            try:
                png = weather_cartoon(str(wx.get("summary") or ""), wx.get("temp_f"), float(wx.get("lat") or 41.5))
                st.image(png, use_container_width=True)
            except Exception:
                pass
        with wc2:
            st.markdown("**Maps (satellite / place)**")
            for m in map_links(float(wx.get("lat") or 41.5), float(wx.get("lon") or -81.7)):
                st.markdown(f"- [{m['name']}]({m['url']})")
        src_note(wsrc)
    except Exception as e:
        st.warning("Weather unavailable.")
        if st.session_state.show_sources:
            st.caption(str(e))

# ===== Betting HQ =====
with tabs[1]:
    st.markdown('<div class="section-title">Sports Betting Dashboard</div>', unsafe_allow_html=True)
    st.caption("Educational only — not gambling advice.")
    with st.expander("Kelly math & odds formats"):
        st.markdown("""
**American → decimal:**  
- Positive odds `+150` → `1 + 150/100 = 2.50`  
- Negative odds `-200` → `1 + 100/200 = 1.50`

**Implied probability:** `1 / decimal_odds`

**Kelly fraction:**  
`f* = (b·p − q) / b` where `b = decimal − 1`, `p` = your win prob, `q = 1 − p`.  
We show **full / half / quarter** Kelly and cap at 25% of bankroll.

| Format | Example | Meaning |
|--------|---------|---------|
| American | +150 / −200 | Profit on $100 risk / stake to win $100 |
| Decimal | 2.50 | Total return per 1 unit staked |
| Fractional | 3/2 | Profit relative to stake |
        """)

    try:
        dash, dsrc = client.get_betting_dashboard(team_key)
    except Exception:
        dash, dsrc = {"games": [], "has_api_key": bool(odds_key), "espn_lines": [], "links": client.prediction_links(team_key)}, "err"
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Odds API", "LIVE" if dash.get("has_api_key") else "KEY NEEDED")
    k2.metric("Book games", len(dash.get("games") or []))
    k3.metric("ESPN lines", len(dash.get("espn_lines") or []))
    k4.metric("Markets", len(dash.get("links") or []))
    if not dash.get("has_api_key"):
        st.warning("Add The Odds API key in the sidebar for full depth.")
    if dash.get("espn_lines"):
        st.markdown("#### ESPN lines")
        for ln in dash["espn_lines"]:
            o = ln.get("odds") or {}
            st.markdown(
                f"**{ln.get('matchup') or ''}** · "
                f"<span class='odds-chip'>Spread {o.get('spread') or '—'}</span> "
                f"<span class='odds-chip'>O/U {o.get('over_under') if o.get('over_under') is not None else '—'}</span>",
                unsafe_allow_html=True,
            )
    if dash.get("games"):
        st.markdown("#### Books")
        for og in dash["games"][:8]:
            st.markdown(f"**{og.get('away_team')} @ {og.get('home_team')}**")
            for bm in (og.get("bookmakers") or [])[:3]:
                chips = []
                for mk, outs in (bm.get("markets") or {}).items():
                    for o in outs:
                        pt = f" ({o.get('point')})" if o.get("point") is not None else ""
                        chips.append(f"<span class='odds-chip'>{mk}:{o.get('name')}{pt} {o.get('price')}</span>")
                if chips:
                    st.markdown(f"{bm.get('book')}: " + " ".join(chips), unsafe_allow_html=True)
    st.markdown("#### Arbitrage scan")
    try:
        if dash.get("has_api_key") and dash.get("games"):
            opps = detect_arbitrage(dash["games"])
            if opps:
                st.dataframe(pd.DataFrame(opps), use_container_width=True, hide_index=True)
            else:
                st.success("No ≥0.3% 2-way ML arb in snapshot.")
        else:
            st.info("Key + book data required for arb scan.")
    except Exception:
        st.warning("Arb scanner error.")
    st.markdown("#### Statistical models (education)")
    for s in STAT_ARB_MODELS:
        st.markdown(f"**{s['title']}** — {s['body']}")
    try:
        if dash.get("games"):
            disp = price_dispersion(dash["games"])
            if disp:
                st.markdown("##### Price dispersion (best vs worst ML)")
                st.dataframe(pd.DataFrame(disp), use_container_width=True, hide_index=True)
            edges = implied_edge_table(dash["games"])
            if edges:
                st.markdown("##### Best-price implied sum / edge")
                st.dataframe(pd.DataFrame(edges), use_container_width=True, hide_index=True)
    except Exception:
        pass
    for s in LIVE_ARB_STRATEGIES[:3]:
        st.markdown(f"**{s['title']}** — {s['body']}")
    st.markdown("#### Bankroll + Kelly")
    try:
        b1, b2, b3 = st.columns(3)
        br = b1.number_input("Bankroll $", 0.0, value=500.0, step=50.0)
        up = b2.number_input("Unit %", 0.25, 5.0, 1.0, 0.25)
        prof = b3.selectbox("Profile", ["conservative", "moderate", "aggressive"], 1)
        plan = bankroll_plan(br, up, prof)
        st.write(f"Unit **${plan['unit_size']}** · Max bet **${plan['max_single_bet']}** · Max daily **${plan['max_daily_risk']}**")
        dec = st.number_input("Decimal odds", 1.01, value=2.0, step=0.05)
        wp = st.slider("Win probability", 0.05, 0.95, 0.55, 0.01)
        table = full_kelly_table(dec, wp, plan["bankroll"])
        for label in ("Full Kelly", "Half Kelly", "Quarter Kelly"):
            row = table.get(label, {})
            st.metric(label, f"${row.get('stake', 0):.2f}")
    except Exception:
        st.warning("Bankroll tools error.")
    src_note(dsrc)

# ===== Odds detail =====

# Sandbox
with tabs[2]:
    st.markdown('<div class="section-title">Bet & Parlay Sandbox</div>', unsafe_allow_html=True)
    st.caption("Educational simulator — not gambling advice. No real money.")
    try:
        br = st.number_input("Bankroll $", min_value=10.0, value=500.0, step=25.0, key="sb_br")
        c1, c2, c3 = st.columns(3)
        amer = c1.number_input("American odds", value=150, step=10, key="sb_amer")
        wp = c2.slider("Your win %", 1, 99, 55, key="sb_wp") / 100.0
        stake = c3.number_input("Stake $", min_value=1.0, value=25.0, step=5.0, key="sb_stake")
        if st.button("Run single-bet simulation"):
            summary = sandbox_single_summary(amer, wp, stake, br)
            if summary.get("error"):
                st.error(summary["error"])
            else:
                st.write(f"Decimal **{summary['decimal']}** · Implied **{summary['implied_prob']}** · Edge **{summary['edge']}**")
                st.dataframe(summary.get("kelly_ladder") or [], use_container_width=True, hide_index=True)
                mc = summary.get("monte_carlo_50_bets") or {}
                st.write(f"Monte Carlo (50 bets × {mc.get('trials')} trials): median **${mc.get('median_final')}** · 5% **${mc.get('p05')}** · 95% **${mc.get('p95')}** · bust-ish rate **{mc.get('bust_rate_pct')}%**")
        st.markdown("#### Parlay lab")
        nlegs = st.slider("Legs", 2, 5, 2, key="sb_legs")
        leg_o, leg_p = [], []
        for i in range(nlegs):
            a, b = st.columns(2)
            lo = a.number_input(f"Leg {i+1} American", value=100, step=10, key=f"lo{i}")
            lp = b.slider(f"Leg {i+1} win %", 1, 99, 50, key=f"lp{i}") / 100.0
            from utils.betting_tools import american_to_decimal as atd
            d = atd(lo)
            if d:
                leg_o.append(d)
                leg_p.append(lp)
        pstake = st.number_input("Parlay stake $", min_value=1.0, value=10.0, key="sb_pstake")
        if st.button("Simulate parlay"):
            res = parlay_monte_carlo(leg_o, leg_p, pstake, br, trials=500)
            if res.get("error"):
                st.error(res["error"])
            else:
                st.write(res)
        st.markdown("#### Poisson score model")
        st.caption("Independent Poisson — λ can be mapped from recent team scoring rates.")
        try:
            form_g, _fs = client.get_recent_form(team_key)
            est = lambdas_from_form(form_g, team.get("name") or "")
            st.caption(f"Live form λ estimate: for={est.get('lambda_for')} against={est.get('lambda_against')} (n={est.get('n')}, {est.get('source')})")
            default_h = float(est.get("lambda_for") or 1.3)
            default_a = float(est.get("lambda_against") or 1.2)
        except Exception:
            default_h, default_a = 1.3, 1.2
        ph, pa, line = st.columns(3)
        lam_h = ph.number_input("λ home / for", min_value=0.1, value=float(round(default_h, 2)), step=0.1)
        lam_a = pa.number_input("λ away / against", min_value=0.1, value=float(round(default_a, 2)), step=0.1)
        tot_line = line.number_input("Total line", min_value=0.5, value=2.5, step=0.5)
        if st.button("Run Poisson"):
            mat = poisson_score_matrix(lam_h, lam_a)
            st.write({k: mat[k] for k in ("p_home", "p_draw", "p_away", "most_likely_score", "most_likely_p")})
            st.write(poisson_total_over_prob(lam_h, lam_a, tot_line))
            try:
                st.markdown("**Joint probability surface (WebGL)**")
                st.plotly_chart(poisson_surface(lam_h, lam_a), use_container_width=True)
            except Exception:
                pass
        st.markdown("#### Detailed Monte Carlo")
        st.caption("Antithetic variates + optional stratified sampling.")
        nb = st.slider("Bets per path", 10, 200, 50)
        tr = st.slider("Trials", 100, 2000, 600, 100)
        use_strat = st.checkbox("Stratified sampling", value=True)
        if st.button("Run detailed MC"):
            from utils.betting_tools import american_to_decimal as atd
            d = atd(amer)
            if d:
                detailed = monte_carlo(d, wp, stake, nb, br, trials=tr, antithetic=True, stratified=use_strat)
                st.json(detailed)
        st.markdown("#### Kalman smoother (1D)")
        st.caption("Smooth a short series (e.g. recent points scored) — teaching demo.")
        series_txt = st.text_input("Comma-separated observations", value="21,17,24,14,28,20")
        if st.button("Run Kalman"):
            try:
                series = [float(x.strip()) for x in series_txt.split(",") if x.strip()]
                st.write(kalman_1d(series))
            except Exception as ke:
                st.error(str(ke))

        st.markdown("#### Bayesian hierarchical Poisson")
        st.caption(
            "Gamma–Poisson conjugate updates + empirical-Bayes shrinkage of team rates toward the league mean. "
            "Teaching model — not full MCMC Dixon–Coles."
        )
        try:
            form_g2, _ = client.get_recent_form(team_key)
            sc_list, al_list = rates_from_form_games(form_g2, team.get("name") or "")
            if not sc_list:
                sc_list = [1, 2, 0, 2, 1]
                al_list = [1, 1, 2, 0, 2]
            cgp1, cgp2 = st.columns(2)
            with cgp1:
                st.markdown("**Attack rate (scored)**")
                st.write(gamma_poisson_update(sc_list, a_prior=2.0, b_prior=1.5))
            with cgp2:
                st.markdown("**Defense proxy (allowed)**")
                st.write(gamma_poisson_update(al_list, a_prior=2.0, b_prior=1.5))

            # Build mini league from form opponents for EB shrinkage
            rate_map = {}
            games_map = {}
            tn = (team.get("name") or "").lower()
            for g in form_g2 or []:
                try:
                    hs = float(g.get("home_score") or 0)
                    as_ = float(g.get("away_score") or 0)
                except Exception:
                    continue
                for label, pts in (
                    (g.get("home_team") or "Home", hs),
                    (g.get("away_team") or "Away", as_),
                ):
                    if not label:
                        continue
                    rate_map.setdefault(label, [])
                    rate_map[label].append(pts)
            team_rates = {k: sum(v)/len(v) for k, v in rate_map.items() if v}
            team_games = {k: len(v) for k, v in rate_map.items()}
            if team_rates:
                eb = empirical_bayes_rates(team_rates, team_games)
                st.markdown("**Empirical-Bayes shrunk rates** (observed → toward league μ)")
                st.write({"mu": eb.get("mu"), "tau2": eb.get("tau2")})
                # show top few
                items = sorted(eb.get("teams", {}).items(), key=lambda kv: -kv[1].get("games", 0))[:8]
                st.dataframe(
                    [{"team": k, **v} for k, v in items],
                    use_container_width=True,
                    hide_index=True,
                )
                # hierarchical match preview using selected team vs average
                att = eb.get("teams", {}).get(team.get("name") or "", {})
                # fallback first key
                if not att and eb.get("teams"):
                    att = list(eb["teams"].values())[0]
                mu = float(eb.get("mu") or 1.2)
                att_s = float(att.get("shrunk") or mu)
                # defense ~ inverse-ish of scoring allowed mean
                def_s = mu / max(0.3, att_s) if att_s else 1.0
                prev = hierarchical_match_preview(att_s, mu, def_s, 1.0, home_advantage=1.08)
                st.markdown("**Hierarchical match preview** (shrunk attack vs league-average opponent)")
                st.write(prev)
        except Exception as be:
            st.warning("Bayesian Poisson block unavailable.")
            if st.session_state.show_sources:
                st.caption(str(be))
    except Exception as e:
        st.warning("Sandbox unavailable.")
        if st.session_state.show_sources:
            st.caption(str(e))


with tabs[3]:
    st.markdown('<div class="section-title">Odds Detail</div>', unsafe_allow_html=True)
    try:
        if not odds_key:
            st.info("Add Odds API key for book depth.")
        else:
            ogames, osrc = client.get_odds(team_key)
            if not ogames:
                st.markdown('<div class="sbsby-card empty-state">No odds returned.</div>', unsafe_allow_html=True)
            for og in ogames:
                st.markdown(f"**{og.get('away_team')} @ {og.get('home_team')}**")
                for bm in og.get("bookmakers") or []:
                    st.caption(bm.get("book"))
            src_note(osrc)
    except Exception as e:
        st.warning("Odds error.")
        if st.session_state.show_sources:
            st.caption(str(e))

# ===== Watch =====
with tabs[4]:
    st.markdown('<div class="section-title">Watch / Listen</div>', unsafe_allow_html=True)
    try:
        media = get_media_for_team(team_key, team.get("name") or "")
        for cat, items in media.items():
            st.markdown(f"#### {cat}")
            for it in items:
                st.markdown(f"- [{it.get('name')}]({it.get('url')}) — {it.get('note','')}")
    except Exception:
        st.warning("Media directory unavailable.")

# ===== News =====
with tabs[5]:
    st.markdown('<div class="section-title">News</div>', unsafe_allow_html=True)
    st.caption(f"Headlines for **{team.get('name')}** only")
    try:
        arts, src = client.get_news(team_key, 16)
        if not arts:
            st.info("No headlines right now — try Refresh.")
        for a in arts:
            st.markdown(f"**[{a.get('headline')}]({a.get('url') or '#'})**")
            meta = " · ".join(filter(None, [a.get("source") or "", (a.get("published") or "")[:16]]))
            if meta:
                st.caption(meta)
        src_note(src)
    except Exception as e:
        st.warning("News unavailable.")
        if st.session_state.show_sources:
            st.caption(str(e))

# ===== Standings =====
with tabs[6]:
    st.markdown('<div class="section-title">Standings</div>', unsafe_allow_html=True)
    st.caption(f"League table context for **{team.get('name')}** · prior seasons if current empty")
    try:
        rows, src = client.get_standings(team_key)
        if rows:
            df = pd.DataFrame(rows)
            focus = (team.get("name") or team.get("short") or "").lower()
            if "Team" in df.columns and focus:
                token = focus.split()[-1] if focus else ""
                if token:
                    mask = df["Team"].astype(str).str.lower().str.contains(token, na=False)
                    if mask.any():
                        st.markdown("**Your team**")
                        st.dataframe(df[mask], use_container_width=True, hide_index=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            # Link rows
            for r in rows:
                s = str(r.get("STRK") or "")
                if s.startswith("http"):
                    st.markdown(f"- [{r.get('Team')}]({s})")
            src_note(src)
        else:
            st.info("Standings unavailable for this league window.")
    except Exception as e:
        st.warning("Standings error.")
        if st.session_state.show_sources:
            st.caption(str(e))

# ===== Schedule =====
with tabs[7]:
    st.markdown('<div class="section-title">Schedule</div>', unsafe_allow_html=True)
    st.caption(f"Ordered schedule for **{team.get('name')}** — date, matchup, venue, result")
    try:
        games, src = client.get_schedule(team_key)
        if not games:
            st.info("No schedule rows yet — try Refresh.")
        rows = []
        for g in games or []:
            detail = g.get("detail") or ""
            when = (g.get("date") or "")[:16].replace("T", " ")
            matchup = g.get("name") or f"{g.get('away_team','')} @ {g.get('home_team','')}"
            venue = g.get("venue") or ""
            status = g.get("status") or g.get("detail") or ""
            score = f"{g.get('away_score','–')}–{g.get('home_score','–')}"
            if str(detail).startswith("http") or (g.get("source") in ("local-program", "maxpreps", "search") and str(detail).startswith("http")):
                st.markdown(f"**[{matchup}]({detail})**" + (f" · {when}" if when else ""))
            else:
                rows.append({
                    "When": when,
                    "Matchup": matchup,
                    "Venue": venue,
                    "Status": status if not str(status).startswith("http") else "Scheduled",
                    "Score": score,
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        src_note(src)
    except Exception as e:
        st.warning("Schedule error.")
        if st.session_state.show_sources:
            st.caption(str(e))

# ===== Trends =====
with tabs[8]:
    st.markdown('<div class="section-title">Trends</div>', unsafe_allow_html=True)
    st.caption(f"Recent form for **{team.get('name')}** only · all-time markers if live form empty")
    try:
        form, src = client.get_recent_form(team_key)
        if form:
            rows = []
            for g in form:
                try:
                    hs = int(float(g.get("home_score") or 0))
                    as_ = int(float(g.get("away_score") or 0))
                except Exception:
                    hs, as_ = 0, 0
                rows.append({
                    "Matchup": g.get("name") or f"{g.get('away_team','')} @ {g.get('home_team','')}",
                    "Away": as_, "Home": hs, "Total": as_ + hs,
                    "Date": (g.get("date") or "")[:10],
                    "Status": g.get("status") or g.get("detail") or "",
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            if len(df) >= 2 and df["Total"].sum() > 0:
                fig = px.bar(df, x="Date", y="Total", color="Total", title=f"{team.get('short')} — recent combined points")
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            try:
                fig3 = form_3d_scatter(rows, title=f"{team.get('short')} — 3D form space (WebGL)")
                if fig3 is not None:
                    st.plotly_chart(fig3, use_container_width=True)
            except Exception:
                pass
            src_note(src)
        else:
            st.info("No current-season finished games found — showing all-time trend markers.")
            try:
                hist, hsrc = client.get_all_time_trends(team_key)
                if hist:
                    st.dataframe(pd.DataFrame(hist), use_container_width=True, hide_index=True)
                    src_note(hsrc)
            except Exception:
                st.caption("All-time trend table unavailable.")
    except Exception as e:
        st.warning("Trends error.")
        if st.session_state.show_sources:
            st.caption(str(e))

# ===== Leaders =====
with tabs[9]:
    st.markdown('<div class="section-title">All-Time Leaders</div>', unsafe_allow_html=True)
    try:
        leaders, lsrc = get_all_time_leaders(team_key)
        if leaders:
            cat = st.selectbox("Category", list(leaders.keys()), key="lead_cat")
            st.dataframe(pd.DataFrame(leaders.get(cat) or []), use_container_width=True, hide_index=True)
            src_note(lsrc)
        else:
            st.info("No leaders table.")
    except Exception:
        st.warning("Leaders error.")

# ===== Greats =====
with tabs[10]:
    st.markdown('<div class="section-title">Championship Greats</div>', unsafe_allow_html=True)
    try:
        greats, gsrc = get_championship_greats(team_key)
        for g in greats:
            st.markdown(f"**{g.get('player')}** · {g.get('era','')} — {g.get('titles','')} · _{g.get('why','')}_")
        gnames = [g.get("player") for g in greats if g.get("player")]
        if gnames:
            gp = st.selectbox("Open player card", ["—"] + gnames, key="great_pick")
            if gp and gp != "—":
                st.session_state.selected_player = gp
                st.info(f"Selected **{gp}** — open the Players tab for the full card.")
        src_note(gsrc)
    except Exception:
        st.warning("Greats error.")

# ===== Players =====
with tabs[11]:
    st.markdown('<div class="section-title">Player Cards</div>', unsafe_allow_html=True)
    try:
        roster, rsrc = get_roster(team_cfg)
        pool = PLAYER_POOL.get(team_key, [])
        options = sorted(set([p.get("name") for p in roster if p.get("name")] + list(pool or []))) or ["(none)"]
        player = st.selectbox("Player", options, key="player_sel")
        if player and player != "(none)":
            card, csrc = get_player_card(player, team_cfg)
            thumb = card.get("cutout") or card.get("thumb")
            if not thumb:
                try:
                    thumb = cartoon_data_uri(player, card.get("position") or "", team.get("colors", {}).get("primary", "#311D00"))
                except Exception:
                    thumb = None
            years = card.get("best_years") or "Career"
            anecdote = card.get("anecdote") or ""
            desc = (card.get("description") or "")[:280]
            img_tag = f'<img class="bb-photo" src="{thumb}" alt="p"/>' if thumb else ""
            st.markdown(f"""
            <div class="bb-card">{img_tag}
              <div class="bb-name">{card.get('name', player)}</div>
              <div class="bb-team">{card.get('team') or team.get('short')} · {card.get('position') or 'Player'}</div>
              <span class="bb-years">BEST YEARS · {years}</span>
              <div class="bb-stats">{desc}</div>
              <div class="bb-anecdote">“{anecdote}”</div>
            </div>""", unsafe_allow_html=True)
            src_note(csrc)
        src_note(rsrc)
    except Exception:
        st.warning("Player cards error.")

# ===== Community =====
with tabs[12]:
    st.markdown('<div class="section-title">Community</div>', unsafe_allow_html=True)
    st.caption("Topics bold · tags · votes · 100 posts/topic · safety filter. Backend: " + ("Supabase" if supabase_configured() else "local JSON failover"))
    user = st.session_state.username or "Fan"
    try:
        with st.expander("Create topic"):
            title = st.text_input("Title (bold topic)", key="ct_title")
            tags = st.text_input("Tags (comma-separated)", key="ct_tags")
            body = st.text_area("Opening post", key="ct_body")
            if st.button("Post topic"):
                tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
                ok, msg = create_topic(team_key, title, user, tag_list, body)
                st.success("Created " + msg) if ok else st.error(msg)
                if ok:
                    st.rerun()
        topics = list_topics(team_key)
        if not topics:
            st.info("No topics yet — start one.")
        for tpc in topics:
            st.markdown(f"### **{tpc.get('title')}**")
            st.caption(f"by {tpc.get('author')} · tags: {', '.join(tpc.get('tags') or [])}")
            for p in tpc.get("posts") or []:
                st.markdown(f"**{p.get('author')}**: {p.get('body')}")
                if p.get("link_url"):
                    st.markdown(f"[Link]({p.get('link_url')})")
                if p.get("image_url"):
                    st.markdown(f"[Image]({p.get('image_url')})")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    if st.button(f"👍 {p.get('up',0)}", key=f"up_{p.get('id')}"):
                        vote(tpc["id"], p["id"], "up"); st.rerun()
                with c2:
                    if st.button(f"👎 {p.get('down',0)}", key=f"dn_{p.get('id')}"):
                        vote(tpc["id"], p["id"], "down"); st.rerun()
                with c3:
                    if st.button("Delete mine", key=f"del_{p.get('id')}"):
                        ok, msg = delete_post(tpc["id"], p["id"], user, "")
                        st.toast(msg)
                        if ok:
                            st.rerun()
            with st.expander(f"Reply to: {tpc.get('title')[:40]}"):
                rb = st.text_area("Comment", key=f"r_{tpc['id']}")
                link = st.text_input("Safe link (https)", key=f"l_{tpc['id']}")
                img = st.text_input("Image URL (https)", key=f"i_{tpc['id']}")
                if st.button("Reply", key=f"rb_{tpc['id']}"):
                    ok, msg = add_post(tpc["id"], user, rb, img, link)
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()
            mod = st.text_input("Mod password (owner)", type="password", key=f"mod_{tpc['id']}")
            if st.button("Mod delete topic", key=f"mdt_{tpc['id']}"):
                ok, msg = delete_topic(tpc["id"], mod)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()
        st.markdown("#### Active usernames")
        for u in list_users()[:50]:
            st.caption(f"{u.get('name')} · posts {u.get('posts')}")
    except Exception as e:
        st.warning("Community unavailable.")
        if st.session_state.show_sources:
            st.caption(str(e))

# ===== Desk Bot =====
with tabs[13]:
    st.markdown('<div class="section-title">Cleveland Desk Bot</div>', unsafe_allow_html=True)
    st.caption("Friendly · Believeland slant · rule-based with failover lines.")
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []
    q = st.text_input("Ask the desk", key="bot_q")
    if st.button("Send") and q:
        ans, src = bot_reply(q, team_key, team.get("name") or "")
        st.session_state.chat_log.append(("you", q))
        st.session_state.chat_log.append(("bot", ans))
        src_note(src)
    for who, text in st.session_state.chat_log[-12:]:
        st.markdown(f"**{'You' if who=='you' else 'Desk'}:** {text}")

# ===== Moments =====
with tabs[14]:
    st.markdown('<div class="section-title">Famous / Infamous Moments</div>', unsafe_allow_html=True)
    try:
        for m in moments_for(team_key, team.get("name") or ""):
            st.markdown(f"**[{m['title']}]({m['url']})** — {m.get('note','')}")
        st.caption("Links are searches / official pages — respect platform copyright rules.")
    except Exception:
        st.warning("Moments unavailable.")

# ===== Tickets =====
with tabs[15]:
    st.markdown('<div class="section-title">Buy Tickets</div>', unsafe_allow_html=True)
    try:
        for t in ticket_links(team.get("name") or team.get("short") or ""):
            st.markdown(f"- [{t['name']}]({t['url']})")
    except Exception:
        st.warning("Ticket links unavailable.")

# ===== Rushmore =====
with tabs[16]:
    st.markdown('<div class="section-title">Fan Mount Rushmore</div>', unsafe_allow_html=True)
    pool = list(PLAYER_POOL.get(team_key, []) or ["Legend A", "Legend B", "Legend C", "Legend D"])
    while len(pool) < 4:
        pool.append(f"Legend {len(pool)}")
    defaults = st.session_state.rushmore_picks or DEFAULT_RUSHMORE.get(team_key, pool[:4])
    cols = st.columns(4)
    picks = []
    for i, col in enumerate(cols):
        with col:
            d = defaults[i] if i < len(defaults) else pool[i]
            try:
                ix = pool.index(d)
            except ValueError:
                ix = min(i, len(pool) - 1)
            picks.append(st.selectbox(f"Face {i+1}", pool, index=ix, key=f"rush_{team_key}_{i}"))
    st.session_state.rushmore_picks = picks
    if st.button("🗻 Generate Mount Rushmore", type="primary"):
        try:
            with st.spinner("Carving faces into the mountain…"):
                png = rushmore_to_bytes(picks, title=f"{team['short']} Mount Rushmore")
            st.image(png, use_container_width=True)
            st.download_button(
                "Download image",
                data=png,
                file_name=f"sosby_rushmore_{team_key}.jpg",
                mime="image/jpeg",
            )
        except Exception as e:
            st.error(f"Rushmore failed: {e}")

# ===== Markets =====

with tabs[17]:
    st.markdown('<div class="section-title">Hypothetical Bet Journal</div>', unsafe_allow_html=True)
    st.caption("Track paper bets only — nothing is submitted to a book.")
    try:
        with st.form("journal_form"):
            j1, j2, j3 = st.columns(3)
            side = j1.text_input("Side / pick", value=team.get("short") or "")
            odds = j2.number_input("American odds", value=-110, step=5)
            stake = j3.number_input("Stake $", min_value=0.0, value=25.0, step=5.0)
            note = st.text_input("Note / model (Kelly, Poisson, MC…)")
            result = st.selectbox("Result", ["Open", "Win", "Loss", "Push"])
            if st.form_submit_button("Add to journal"):
                pnl = 0.0
                from utils.betting_tools import american_to_decimal
                dec = american_to_decimal(odds) or 0
                if result == "Win" and dec:
                    pnl = stake * (dec - 1)
                elif result == "Loss":
                    pnl = -stake
                add_entry({
                    "team": team.get("name"),
                    "side": side,
                    "odds": odds,
                    "stake": stake,
                    "note": note,
                    "result": result,
                    "pnl": round(pnl, 2),
                })
                st.success("Logged")
        rows = list_entries(100)
        st.write(summary_stats(rows))
        if rows:
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.download_button(
                "Download journal CSV",
                data=to_csv(rows),
                file_name="sosby_bet_journal.csv",
                mime="text/csv",
            )
        if st.button("Clear journal"):
            clear_all()
            st.rerun()
    except Exception as e:
        st.warning("Journal unavailable.")
        if st.session_state.show_sources:
            st.caption(str(e))


with tabs[18]:
    st.markdown('<div class="section-title">Prediction Markets</div>', unsafe_allow_html=True)
    for l in client.prediction_links(team_key):
        st.markdown(f"**[{l['name']}]({l['url']})** — {l['desc']}")

# ===== Alerts / Twilio =====
with tabs[19]:
    st.markdown('<div class="section-title">Alerts & Twilio SMS</div>', unsafe_allow_html=True)
    st.markdown(SETUP_HELP)
    st.write("Twilio configured:" , "✅" if twilio_configured() else "❌ (add secrets)")
    phone = st.text_input("E.164 phone", placeholder="+15551234567")
    msg = st.text_input("Message", value=f"SBSBY update: check {team.get('name')} scores!")
    if st.button("Send SMS now"):
        ok, m = send_sms(phone, msg)
        st.success(m) if ok else st.error(m)
    st.caption("SMS only sends while you trigger it with valid Twilio secrets. No offline background push on Community Cloud.")
    st.markdown("#### Live feed / WebSocket diagnostics")
    try:
        for c in sports_ws_candidates(team_key):
            st.caption(f"{c.get('name')} · {c.get('transport')} — {c.get('note')}")
        if st.button("Probe public echo WebSocket"):
            st.json(probe_websocket())
        sock = get_owner_ws()
        st.caption("Owner SPORTS_WS_URL: " + ("active" if sock else "not set"))
    except Exception as e:
        st.caption(str(e))

st.divider()
st.markdown("""
<div style="text-align:center;opacity:.7;font-size:.8rem">
<strong>SO!SB!Y!</strong> · Superb Owl! Super Browns! Yeah!<br>
SO!SB!Y! · Superb Owl · Read-only shell · Community posts · Owner via GitHub · Not affiliated with leagues/schools
</div>""", unsafe_allow_html=True)
