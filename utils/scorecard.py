"""Beautiful, overflow-safe score cards + clean score formatting."""
from __future__ import annotations
from html import escape
from typing import Any, Optional


def format_score(val: Any) -> str:
    if val is None or val == "" or val == "–":
        return "–"
    try:
        f = float(str(val).strip().replace(",", ""))
        if f == int(f):
            return str(int(f))
        return f"{f:.1f}".rstrip("0").rstrip(".")
    except Exception:
        s = str(val).strip()
        return s[:8] if s else "–"


def short_status(text: Any, limit: int = 28) -> str:
    s = " ".join(str(text or "").split())
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "…"


def render_score_card(game: dict) -> str:
    """Return self-contained HTML for one game card."""
    st_state = (game.get("status_state") or "").lower()
    live = st_state == "in"
    is_final = st_state in ("post", "final") or "final" in str(game.get("status") or "").lower()
    label = "LIVE" if live else ("FINAL" if is_final else "UPCOMING")
    badge_cls = "status-badge live" if live else "status-badge"
    status = short_status(game.get("detail") or game.get("status") or label, 32)
    when = (game.get("date") or "")[:16].replace("T", " ")
    venue = short_status(game.get("venue") or "", 40)
    bcast = short_status(game.get("broadcast") or "", 24)
    meta = " · ".join(x for x in [label, when, venue, bcast] if x)

    away_s = format_score(game.get("away_score"))
    home_s = format_score(game.get("home_score"))
    away_n = short_status(game.get("away_team") or "Away", 22)
    home_n = short_status(game.get("home_team") or "Home", 22)

    away_logo = game.get("away_logo") or ""
    home_logo = game.get("home_logo") or ""

    def logo_tag(url: str, alt: str) -> str:
        if not url or not str(url).startswith("http"):
            return ""
        return (
            f'<img class="logo" src="{escape(str(url), quote=True)}" '
            f'alt="{escape(alt)}" loading="lazy" />'
        )

    return (
        f'<div class="sbsby-card" style="overflow:hidden">'
        f'<div class="score-card">'
        f'<div class="team-block">'
        f'{logo_tag(away_logo, away_n)}'
        f'<div class="score">{escape(away_s)}</div>'
        f'<div class="name" title="{escape(str(game.get("away_team") or ""))}">{escape(away_n)}</div>'
        f'</div>'
        f'<div class="score-mid">'
        f'<div class="vs-pill">VS</div>'
        f'<div class="{badge_cls}" title="{escape(str(game.get("status") or ""))}">{escape(status)}</div>'
        f'</div>'
        f'<div class="team-block">'
        f'{logo_tag(home_logo, home_n)}'
        f'<div class="score">{escape(home_s)}</div>'
        f'<div class="name" title="{escape(str(game.get("home_team") or ""))}">{escape(home_n)}</div>'
        f'</div>'
        f'</div>'
        f'<div class="score-meta">{escape(meta)}</div>'
        f'</div>'
    )


def format_score_pair(away: Any, home: Any) -> str:
    return f"{format_score(away)}–{format_score(home)}"
