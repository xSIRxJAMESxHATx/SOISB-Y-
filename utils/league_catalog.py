"""
Load all teams from leagues already in the app (ESPN site API).
Core SO!SB!Y! teams stay first-class; others become selectable configs.
"""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

ESPN = "https://site.api.espn.com/apis/site/v2/sports"

# Leagues tied to existing app teams
LEAGUE_PATHS = {
    "nfl": ("football/nfl", "football", "americanfootball_nfl"),
    "mlb": ("baseball/mlb", "baseball", "baseball_mlb"),
    "nba": ("basketball/nba", "basketball", "basketball_nba"),
    "nhl": ("hockey/nhl", "hockey", "icehockey_nhl"),
    "mls": ("soccer/usa.1", "soccer", "soccer_usa_mls"),
    "ncaaf": ("football/college-football", "football", "americanfootball_ncaaf"),
    "ncaab": ("basketball/mens-college-basketball", "basketball", "basketball_ncaab"),
}

_CACHE: Dict[str, Tuple[float, list]] = {}
_TTL = 3600.0


def _get(url: str) -> dict:
    r = requests.get(url, timeout=12, headers={"User-Agent": "SOSBY/3.5"})
    r.raise_for_status()
    return r.json()


def fetch_league_teams(league_key: str) -> List[dict]:
    now = time.time()
    hit = _CACHE.get(league_key)
    if hit and now - hit[0] < _TTL:
        return hit[1]
    path, sport, odds_key = LEAGUE_PATHS[league_key]
    data = _get(f"{ESPN}/{path}/teams")
    sports = data.get("sports") or []
    out = []
    for sp in sports:
        for lg in sp.get("leagues") or []:
            for t in lg.get("teams") or []:
                team = t.get("team") or t
                tid = str(team.get("id") or "")
                if not tid:
                    continue
                logos = team.get("logos") or []
                out.append({
                    "espn_id": tid,
                    "espn_path": path,
                    "name": team.get("displayName") or team.get("name") or tid,
                    "short": team.get("abbreviation") or team.get("shortDisplayName") or team.get("name") or tid,
                    "sport": sport,
                    "league": path.split("/")[-1],
                    "odds_sport_key": odds_key,
                    "odds_team": team.get("displayName") or team.get("name"),
                    "logo": logos[0].get("href") if logos else None,
                    "league_key": league_key,
                })
    _CACHE[league_key] = (now, out)
    return out


def all_catalog_teams(include_college: bool = True) -> List[dict]:
    keys = ["nfl", "mlb", "nba", "nhl", "mls"]
    if include_college:
        keys.extend(["ncaaf", "ncaab"])
    rows = []
    for k in keys:
        try:
            rows.extend(fetch_league_teams(k))
        except Exception:
            continue
    return rows


def catalog_to_team_cfg(row: dict) -> dict:
    """Build a TEAMS-compatible config for ephemeral selection."""
    return {
        "name": row.get("name") or "Team",
        "short": row.get("short") or "Team",
        "search_name": row.get("name"),
        "sport": row.get("sport") or "",
        "league": row.get("league") or "",
        "espn_id": str(row.get("espn_id") or ""),
        "espn_path": row.get("espn_path") or "",
        "thesportsdb_id": "",
        "odds_sport_key": row.get("odds_sport_key") or "",
        "odds_team": row.get("odds_team") or row.get("name"),
        "colors": {
            "primary": "#FF5A00",
            "secondary": "#E7B100",
            "accent": "#FFFFFF",
            "light_bg": "#FFF8EF",
            "light_card": "#FFFFFF",
            "dark_bg": "#1A1208",
            "dark_card": "#2A1F12",
        },
        "prediction_query": row.get("name") or "",
        "logo": row.get("logo"),
        "ephemeral": True,
        "league_key": row.get("league_key"),
    }


def search_catalog(query: str, limit: int = 40) -> List[dict]:
    q = (query or "").strip().lower()
    rows = all_catalog_teams(include_college=True)
    if not q:
        return rows[:limit]
    hits = []
    for r in rows:
        blob = f"{r.get('name','')} {r.get('short','')}".lower()
        if q in blob:
            hits.append(r)
        if len(hits) >= limit:
            break
    return hits
