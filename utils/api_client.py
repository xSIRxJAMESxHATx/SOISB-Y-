"""
SBSBY multi-source sports client — production grade.
Primary: ESPN public endpoints
Fallbacks: TheSportsDB
Optional: The Odds API (ODDS_API_KEY in secrets / env)
Intelligent retries, short TTL cache, graceful missing-data handling.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# ---------------------------------------------------------------------------
# Team configuration
# ---------------------------------------------------------------------------

TEAMS: Dict[str, dict] = {
    "browns": {
        "name": "Cleveland Browns",
        "short": "Browns",
        "sport": "football",
        "league": "nfl",
        "espn_id": "5",
        "espn_path": "football/nfl",
        "thesportsdb_id": "134920",
        "odds_sport_key": "americanfootball_nfl",
        "odds_team": "Cleveland Browns",
        "colors": {
            "primary": "#311D00",
            "secondary": "#FF3C00",
            "accent": "#FFFFFF",
            "light_bg": "#FDF6F0",
            "light_card": "#FFF8F3",
            "dark_bg": "#1A1208",
            "dark_card": "#2A1F12",
        },
        "prediction_query": "Cleveland Browns",
    },
    "guardians": {
        "name": "Cleveland Guardians",
        "short": "Guardians",
        "sport": "baseball",
        "league": "mlb",
        "espn_id": "5",
        "espn_path": "baseball/mlb",
        "thesportsdb_id": "135269",
        "odds_sport_key": "baseball_mlb",
        "odds_team": "Cleveland Guardians",
        "colors": {
            "primary": "#0C2340",
            "secondary": "#E31937",
            "accent": "#FFFFFF",
            "light_bg": "#F0F4F8",
            "light_card": "#F8FBFD",
            "dark_bg": "#0A1520",
            "dark_card": "#122030",
        },
        "prediction_query": "Cleveland Guardians",
    },
    "cavaliers": {
        "name": "Cleveland Cavaliers",
        "short": "Cavaliers",
        "sport": "basketball",
        "league": "nba",
        "espn_id": "5",
        "espn_path": "basketball/nba",
        "thesportsdb_id": "134880",
        "odds_sport_key": "basketball_nba",
        "odds_team": "Cleveland Cavaliers",
        "colors": {
            "primary": "#860038",
            "secondary": "#FDBB30",
            "accent": "#041E42",
            "light_bg": "#FDF5F7",
            "light_card": "#FFF9FB",
            "dark_bg": "#1A0A12",
            "dark_card": "#2A1220",
        },
        "prediction_query": "Cleveland Cavaliers",
    },
    "osu_football": {
        "name": "Ohio State Buckeyes Football",
        "short": "OSU Football",
        "sport": "football",
        "league": "college-football",
        "espn_id": "194",
        "espn_path": "football/college-football",
        "thesportsdb_id": "134940",
        "odds_sport_key": "americanfootball_ncaaf",
        "odds_team": "Ohio State",
        "colors": {
            "primary": "#BB0000",
            "secondary": "#666666",
            "accent": "#FFFFFF",
            "light_bg": "#FDF5F5",
            "light_card": "#FFF8F8",
            "dark_bg": "#1A0808",
            "dark_card": "#2A1010",
        },
        "prediction_query": "Ohio State Football",
    },
    "osu_mbb": {
        "name": "Ohio State Buckeyes Men's Basketball",
        "short": "OSU Men's BB",
        "sport": "basketball",
        "league": "mens-college-basketball",
        "espn_id": "194",
        "espn_path": "basketball/mens-college-basketball",
        "thesportsdb_id": "134941",
        "odds_sport_key": "basketball_ncaab",
        "odds_team": "Ohio State",
        "colors": {
            "primary": "#BB0000",
            "secondary": "#666666",
            "accent": "#FFFFFF",
            "light_bg": "#FDF5F5",
            "light_card": "#FFF8F8",
            "dark_bg": "#1A0808",
            "dark_card": "#2A1010",
        },
        "prediction_query": "Ohio State Basketball",
    },
    "crew": {
        "name": "Columbus Crew",
        "short": "Crew",
        "sport": "soccer",
        "league": "usa.1",
        "espn_id": "183",
        "espn_path": "soccer/usa.1",
        "thesportsdb_id": "134981",
        "odds_sport_key": "soccer_usa_mls",
        "odds_team": "Columbus Crew",
        "colors": {
            "primary": "#000000",
            "secondary": "#FFED00",
            "accent": "#FFFFFF",
            "light_bg": "#FFFEF5",
            "light_card": "#FFFEF8",
            "dark_bg": "#12120A",
            "dark_card": "#1F1F12",
        },
        "prediction_query": "Columbus Crew",
    },
    "bluejackets": {
        "name": "Columbus Blue Jackets",
        "short": "Blue Jackets",
        "sport": "hockey",
        "league": "nhl",
        "espn_id": "29",
        "espn_path": "hockey/nhl",
        "thesportsdb_id": "134863",
        "odds_sport_key": "icehockey_nhl",
        "odds_team": "Columbus Blue Jackets",
        "colors": {
            "primary": "#002654",
            "secondary": "#CE1126",
            "accent": "#A2AAAD",
            "light_bg": "#F0F4F8",
            "light_card": "#F7FAFC",
            "dark_bg": "#0A1520",
            "dark_card": "#122030",
        },
        "prediction_query": "Columbus Blue Jackets",
    },
    "usmnt": {
        "name": "US Men's National Team Soccer",
        "short": "USMNT",
        "sport": "soccer",
        "league": "fifa.world",
        "espn_id": "660",
        "espn_path": "soccer/fifa.world",
        "thesportsdb_id": "135508",
        "odds_sport_key": "soccer_fifa_world_cup",
        "odds_team": "USA",
        "colors": {
            "primary": "#002868",
            "secondary": "#BF0A30",
            "accent": "#FFFFFF",
            "light_bg": "#F5F7FB",
            "light_card": "#FAFBFD",
            "dark_bg": "#0A1020",
            "dark_card": "#121A30",
        },
        "prediction_query": "USMNT USA soccer",
    },
    "usab": {
        "name": "USA Men's Basketball",
        "short": "Team USA BB",
        "sport": "basketball",
        "league": "mens-olympic-basketball",
        "espn_id": "1",
        "espn_path": "basketball/mens-olympic-basketball",
        "thesportsdb_id": "135500",
        "odds_sport_key": "basketball_nba",
        "odds_team": "USA",
        "colors": {
            "primary": "#002868",
            "secondary": "#BF0A30",
            "accent": "#FFFFFF",
            "light_bg": "#F5F7FB",
            "light_card": "#FAFBFD",
            "dark_bg": "#0A1020",
            "dark_card": "#121A30",
        },
        "prediction_query": "Team USA basketball",
    },
    "rhs_football": {
        "name": "Reynoldsburg High School Football",
        "short": "RHS Football",
        "sport": "football",
        "league": "high-school",
        "espn_id": "",
        "espn_path": "football/college-football",
        "thesportsdb_id": "",
        "odds_sport_key": "",
        "odds_team": "Reynoldsburg",
        "colors": {
            "primary": "#4B2E83",
            "secondary": "#E87722",
            "accent": "#FFFFFF",
            "light_bg": "#F8F5FC",
            "light_card": "#FCFAFE",
            "dark_bg": "#140F1C",
            "dark_card": "#221A2E",
        },
        "prediction_query": "Reynoldsburg Raiders football",
        "hs": True,
        "search_name": "Reynoldsburg",
    },
    "rhs_mbb": {
        "name": "Reynoldsburg High School Boys Basketball",
        "short": "RHS Boys BB",
        "sport": "basketball",
        "league": "high-school",
        "espn_id": "",
        "espn_path": "basketball/mens-college-basketball",
        "thesportsdb_id": "",
        "odds_sport_key": "",
        "odds_team": "Reynoldsburg",
        "colors": {
            "primary": "#4B2E83",
            "secondary": "#E87722",
            "accent": "#FFFFFF",
            "light_bg": "#F8F5FC",
            "light_card": "#FCFAFE",
            "dark_bg": "#140F1C",
            "dark_card": "#221A2E",
        },
        "prediction_query": "Reynoldsburg Raiders basketball",
        "hs": True,
        "search_name": "Reynoldsburg",
    },
    "tiffin_tf": {
        "name": "Tiffin University Men's Track & Field",
        "short": "Tiffin Track",
        "sport": "track-and-field",
        "league": "ncaa-d2",
        "espn_id": "",
        "espn_path": "trackandfield/ncaa",
        "thesportsdb_id": "",
        "odds_sport_key": "",
        "odds_team": "Tiffin",
        "colors": {
            "primary": "#4E2A84",
            "secondary": "#C5B358",
            "accent": "#FFFFFF",
            "light_bg": "#F8F5FC",
            "light_card": "#FCFAFE",
            "dark_bg": "#140F1C",
            "dark_card": "#221A2E",
        },
        "prediction_query": "Tiffin University track field",
        "hs": True,
        "search_name": "Tiffin",
    },
    "kent_mbb": {
        "name": "Kent State Men's Basketball",
        "short": "Kent State BB",
        "sport": "basketball",
        "league": "mens-college-basketball",
        "espn_id": "2309",
        "espn_path": "basketball/mens-college-basketball",
        "thesportsdb_id": "134942",
        "odds_sport_key": "basketball_ncaab",
        "odds_team": "Kent State",
        "colors": {
            "primary": "#002664",
            "secondary": "#EAAB00",
            "accent": "#FFFFFF",
            "light_bg": "#F5F8FC",
            "light_card": "#FAFCFF",
            "dark_bg": "#0A1520",
            "dark_card": "#122030",
        },
        "prediction_query": "Kent State basketball",
    },
}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/3"
ODDS_API_BASE = "https://api.the-odds-api.com/v4"


class APIError(Exception):
    pass


def _safe_get(d: Any, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


class SportsAPIClient:
    """Multi-source client with cache, retries, and missing-data safety."""

    def __init__(self, timeout: float = 8.0, cache_ttl: float = 35.0):
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "SBSBY-SportsHub/2.0 (+https://share.streamlit.io)",
                "Accept": "application/json",
            }
        )
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.odds_api_key = (
            os.environ.get("ODDS_API_KEY")
            or os.environ.get("THE_ODDS_API_KEY")
            or ""
        )

    def _get_cached(self, key: str) -> Optional[Any]:
        hit = self._cache.get(key)
        if hit and (time.time() - hit[0]) < self.cache_ttl:
            return hit[1]
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        self._cache[key] = (time.time(), data)

    def clear_cache(self) -> None:
        self._cache.clear()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.4, min=0.4, max=3.5),
        retry=retry_if_exception_type((requests.RequestException, APIError)),
        reraise=True,
    )
    def _request(self, url: str, params: Optional[dict] = None) -> Any:
        resp = self.session.get(url, params=params, timeout=self.timeout)
        if resp.status_code == 429:
            raise APIError(f"Rate limited: {url}")
        if resp.status_code >= 400:
            raise APIError(f"HTTP {resp.status_code}: {url}")
        try:
            return resp.json()
        except ValueError as e:
            raise APIError(f"Bad JSON from {url}") from e

    def _try_sources(
        self,
        sources: List[Tuple[str, Callable[[], Any]]],
        cache_key: str,
        allow_empty: bool = True,
    ) -> Tuple[Any, str]:
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached, "cache"

        errors: List[str] = []
        for name, fn in sources:
            try:
                data = fn()
                if data is None:
                    errors.append(f"{name}: empty")
                    continue
                if not allow_empty and (data == [] or data == {}):
                    errors.append(f"{name}: empty payload")
                    continue
                self._set_cache(cache_key, data)
                return data, name
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {e}")
                continue

        empty: Any = [] if allow_empty else {}
        self._set_cache(cache_key, empty)
        return empty, "fallback-empty"

    # ---- Scoreboard ----
    def get_scoreboard(
        self, team_key: str, date: Optional[str] = None
    ) -> Tuple[List[dict], str]:
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"sb:{team_key}:{date or 'today'}"

        def espn() -> List[dict]:
            params = {}
            if date:
                params["dates"] = date.replace("-", "")
            url = f"{ESPN_BASE}/{team['espn_path']}/scoreboard"
            data = self._request(url, params)
            events = data.get("events") or []
            tid = str(team.get("espn_id") or "")
            search = (team.get("search_name") or team.get("odds_team") or team.get("short") or "").lower()
            aliases = {
                "osu_football": ["ohio state", "buckeyes"],
                "osu_mbb": ["ohio state", "buckeyes"],
                "usmnt": ["united states", "usa", "usmnt"],
                "usab": ["united states", "usa", "team usa"],
                "crew": ["columbus crew", "crew"],
                "bluejackets": ["blue jackets", "columbus"],
                "kent_mbb": ["kent state", "golden flashes"],
            }
            keys = aliases.get(team_key, [search] if search else [])
            out = []
            for ev in events:
                comps = _safe_get(ev, "competitions", default=[{}]) or [{}]
                competitors = comps[0].get("competitors") or []
                ids = [str(_safe_get(c, "team", "id", default="")) for c in competitors]
                names = " ".join(
                    (_safe_get(c, "team", "displayName", default="") or "").lower()
                    for c in competitors
                )
                match_id = tid and tid in ids
                match_name = any(a in names for a in keys if a)
                if match_id or match_name:
                    out.append(self._norm_espn_event(ev))
            if not out:
                # HS / niche: return slate sample so UI is never empty
                out = [self._norm_espn_event(e) for e in events[:12]]
            return out

        def thesportsdb() -> List[dict]:
            url = f"{THESPORTSDB_BASE}/eventsnext.php"
            data = self._request(url, {"id": team["thesportsdb_id"]})
            events = data.get("events") or []
            return [self._norm_tsdb_event(e) for e in events[:8]]

        return self._try_sources(
            [("espn", espn), ("thesportsdb", thesportsdb)], cache_key
        )

    def _norm_espn_event(self, ev: dict) -> dict:
        comps = ev.get("competitions") or [{}]
        comp = comps[0] if comps else {}
        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        status = _safe_get(ev, "status", "type", default={}) or {}
        state = (status.get("state") or "pre").lower()
        odds_list = comp.get("odds") or []
        line = None
        if odds_list:
            o = odds_list[0]
            line = {
                "provider": _safe_get(o, "provider", "name"),
                "spread": o.get("details"),
                "over_under": o.get("overUnder"),
            }
        return {
            "id": ev.get("id"),
            "name": ev.get("name") or ev.get("shortName") or "Game",
            "date": ev.get("date"),
            "status": status.get("description") or "Scheduled",
            "status_state": state,
            "detail": status.get("detail") or status.get("shortDetail"),
            "home_team": _safe_get(home, "team", "displayName", default="Home"),
            "home_score": home.get("score") if home.get("score") is not None else "–",
            "home_logo": _safe_get(home, "team", "logo"),
            "away_team": _safe_get(away, "team", "displayName", default="Away"),
            "away_score": away.get("score") if away.get("score") is not None else "–",
            "away_logo": _safe_get(away, "team", "logo"),
            "venue": _safe_get(comp, "venue", "fullName"),
            "broadcast": ", ".join(
                filter(
                    None,
                    [
                        _safe_get(b, "media", "shortName")
                        for b in (comp.get("broadcasts") or [])
                    ],
                )
            )
            or None,
            "odds": line,
            "source": "espn",
        }

    def _norm_tsdb_event(self, e: dict) -> dict:
        return {
            "id": e.get("idEvent"),
            "name": e.get("strEvent") or "Game",
            "date": e.get("dateEvent"),
            "status": e.get("strStatus") or "Scheduled",
            "status_state": "pre",
            "detail": e.get("strTime"),
            "home_team": e.get("strHomeTeam") or "Home",
            "home_score": e.get("intHomeScore")
            if e.get("intHomeScore") is not None
            else "–",
            "home_logo": None,
            "away_team": e.get("strAwayTeam") or "Away",
            "away_score": e.get("intAwayScore")
            if e.get("intAwayScore") is not None
            else "–",
            "away_logo": None,
            "venue": e.get("strVenue"),
            "broadcast": None,
            "odds": None,
            "source": "thesportsdb",
        }

    # ---- Team info ----
    def get_team_info(self, team_key: str) -> Tuple[dict, str]:
        if team_key not in TEAMS:
            return {"name": "Unknown", "record": "—", "logo": None}, "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"info:{team_key}"

        def espn() -> dict:
            url = f"{ESPN_BASE}/{team['espn_path']}/teams/{team['espn_id']}"
            data = self._request(url)
            t = data.get("team") or {}
            record_items = _safe_get(t, "record", "items", default=[]) or []
            summary = record_items[0].get("summary") if record_items else None
            logos = t.get("logos") or []
            return {
                "name": t.get("displayName") or team["name"],
                "abbreviation": t.get("abbreviation"),
                "location": t.get("location"),
                "logo": logos[0].get("href") if logos else None,
                "record": summary or t.get("standingSummary") or "—",
                "standingSummary": t.get("standingSummary"),
                "source": "espn",
            }

        def thesportsdb() -> dict:
            url = f"{THESPORTSDB_BASE}/lookupteam.php"
            data = self._request(url, {"id": team["thesportsdb_id"]})
            teams = data.get("teams") or []
            if not teams:
                return None
            t = teams[0]
            return {
                "name": t.get("strTeam") or team["name"],
                "abbreviation": t.get("strTeamShort"),
                "location": t.get("strStadiumLocation"),
                "logo": t.get("strTeamBadge"),
                "record": "—",
                "standingSummary": (t.get("strDescriptionEN") or "")[:160],
                "source": "thesportsdb",
            }

        data, src = self._try_sources(
            [("espn", espn), ("thesportsdb", thesportsdb)],
            cache_key,
            allow_empty=False,
        )
        if not data:
            data = {
                "name": team["name"],
                "abbreviation": team["short"][:3].upper(),
                "location": "Ohio",
                "logo": None,
                "record": "—",
                "standingSummary": None,
                "source": "static-fallback",
            }
            src = "static-fallback"
        return data, src

    # ---- News ----
    def get_news(self, team_key: str, limit: int = 12) -> Tuple[List[dict], str]:
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"news:{team_key}:{limit}"

        def espn() -> List[dict]:
            url = f"{ESPN_BASE}/{team['espn_path']}/news"
            data = self._request(url, {"limit": limit})
            articles = data.get("articles") or []
            out = []
            for a in articles[:limit]:
                out.append(
                    {
                        "headline": a.get("headline") or "Headline",
                        "description": a.get("description") or "",
                        "published": a.get("published") or "",
                        "url": _safe_get(a, "links", "web", "href") or "#",
                        "image": (a.get("images") or [{}])[0].get("url"),
                        "source": "ESPN",
                    }
                )
            return out

        return self._try_sources([("espn", espn)], cache_key)

    # ---- Standings ----
    def get_standings(self, team_key: str) -> Tuple[List[dict], str]:
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"std:{team_key}"

        def espn() -> List[dict]:
            url = f"{ESPN_BASE}/{team['espn_path']}/standings"
            data = self._request(url)
            rows: List[dict] = []

            def walk(node: Any) -> None:
                if isinstance(node, dict):
                    entries = _safe_get(node, "standings", "entries")
                    if entries:
                        for entry in entries:
                            team_obj = entry.get("team") or {}
                            stats = {
                                s.get("name"): s.get("displayValue")
                                for s in (entry.get("stats") or [])
                                if s.get("name")
                            }
                            rows.append(
                                {
                                    "Team": team_obj.get("displayName") or "—",
                                    "W": stats.get("wins")
                                    or stats.get("overall")
                                    or "—",
                                    "L": stats.get("losses") or "—",
                                    "PCT": stats.get("winPercent") or "—",
                                    "GB": stats.get("gamesBehind") or "—",
                                    "STRK": stats.get("streak") or "—",
                                }
                            )
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for item in node:
                        walk(item)

            walk(data)
            seen = set()
            unique = []
            for r in rows:
                if r["Team"] not in seen:
                    seen.add(r["Team"])
                    unique.append(r)
            return unique[:50] if unique else None

        return self._try_sources([("espn", espn)], cache_key)

    # ---- Schedule ----
    def get_schedule(self, team_key: str) -> Tuple[List[dict], str]:
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"sch:{team_key}"

        def espn() -> List[dict]:
            url = f"{ESPN_BASE}/{team['espn_path']}/teams/{team['espn_id']}/schedule"
            data = self._request(url)
            events = data.get("events") or []
            return [self._norm_espn_event(e) for e in events[-20:]]

        def thesportsdb() -> List[dict]:
            url = f"{THESPORTSDB_BASE}/eventsnext.php"
            data = self._request(url, {"id": team["thesportsdb_id"]})
            events = data.get("events") or []
            past = self._request(
                f"{THESPORTSDB_BASE}/eventslast.php",
                {"id": team["thesportsdb_id"]},
            )
            past_events = past.get("results") or []
            return [
                self._norm_tsdb_event(e)
                for e in (list(past_events)[-5:] + list(events)[:8])
            ]

        return self._try_sources(
            [("espn", espn), ("thesportsdb", thesportsdb)], cache_key
        )

    def get_recent_form(self, team_key: str) -> Tuple[List[dict], str]:
        try:
            schedule, src = self.get_schedule(team_key)
            finished = [
                g
                for g in schedule
                if (g.get("status_state") or "") in ("post", "final")
                or "final" in str(g.get("status", "")).lower()
            ]
            return finished[-10:], src
        except Exception:
            return [], "none"

    # ---- Odds (optional The Odds API) ----
    def set_odds_key(self, key: str) -> None:
        self.odds_api_key = (key or "").strip()

    def get_odds(self, team_key: str) -> Tuple[List[dict], str]:
        if team_key not in TEAMS:
            return [], "unknown-team"
        if not self.odds_api_key:
            return [], "no-api-key"
        team = TEAMS[team_key]
        cache_key = f"odds:{team_key}"
        sport_key = team.get("odds_sport_key")
        team_name = (team.get("odds_team") or "").lower()

        def odds_api() -> List[dict]:
            url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
            params = {
                "apiKey": self.odds_api_key,
                "regions": "us",
                "markets": "h2h,spreads,totals",
                "oddsFormat": "american",
            }
            data = self._request(url, params)
            if not isinstance(data, list):
                return []
            out = []
            for game in data:
                home = (game.get("home_team") or "").lower()
                away = (game.get("away_team") or "").lower()
                relevant = team_name in home or team_name in away
                if not relevant and len(out) >= 5:
                    continue
                bookmakers = game.get("bookmakers") or []
                books = []
                for bm in bookmakers[:5]:
                    markets = {}
                    for m in bm.get("markets") or []:
                        markets[m.get("key")] = [
                            {
                                "name": o.get("name"),
                                "price": o.get("price"),
                                "point": o.get("point"),
                            }
                            for o in (m.get("outcomes") or [])
                        ]
                    books.append({"book": bm.get("title"), "markets": markets})
                out.append(
                    {
                        "commence_time": game.get("commence_time"),
                        "home_team": game.get("home_team"),
                        "away_team": game.get("away_team"),
                        "sport": game.get("sport_title"),
                        "bookmakers": books,
                        "relevant": relevant,
                    }
                )
            # prefer relevant games first
            out.sort(key=lambda g: (not g["relevant"], g.get("commence_time") or ""))
            return out[:10]

        return self._try_sources([("the-odds-api", odds_api)], cache_key)

    def prediction_links(self, team_key: str) -> List[dict]:
        q = TEAMS.get(team_key, {}).get("prediction_query", "Cleveland")
        qq = quote_plus(q)
        return [
            {
                "name": "Polymarket",
                "url": f"https://polymarket.com/search?q={qq}",
                "desc": "Crypto prediction markets — game & season contracts",
            },
            {
                "name": "Kalshi",
                "url": f"https://kalshi.com/search?q={qq}",
                "desc": "CFTC-regulated event contracts",
            },
            {
                "name": "ESPN search",
                "url": f"https://www.espn.com/search/_/q/{qq}",
                "desc": "News + odds ecosystem",
            },
            {
                "name": "The Odds API",
                "url": "https://the-odds-api.com/",
                "desc": "Free key powers in-app consensus odds",
            },
        ]

    def any_live_games(self, team_key: str) -> bool:
        try:
            games, _ = self.get_scoreboard(team_key)
            return any((g.get("status_state") or "") == "in" for g in games)
        except Exception:
            return False



    def get_betting_dashboard(self, team_key: str) -> Tuple[dict, str]:
        """Unified betting payload: live odds + ESPN lines + market links."""
        result = {
            "games": [],
            "has_api_key": bool(self.odds_api_key),
            "espn_lines": [],
            "links": self.prediction_links(team_key),
        }
        sources = []
        # Odds API
        try:
            games, src = self.get_odds(team_key)
            result["games"] = games
            sources.append(src)
        except Exception as e:
            sources.append(f"odds-api:{e}")
        # ESPN scoreboard embedded lines
        try:
            sb, ssrc = self.get_scoreboard(team_key)
            lines = []
            for g in sb:
                if g.get("odds"):
                    lines.append({
                        "matchup": g.get("name"),
                        "status": g.get("status"),
                        "odds": g.get("odds"),
                        "home": g.get("home_team"),
                        "away": g.get("away_team"),
                    })
            result["espn_lines"] = lines
            sources.append(ssrc)
        except Exception as e:
            sources.append(f"espn-lines:{e}")
        return result, "+".join(sources[:4])



@lru_cache(maxsize=1)
def get_client() -> SportsAPIClient:
    return SportsAPIClient()
