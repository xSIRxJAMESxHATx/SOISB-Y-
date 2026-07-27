"""Premium Owl-first theme with Tailwind-inspired utility CSS for Streamlit."""
from __future__ import annotations

from utils.api_client import TEAMS


def build_css(team_key: str, dark: bool = False) -> str:
    team_c = (TEAMS.get(team_key) or TEAMS.get("browns") or {}).get("colors") or {}
    team_primary = team_c.get("primary") or "#FF5A00"
    # Superb Owl core
    o_orange, o_brown, o_cream, o_gold = "#FF5A00", "#4A2A12", "#FFF8EF", "#E7B100"
    if dark:
        bg, card, text, muted = "#120e0a", "#1c1610", "#F5E6C8", "#a89080"
        border = "rgba(255,180,80,0.12)"
        shadow = "0 12px 40px rgba(0,0,0,0.45)"
        header_grad = f"linear-gradient(125deg, {o_brown} 0%, #6B3E18 28%, {o_orange} 58%, {o_gold} 88%, #FFE08A 100%)"
        primary, secondary = o_orange, o_gold
    else:
        bg, card, text, muted = o_cream, "#ffffff", o_brown, "#6b5344"
        border = "rgba(74,42,18,0.08)"
        shadow = "0 12px 40px rgba(74,42,18,0.08)"
        header_grad = f"linear-gradient(125deg, {o_brown} 0%, #6B3E18 25%, {o_orange} 55%, {o_gold} 85%, #FFE08A 100%)"
        primary, secondary = o_orange, o_gold
    team_accent = team_primary

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    :root {{
      --sosby-bg: {bg};
      --sosby-card: {card};
      --sosby-text: {text};
      --sosby-muted: {muted};
      --sosby-primary: {primary};
      --sosby-secondary: {secondary};
      --sosby-team: {team_accent};
      --sosby-radius: 16px;
      --sosby-shadow: {shadow};
    }}

    html, body, .stApp {{
      background:
        radial-gradient(1200px 600px at 10% -10%, rgba(255,90,0,0.08), transparent 55%),
        radial-gradient(900px 500px at 100% 0%, rgba(231,177,0,0.07), transparent 50%),
        var(--sosby-bg) !important;
      color: var(--sosby-text) !important;
      font-family: 'Outfit', system-ui, sans-serif !important;
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
      padding-top: 1.25rem !important;
      max-width: 1200px !important;
    }}

    /* Premium banner */
    .sbsby-banner {{
      background: {header_grad};
      color: #fff !important;
      border-radius: 20px;
      padding: 1.15rem 1.4rem;
      box-shadow: var(--sosby-shadow), inset 0 1px 0 rgba(255,255,255,0.2);
      border: 1px solid rgba(255,255,255,0.15);
      position: relative;
      overflow: hidden;
    }}
    .sbsby-banner::after {{
      content: '';
      position: absolute; right: -40px; top: -40px;
      width: 160px; height: 160px; border-radius: 50%;
      background: rgba(255,255,255,0.08);
    }}
    .sbsby-banner h1 {{
      margin: 0;
      font-size: clamp(1.15rem, 2.5vw, 1.65rem);
      font-weight: 800;
      letter-spacing: 0.02em;
      text-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}
    .sbsby-banner .subtitle {{
      margin: 0.35rem 0 0;
      opacity: 0.92;
      font-weight: 500;
      font-size: 0.95rem;
    }}

    /* Cards */
    .sbsby-card, .score-card, .bb-card, .metric-pill {{
      background: var(--sosby-card) !important;
      border-radius: var(--sosby-radius) !important;
      box-shadow: var(--sosby-shadow) !important;
      border: 1px solid {border} !important;
      border-left: 4px solid var(--sosby-primary) !important;
    }}
    .sbsby-card {{ padding: 1rem 1.15rem; margin: 0.5rem 0; }}
    .empty-state {{ opacity: 0.85; text-align: center; padding: 1.5rem; }}

    .metric-pill {{
      padding: 0.85rem 1rem;
      text-align: center;
    }}
    .metric-pill .label {{
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--sosby-muted);
      font-weight: 600;
    }}
    .metric-pill .value {{
      font-size: 1.15rem;
      font-weight: 800;
      margin-top: 0.2rem;
      font-family: 'JetBrains Mono', monospace;
    }}

    /* Score cards */
    .score-card {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      gap: 0.75rem;
      align-items: center;
      padding: 1rem 1.2rem;
      margin: 0.65rem 0;
    }}
    .score-card .team-name {{ font-weight: 700; font-size: 0.95rem; }}
    .score-card .score-num {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 1.45rem;
      letter-spacing: -0.02em;
      color: var(--sosby-text);
    }}
    .status-badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 700;
      background: rgba(255,90,0,0.12);
      color: var(--sosby-primary);
    }}
    .status-badge.live {{
      background: #dc2626;
      color: #fff;
      animation: pulse 1.4s ease-in-out infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.7; }}
    }}
    .live-dot {{
      display: inline-block; width: 8px; height: 8px;
      background: #ef4444; border-radius: 50%;
      margin-right: 6px;
      box-shadow: 0 0 0 0 rgba(239,68,68,0.5);
      animation: ping 1.2s infinite;
    }}
    @keyframes ping {{
      0% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.45); }}
      70% {{ box-shadow: 0 0 0 8px rgba(239,68,68,0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0); }}
    }}

    /* Vintage player card */
    .bb-card {{
      max-width: 320px;
      margin: 0.75rem auto;
      padding: 0.75rem;
      background: linear-gradient(160deg, #f7f0e0 0%, #ebe2cc 55%, #e0d4b8 100%) !important;
      border: 3px solid var(--sosby-team) !important;
      text-align: center;
    }}
    .bb-photo {{ width: 100%; border-radius: 8px; margin-bottom: 0.5rem; }}
    .bb-name {{ font-weight: 800; font-size: 1.05rem; }}
    .bb-team {{ font-size: 0.8rem; color: #5c5346; }}
    .bb-years {{
      display: inline-block; margin: 0.4rem 0;
      font-size: 0.7rem; font-weight: 700;
      padding: 0.15rem 0.5rem; border-radius: 6px;
      background: rgba(255,90,0,0.15);
    }}
    .bb-stats, .bb-anecdote {{ font-size: 0.8rem; margin-top: 0.35rem; }}

    .odds-chip {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      margin: 0.15rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
      background: rgba(255,90,0,0.1);
      border: 1px solid rgba(255,90,0,0.25);
    }}
    .section-title {{
      font-size: 1.15rem;
      font-weight: 800;
      margin: 0.75rem 0 0.5rem;
      letter-spacing: 0.01em;
    }}

    /* Streamlit chrome polish */
    .stButton > button {{
      min-height: 44px !important;
      border-radius: 12px !important;
      font-weight: 600 !important;
      border: 1px solid {border} !important;
      transition: transform 0.12s ease, box-shadow 0.12s ease;
    }}
    .stButton > button:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(74,42,18,0.12);
    }}
    .stButton > button[kind="primary"] {{
      background: linear-gradient(135deg, {primary} 0%, #FF8C29 48%, {secondary} 100%) !important;
      color: #fff !important;
      border: none !important;
    }}
    div[data-testid="stMetric"] {{
      background: var(--sosby-card);
      border-radius: 14px;
      padding: 0.65rem 0.85rem;
      border: 1px solid {border};
      box-shadow: var(--sosby-shadow);
    }}
    .stTabs [data-baseweb="tab-list"] {{
      gap: 0.35rem;
      background: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
      border-radius: 999px !important;
      padding: 0.45rem 0.9rem !important;
      font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
      background: rgba(255,90,0,0.12) !important;
    }}
    [data-testid="stSidebar"] {{
      background: linear-gradient(180deg, #FFF8EF 0%, #F5E6C8 100%) !important;
      border-right: 1px solid {border};
    }}
    [data-testid="stSidebar"] .stMarkdown {{ color: {o_brown}; }}

    /* Mobile */
    @media (max-width: 768px) {{
      .sbsby-banner h1 {{ font-size: 1.05rem !important; }}
      .score-card {{
        grid-template-columns: 1fr auto 1fr !important;
        padding: 0.85rem !important;
      }}
      .score-card .score-num {{ font-size: 1.2rem !important; }}
      .block-container {{ padding-left: 0.75rem !important; padding-right: 0.75rem !important; }}
    }}
    </style>
    """


def inject_css(team_key: str, dark: bool) -> None:
    import streamlit as st
    st.markdown(build_css(team_key, dark), unsafe_allow_html=True)
    try:
        from .branding import watermark_data_uri
        uri = watermark_data_uri()
        if uri:
            st.markdown(
                f'<div style="position:fixed;bottom:12px;right:12px;opacity:0.07;'
                f'pointer-events:none;z-index:0"><img src="{uri}" width="120"/></div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass
