"""Educational Betting Lab — sandbox only, multi-team aware."""
from __future__ import annotations
import streamlit as st
import pandas as pd

from utils.nav_state import remember_page
from utils.app_shell import page_setup, src_note
from utils.api_client import TEAMS
from utils.cached_feeds import cached_betting_dashboard
from utils.betting_tools import (
    detect_arbitrage, bankroll_plan, full_kelly_table,
    STAT_ARB_MODELS, LIVE_ARB_STRATEGIES, price_dispersion, implied_edge_table,
    american_to_decimal,
)
from utils.betting_sandbox import sandbox_single_summary, parlay_monte_carlo
from utils.bet_journal import add_entry, list_entries, clear_all, summary_stats, to_csv
from utils.error_handler import ui_error

remember_page("betting")
team_key, team, client, flavor = page_setup("Betting Lab · SO!SB!Y!")

st.warning(
    "**Educational sandbox only.** These tools teach odds math, bankroll sizing, "
    "and risk. Nothing here places a real bet. No bookmaker affiliation."
)

# Multi-team focus
focus_labels = {v["short"]: k for k, v in TEAMS.items()}
focus_name = st.selectbox(
    "Study odds for team",
    list(focus_labels.keys()),
    index=list(focus_labels.values()).index(team_key) if team_key in focus_labels.values() else 0,
)
focus_key = focus_labels[focus_name]
st.caption(f"Lab focus: **{TEAMS[focus_key]['name']}** ({TEAMS[focus_key].get('league','')}). Switch sidebar team anytime.")

tabs = st.tabs(["Why this lab?", "Live lines", "Kelly classroom", "Sandbox sim", "Journal", "Markets"])

with tabs[0]:
    st.markdown("""
### Why a betting *lab*?
Sports odds are just **prices** on outcomes. Learning to read them helps you:
1. Convert **American ↔ decimal** odds and see implied probability  
2. Compare **your** probability estimate vs the market  
3. Size paper stakes with **Kelly** so you do not blow a pretend bankroll  
4. Spot **arbitrage** structure (rare, often gone before you can click)

**Safe rule:** only practice with hypothetical stakes in this sandbox.

### Core formulas
- Positive American `+150` → decimal `1 + 150/100 = 2.50`  
- Negative American `-200` → decimal `1 + 100/200 = 1.50`  
- Implied probability ≈ `1 / decimal`  
- Kelly fraction: `f* = (b·p − q) / b` with `b = decimal−1`, `q = 1−p`  

We show **full / half / quarter** Kelly and cap risk so the lesson is about *discipline*, not max aggression.
    """)
    for s in STAT_ARB_MODELS[:4]:
        st.markdown(f"**{s['title']}** — {s['body']}")

with tabs[1]:
    try:
        dash, dsrc = cached_betting_dashboard(focus_key)
        st.metric("Odds API", "connected" if dash.get("has_api_key") else "add key in Settings")
        if not dash.get("has_api_key"):
            st.info("Add The Odds API key under sidebar → Settings for book depth. ESPN lines may still appear.")
        if dash.get("espn_lines"):
            st.markdown("#### ESPN-style lines (selected team context)")
            for ln in dash["espn_lines"]:
                o = ln.get("odds") or {}
                st.markdown(f"**{ln.get('matchup') or ''}** · spread {o.get('spread')} · O/U {o.get('over_under')}")
        if dash.get("games"):
            st.markdown("#### Bookmakers (snapshot)")
            for og in dash["games"][:6]:
                st.markdown(f"**{og.get('away_team')} @ {og.get('home_team')}**")
                for bm in (og.get("bookmakers") or [])[:2]:
                    st.caption(bm.get("book"))
            try:
                opps = detect_arbitrage(dash["games"])
                if opps:
                    st.markdown("#### Arb scan (educational)")
                    st.dataframe(pd.DataFrame(opps), use_container_width=True, hide_index=True)
                else:
                    st.success("No ≥0.3% 2-way ML arb in this snapshot (common).")
            except Exception:
                pass
        src_note(dsrc)
    except Exception as e:
        ui_error("Lines", e)

with tabs[2]:
    st.markdown("Enter **any** price and a win probability to see recommended paper stake sizes.")
    try:
        b1, b2, b3 = st.columns(3)
        br = b1.number_input("Paper bankroll $", 10.0, value=500.0, step=25.0)
        up = b2.number_input("Unit % of bankroll", 0.25, 5.0, 1.0, 0.25)
        prof = b3.selectbox("Risk profile", ["conservative", "moderate", "aggressive"], 1)
        plan = bankroll_plan(br, up, prof)
        st.write(f"Unit **${plan['unit_size']}** · Max single **${plan['max_single_bet']}** · Max daily **${plan['max_daily_risk']}**")
        dec = st.number_input("Decimal odds", 1.01, value=2.0, step=0.05)
        wp = st.slider("Your estimated win probability", 0.05, 0.95, 0.55, 0.01)
        table = full_kelly_table(dec, wp, plan["bankroll"])
        for label in ("Full Kelly", "Half Kelly", "Quarter Kelly"):
            row = table.get(label, {})
            st.metric(label, f"${row.get('stake', 0):.2f}")
        st.caption("Quarter Kelly is often used in teaching to reduce variance while you learn.")
    except Exception as e:
        ui_error("Kelly", e)

    st.markdown("#### Expected value (EV) helper")
    st.caption("EV = (p × profit_if_win) − ((1−p) × stake). Positive EV is a teaching signal, not a guarantee.")
    try:
        ev_stake = st.number_input("Stake $", 1.0, value=100.0, step=5.0, key="ev_stake")
        ev_amer = st.number_input("American odds", value=-110, step=5, key="ev_amer")
        ev_p = st.slider("Your win p", 0.01, 0.99, 0.52, 0.01, key="ev_p")
        dec = american_to_decimal(ev_amer) or 0
        profit = ev_stake * (dec - 1) if dec else 0
        ev = ev_p * profit - (1 - ev_p) * ev_stake
        st.metric("Estimated EV $", f"{ev:.2f}")
        st.caption(f"Decimal {dec:.3f} · Implied {(1/dec if dec else 0):.1%}")
    except Exception as e:
        ui_error("EV helper", e)

    st.markdown("#### Break-even win rate")
    try:
        be_amer = st.number_input("Odds for break-even", value=-110, step=5, key="be_amer")
        be_dec = american_to_decimal(be_amer) or 0
        if be_dec:
            st.write(f"You need about **{(1/be_dec)*100:.1f}%** win rate to break even at these odds (before juice nuance).")
    except Exception:
        pass

    st.markdown("#### Hedge sketch (two-way)")
    st.caption("Illustrates how a hedge stake offsets risk — educational only.")
    try:
        h1 = st.number_input("Original stake", 1.0, value=50.0, key="h1")
        h1o = st.number_input("Original American", value=150, key="h1o")
        h2o = st.number_input("Hedge American", value=-160, key="h2o")
        d1, d2 = american_to_decimal(h1o) or 0, american_to_decimal(h2o) or 0
        if d1 and d2:
            # stake2 so profit roughly balances
            win1 = h1 * (d1 - 1)
            h2 = win1 / (d2 - 1) if d2 > 1 else 0
            st.write(f"Approx hedge stake **${h2:.2f}** so outcomes are closer to flat (ignores limits/fees).")
    except Exception:
        pass

