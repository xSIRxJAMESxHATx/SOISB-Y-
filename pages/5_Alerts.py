"""Alerts — Twilio SMS + feed diagnostics."""
from __future__ import annotations
import streamlit as st

from utils.nav_state import remember_page
from utils.app_shell import page_setup
from utils.twilio_sms import twilio_configured, send_sms, SETUP_HELP
from utils.ws_feeds import probe_websocket, sports_ws_candidates, get_owner_ws
from utils.error_handler import recent_logs

remember_page("alerts")
team_key, team, client, flavor = page_setup("Alerts · SO!SB!Y!")

st.markdown(SETUP_HELP)
st.write("Twilio:", "ready" if twilio_configured() else "add secrets")
phone = st.text_input("E.164 phone", placeholder="+15551234567")
msg = st.text_input("Message", value=f"SO!SB!Y! check {team.get('name')} scores")
if st.button("Send SMS"):
    ok, m = send_sms(phone, msg)
    st.success(m) if ok else st.error(m)
st.caption("SMS only when you press send with valid secrets. No background push on Community Cloud.")

st.markdown("#### Feed diagnostics")
for c in sports_ws_candidates(team_key):
    st.caption(f"{c.get('name')} · {c.get('transport')} — {c.get('note')}")
if st.button("Probe echo WebSocket"):
    st.json(probe_websocket())
st.caption("Owner WS: " + ("active" if get_owner_ws() else "not set"))

if st.session_state.get("show_sources"):
    st.markdown("#### Recent error log")
    st.json(recent_logs(8))
