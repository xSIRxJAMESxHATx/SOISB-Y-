"""Search main roster + lightweight external team stubs for lab simulations."""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from utils.api_client import TEAMS


def list_team_choices() -> List[Tuple[str, str]]:
    """(key, display label) for all configured teams."""
    out = []
    for k, v in TEAMS.items():
        out.append((k, f"{v.get('name')} ({v.get('league','')})"))
    out.sort(key=lambda x: x[1].lower())
    return out


def search_teams(query: str) -> List[Tuple[str, str]]:
    q = (query or "").strip().lower()
    if not q:
        return list_team_choices()
    hits = []
    for k, v in TEAMS.items():
        blob = " ".join([
            k,
            str(v.get("name") or ""),
            str(v.get("short") or ""),
            str(v.get("search_name") or ""),
            str(v.get("odds_team") or ""),
            str(v.get("league") or ""),
            str(v.get("sport") or ""),
        ]).lower()
        if q in blob or all(part in blob for part in q.split()):
            hits.append((k, f"{v.get('name')} ({v.get('league','')})"))
    hits.sort(key=lambda x: x[1].lower())
    return hits


def resolve_team_key(query: str) -> Optional[str]:
    hits = search_teams(query)
    if len(hits) == 1:
        return hits[0][0]
    # exact short/name match
    q = (query or "").strip().lower()
    for k, v in TEAMS.items():
        if q in {
            k,
            (v.get("short") or "").lower(),
            (v.get("name") or "").lower(),
        }:
            return k
    return hits[0][0] if hits else None