with tabs[3]:
    st.markdown("### Single-bet Monte Carlo (paper)")
    try:
        amer = st.number_input("American odds", value=150, step=10)
        wp = st.slider("Win %", 1, 99, 55) / 100.0
        stake = st.number_input("Stake $", 1.0, value=25.0, step=5.0)
        br = st.number_input("Bankroll $", 10.0, value=500.0, step=25.0, key="sim_br")
        if st.button("Run simulation"):
            summary = sandbox_single_summary(amer, wp, stake, br)
            if summary.get("error"):
                st.error(summary["error"])
            else:
                st.write(
                    f"Decimal **{summary['decimal']}** · Implied **{summary['implied_prob']}** · "
                    f"Edge **{summary['edge']}**"
                )
                st.dataframe(summary.get("kelly_ladder") or [], use_container_width=True, hide_index=True)
                mc = summary.get("monte_carlo_50_bets") or {}
                st.write(
                    f"After 50 paper bets × many trials: median **${mc.get('median_final')}** · "
                    f"5% **${mc.get('p05')}** · 95% **${mc.get('p95')}**"
                )
        st.markdown("### Parlay lab")
        nlegs = st.slider("Legs", 2, 5, 2)
        leg_o, leg_p = [], []
        for i in range(nlegs):
            a, b = st.columns(2)
            leg_o.append(a.number_input(f"Leg {i+1} American", value=100, step=10, key=f"plo{i}"))
            leg_p.append(b.slider(f"Leg {i+1} win %", 1, 99, 50, key=f"plp{i}") / 100.0)
        if st.button("Simulate parlay"):
            st.json(parlay_monte_carlo(leg_o, leg_p, stake=25.0, bankroll=br, trials=2000))
    except Exception as e:
        ui_error("Sandbox", e)

with tabs[4]:
    st.caption("Paper journal — nothing is sent to a book.")
    try:
        with st.form("jform"):
            side = st.text_input("Pick", value=TEAMS[focus_key].get("short") or "")
            odds = st.number_input("American odds", value=-110, step=5)
            stake = st.number_input("Stake $", 0.0, value=25.0, step=5.0)
            note = st.text_input("Note")
            result = st.selectbox("Result", ["Open", "Win", "Loss", "Push"])
            if st.form_submit_button("Log"):
                pnl = 0.0
                dec = american_to_decimal(odds) or 0
                if result == "Win" and dec:
                    pnl = stake * (dec - 1)
                elif result == "Loss":
                    pnl = -stake
                add_entry({
                    "team": TEAMS[focus_key].get("name"),
                    "side": side, "odds": odds, "stake": stake,
                    "note": note, "result": result, "pnl": round(pnl, 2),
                })
                st.success("Logged")
        rows = list_entries(100)
        st.write(summary_stats(rows))
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.download_button("CSV", data=to_csv(rows), file_name="sosby_journal.csv", mime="text/csv")
        if st.button("Clear journal"):
            clear_all()
            st.rerun()
    except Exception as e:
        ui_error("Journal", e)


with st.expander("More lab tools"):
    st.markdown("#### Unit ladder")
    st.caption("Maps confidence to paper units (1–5). Teaching aid only.")
    conf = st.slider("Confidence", 1, 5, 3, key="unit_conf")
    unit = st.number_input("Unit size $", 1.0, value=10.0, key="unit_sz")
    st.write(f"Suggested paper stake: **${conf * unit:.2f}** ({conf} units)")
    st.markdown("#### Closing line value (CLV) sketch")
    st.caption("CLV ≈ your price vs close. Positive CLV is a process metric, not profit.")
    yours = st.number_input("Your decimal price", 1.01, value=2.1, step=0.01, key="clv_y")
    close = st.number_input("Closing decimal", 1.01, value=2.0, step=0.01, key="clv_c")
    if yours > 1 and close > 1:
        st.write(f"Rough CLV signal: **{(yours/close - 1)*100:.2f}%** price improvement vs close")
    st.markdown("#### Parlay vig awareness")
    st.write("Each leg multiplies book edge. More legs → more total juice. Prefer learning on singles first.")

with tabs[5]:
    for l in client.prediction_links(focus_key):
        st.markdown(f"**[{l['name']}]({l['url']})** — {l['desc']}")
    for s in LIVE_ARB_STRATEGIES[:3]:
        st.markdown(f"**{s['title']}** — {s['body']}")
