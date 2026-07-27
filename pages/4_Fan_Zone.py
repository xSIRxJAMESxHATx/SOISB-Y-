"""Fan Zone — community, rushmore, moments, tickets, desk bot."""
from __future__ import annotations
import streamlit as st

from utils.nav_state import remember_page
from utils.app_shell import page_setup, src_note, header_bar
from utils.community import (
    list_topics, create_topic, add_post, vote, delete_post, delete_topic,
    list_users, supabase_configured,
)
from utils.curated_data import DEFAULT_RUSHMORE, PLAYER_POOL
from utils.rushmore import rushmore_to_bytes
from utils.moments_tickets import moments_for, ticket_links
from utils.chatbot import reply as bot_reply
from utils.error_handler import ui_error

remember_page("fan")
team_key, team, client, flavor = page_setup("Fan Zone · SO!SB!Y!")
header_bar(team, flavor)
tabs = st.tabs(["Community", "Rushmore", "Moments", "Tickets", "Desk Bot"])

with tabs[0]:
    st.caption("Backend: " + ("Supabase" if supabase_configured() else "local JSON"))
    user = st.session_state.username or "Fan"
    try:
        with st.expander("Create topic"):
            title = st.text_input("Title", key="ct")
            tags = st.text_input("Tags", key="tg")
            body = st.text_area("Opening post", key="bd")
            if st.button("Post topic"):
                tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
                ok, msg = create_topic(team_key, title, user, tag_list, body)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()
        for tpc in list_topics(team_key):
            st.markdown(f"### **{tpc.get('title')}**")
            st.caption(f"by {tpc.get('author')}")
            for p in tpc.get("posts") or []:
                st.markdown(f"**{p.get('author')}**: {p.get('body')}")
                c1, c2 = st.columns(2)
                if c1.button(f"Up {p.get('up',0)}", key=f"u{p.get('id')}"):
                    vote(tpc["id"], p["id"], "up"); st.rerun()
                if c2.button(f"Down {p.get('down',0)}", key=f"d{p.get('id')}"):
                    vote(tpc["id"], p["id"], "down"); st.rerun()
            with st.expander(f"Reply · {tpc.get('title','')[:30]}"):
                rb = st.text_area("Comment", key=f"r{tpc['id']}")
                if st.button("Reply", key=f"rb{tpc['id']}"):
                    ok, msg = add_post(tpc["id"], user, rb, "", "")
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()
    except Exception as e:
        ui_error("Community", e)

with tabs[1]:
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
            picks.append(st.selectbox(f"Face {i+1}", pool, index=ix, key=f"rush{i}"))
    st.session_state.rushmore_picks = picks
    if st.button("Generate Mount Rushmore", type="primary"):
        try:
            png = rushmore_to_bytes(picks, title=f"{team['short']} Mount Rushmore")
            st.image(png, use_container_width=True)
            st.download_button("Download", data=png, file_name=f"rushmore_{team_key}.jpg", mime="image/jpeg")
        except Exception as e:
            ui_error("Rushmore", e)

with tabs[2]:
    try:
        for m in moments_for(team_key, team.get("name") or ""):
            st.markdown(f"**[{m['title']}]({m['url']})** — {m.get('note','')}")
    except Exception as e:
        ui_error("Moments", e)

with tabs[3]:
    try:
        for t in ticket_links(team.get("name") or team.get("short") or ""):
            st.markdown(f"- [{t['name']}]({t['url']})")
    except Exception as e:
        ui_error("Tickets", e)

with tabs[4]:
    st.caption("Friendly Cleveland slant · rule-based")
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []
    q = st.text_input("Ask the desk")
    if st.button("Send") and q:
        ans, src = bot_reply(q, team_key, team.get("name") or "")
        st.session_state.chat_log.append(("you", q))
        st.session_state.chat_log.append(("bot", ans))
        src_note(src)
    for who, text in st.session_state.chat_log[-12:]:
        st.markdown(f"**{'You' if who == 'you' else 'Desk'}:** {text}")
