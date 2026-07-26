"""
Dynamic team-themed CSS — light tones for readability + dark mode.
Premium glass cards, live pulse, odds chips.
"""

from __future__ import annotations

from .api_client import TEAMS


def build_css(team_key: str, dark: bool = False) -> str:
    c = TEAMS.get(team_key, TEAMS["browns"])["colors"]
    if dark:
        bg = c["dark_bg"]
        card = c["dark_card"]
        text = "#F5F0EB"
        muted = "#B8A99A"
        border = "rgba(255,255,255,0.08)"
        shadow = "0 8px 32px rgba(0,0,0,0.45)"
        header_grad = f"linear-gradient(135deg, {c['primary']} 0%, {c['secondary']} 100%)"
    else:
        bg = c["light_bg"]
        card = c["light_card"]
        text = "#1A1410"
        muted = "#5C5346"
        border = "rgba(0,0,0,0.06)"
        shadow = "0 8px 28px rgba(0,0,0,0.08)"
        header_grad = f"linear-gradient(135deg, {c['primary']}ee 0%, {c['secondary']}dd 100%)"

    primary = c["primary"]
    secondary = c["secondary"]
    accent = c.get("accent", "#FFFFFF")

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {bg} !important;
        color: {text} !important;
        font-family: 'Outfit', system-ui, -apple-system, sans-serif !important;
    }}
    .stApp {{ background: {bg} !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    .sbsby-banner {{
        background: {header_grad};
        color: {accent};
        padding: 1.15rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.25rem;
        box-shadow: {shadow};
        position: relative;
        overflow: hidden;
    }}
    .sbsby-banner::before {{
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 20% 50%, rgba(255,255,255,0.14) 0%, transparent 55%);
        pointer-events: none;
    }}
    .sbsby-banner h1 {{
        margin: 0;
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}
    .sbsby-banner .subtitle {{
        margin: 0.35rem 0 0;
        font-size: 0.95rem;
        font-weight: 500;
        opacity: 0.92;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }}
    .live-dot {{
        display: inline-block;
        width: 9px; height: 9px;
        background: #ef4444;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse-dot 1.2s ease-in-out infinite;
        vertical-align: middle;
    }}
    @keyframes pulse-dot {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.45; transform: scale(0.85); }}
    }}

    .sbsby-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: {shadow};
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    .sbsby-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 36px rgba(0,0,0,0.12);
    }}
    .score-card {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
    }}
    .team-block {{
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 110px;
        flex: 1;
    }}
    .team-block .name {{
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 0.35rem;
        text-align: center;
    }}
    .team-block .score {{
        font-size: 2rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: {primary};
        line-height: 1.1;
    }}
    .vs-pill {{
        background: {primary}22;
        color: {primary};
        border: 1px solid {primary}44;
        border-radius: 999px;
        padding: 0.35rem 0.85rem;
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 0.06em;
    }}
    .status-badge {{
        display: inline-block;
        background: {secondary}33;
        color: {secondary};
        border-radius: 8px;
        padding: 0.2rem 0.55rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.4rem;
    }}
    .status-badge.live {{
        background: #e11d4833;
        color: #e11d48;
        animation: pulse 1.6s ease-in-out infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.65; }}
    }}

    .section-title {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {primary};
        margin: 1.4rem 0 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .section-title::before {{
        content: '';
        width: 4px;
        height: 1.1em;
        background: {secondary};
        border-radius: 2px;
    }}

    .news-item a {{
        color: {text};
        text-decoration: none;
        font-weight: 600;
        font-size: 0.95rem;
        line-height: 1.35;
    }}
    .news-item a:hover {{ color: {primary}; }}
    .news-meta {{
        font-size: 0.78rem;
        color: {muted};
        margin-top: 0.25rem;
    }}

    .metric-row {{ display: flex; flex-wrap: wrap; gap: 0.65rem; margin: 0.5rem 0 1rem; }}
    .metric-pill {{
        background: {primary}12;
        border: 1px solid {primary}28;
        border-radius: 12px;
        padding: 0.55rem 0.9rem;
        min-width: 100px;
    }}
    .metric-pill .label {{
        font-size: 0.72rem;
        color: {muted};
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .metric-pill .value {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {primary};
        font-family: 'JetBrains Mono', monospace;
    }}

    .pred-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.75rem;
    }}
    .pred-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 0.9rem 1rem;
        text-decoration: none !important;
        color: {text} !important;
        transition: border-color 0.15s, transform 0.15s;
    }}
    .pred-card:hover {{ border-color: {secondary}; transform: translateY(-2px); }}
    .pred-card strong {{ color: {primary}; display: block; margin-bottom: 0.25rem; }}
    .pred-card span {{ font-size: 0.8rem; color: {muted}; }}

    .odds-chip {{
        display: inline-block;
        background: {primary}14;
        border: 1px solid {primary}30;
        border-radius: 8px;
        padding: 0.25rem 0.55rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.15rem 0.25rem 0.15rem 0;
        color: {primary};
    }}
    .odds-book {{
        font-size: 0.78rem;
        color: {muted};
        margin-top: 0.35rem;
    }}

    [data-testid="stSidebar"] {{
        background: {card} !important;
        border-right: 1px solid {border};
    }}
    [data-testid="stSidebar"] * {{ color: {text} !important; }}

    .stButton > button {{
        background: {primary} !important;
        color: {accent} !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.1rem !important;
        transition: filter 0.15s, transform 0.15s !important;
    }}
    .stButton > button:hover {{ filter: brightness(1.08); transform: translateY(-1px); }}

    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {border};
    }}
    .source-badge {{
        font-size: 0.7rem;
        color: {muted};
        font-family: 'JetBrains Mono', monospace;
        margin-top: 0.35rem;
    }}
    .empty-state {{
        text-align: center;
        padding: 1.5rem;
        color: {muted};
        font-size: 0.95rem;
    }}

    .bb-card {
        width: 100%;
        max-width: 320px;
        margin: 0.5rem auto 1rem;
        background: linear-gradient(160deg, #f7f0e0 0%, #ebe2cc 55%, #e0d5b8 100%);
        border: 8px solid {primary};
        outline: 3px solid {secondary};
        outline-offset: 2px;
        border-radius: 6px;
        box-shadow: 4px 6px 0 rgba(0,0,0,0.25), 0 12px 28px rgba(0,0,0,0.12);
        padding: 0.65rem 0.75rem 0.85rem;
        color: #1a1410;
        font-family: 'Outfit', Georgia, serif;
        position: relative;
    }
    .bb-card::before {
        content: 'SBSBY CLASSIC';
        position: absolute; top: 6px; right: 10px;
        font-size: 0.55rem; letter-spacing: 0.12em; color: {primary}; font-weight: 700;
    }
    .bb-card .bb-photo {
        width: 100%; aspect-ratio: 4/5; object-fit: cover; object-position: top;
        border: 3px solid #3a3020; background: #cfc4a8; display: block;
    }
    .bb-card .bb-name {
        text-align: center; font-size: 1.15rem; font-weight: 800;
        margin: 0.45rem 0 0.15rem; color: {primary}; text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .bb-card .bb-team {
        text-align: center; font-size: 0.75rem; font-weight: 600; color: #4a4030;
        margin-bottom: 0.35rem;
    }
    .bb-card .bb-stats {
        background: rgba(0,0,0,0.06); border-radius: 4px; padding: 0.4rem 0.5rem;
        font-size: 0.72rem; line-height: 1.45; margin-top: 0.35rem;
    }
    .bb-card .bb-anecdote {
        font-size: 0.7rem; font-style: italic; color: #3a3228; margin-top: 0.4rem;
        border-top: 1px dashed #9a8c70; padding-top: 0.35rem; line-height: 1.4;
    }
    .bb-card .bb-years {
        display: inline-block; background: {secondary}; color: #fff;
        font-size: 0.65rem; font-weight: 700; padding: 0.12rem 0.4rem; border-radius: 3px;
    }

    @media (max-width: 640px) {{
        .sbsby-banner h1 {{ font-size: 1.35rem; }}
        .team-block .score {{ font-size: 1.55rem; }}
    }}
    </style>
    """


def inject_css(team_key: str, dark: bool) -> None:
    import streamlit as st
    st.markdown(build_css(team_key, dark), unsafe_allow_html=True)
    try:
        from .branding import watermark_data_uri
        uri = watermark_data_uri()
        st.markdown(
            f"""<style>
            .stApp::before {{
                content: '';
                position: fixed;
                inset: 0;
                background: url('{uri}') center center / min(55vw, 420px) no-repeat;
                opacity: 0.07;
                pointer-events: none;
                z-index: 0;
            }}
            [data-testid="stAppViewContainer"] > .main {{ position: relative; z-index: 1; }}
            </style>""",
            unsafe_allow_html=True,
        )
    except Exception:
        pass
