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
        "name": "Reynoldsburg Raiders Football",
        "short": "Raiders FB",
        "sport": "football",
        "league": "high-school",
        "espn_id": "",
        "espn_path": "football/college-football",
        "thesportsdb_id": "",
        "odds_sport_key": "",
        "odds_team": "Reynoldsburg",
        "colors": {
            "primary": "#4B2E83",
            "secondary": "#C5A000",
            "accent": "#FFFFFF",
            "light_bg": "#F8F5FC",
            "light_card": "#FCFAFE",
            "dark_bg": "#140F1C",
            "dark_card": "#221A2E",
        },
        "prediction_query": "Reynoldsburg Raiders football",
        "hs": True,
        "search_name": "Reynoldsburg",
        "mascot": "Raiders",
    },
    "rhs_mbb": {
        "name": "Reynoldsburg Raiders Boys Basketball",
        "short": "Raiders BB",
        "sport": "basketball",
        "league": "high-school",
        "espn_id": "",
        "espn_path": "basketball/mens-college-basketball",
        "thesportsdb_id": "",
        "odds_sport_key": "",
        "odds_team": "Reynoldsburg",
        "colors": {
            "primary": "#4B2E83",
            "secondary": "#C5A000",
            "accent": "#FFFFFF",
            "light_bg": "#F8F5FC",
            "light_card": "#FCFAFE",
            "dark_bg": "#140F1C",
            "dark_card": "#221A2E",
        },
        "prediction_query": "Reynoldsburg Raiders basketball",
        "hs": True,
        "search_name": "Reynoldsburg",
        "mascot": "Raiders",
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
THESPORTSDB_BASE = "https://www.thesportsdb.com/api/v1/json/123"  # free tier key; 30 req/min
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


REDDIT_SUBS = {
    "browns": "https://www.reddit.com/r/Browns/",
    "guardians": "https://www.reddit.com/r/ClevelandGuardians/",
    "cavaliers": "https://www.reddit.com/r/clevelandcavs/",
    "osu_football": "https://www.reddit.com/r/OhioStateFootball/",
    "osu_mbb": "https://www.reddit.com/r/OhioStateBasketball/",
    "crew": "https://www.reddit.com/r/columbuscrew/",
    "bluejackets": "https://www.reddit.com/r/BlueJackets/",
    "usmnt": "https://www.reddit.com/r/ussoccer/",
    "usab": "https://www.reddit.com/r/usabasketball/",
    "kent_mbb": "https://www.reddit.com/r/KentState/",
    "rhs_football": "https://www.reddit.com/r/highschoolfootball/",
    "rhs_mbb": "https://www.reddit.com/r/Basketball/",
    "tiffin_tf": "https://www.reddit.com/r/trackandfield/",
}


def reddit_url(team_key: str) -> str:
    return REDDIT_SUBS.get(team_key) or (
        "https://www.reddit.com/search/?q=" + quote_plus(
            (TEAMS.get(team_key) or {}).get("name") or team_key
        )
    )


# Local-only cards for programs without stable ESPN IDs
LOCAL_PROGRAMS = {
    "rhs_football": {
        "label": "Reynoldsburg Raiders Football",
        "note": "OHSAA / OCC — purple & gold. Live scores via local/NFHS sources when in season.",
        "links": [
            ("NFHS Network", "https://www.nfhsnetwork.com/"),
            ("MaxPreps search", "https://www.maxpreps.com/search/default.aspx?type=school&search=reynoldsburg&state=oh"),
            ("Google schedule", "https://www.google.com/search?q=Reynoldsburg+Raiders+football+schedule"),
        ],
    },
    "rhs_mbb": {
        "label": "Reynoldsburg Raiders Boys Basketball",
        "note": "OHSAA boys basketball — purple & gold Raiders.",
        "links": [
            ("NFHS Network", "https://www.nfhsnetwork.com/"),
            ("MaxPreps search", "https://www.maxpreps.com/search/default.aspx?type=school&search=reynoldsburg&state=oh"),
            ("Google schedule", "https://www.google.com/search?q=Reynoldsburg+Raiders+basketball+schedule"),
        ],
    },
    "tiffin_tf": {
        "label": "Tiffin University Men's Track & Field",
        "note": "NCAA DII / G-MAC — Dragons track & field. Meets populate seasonally.",
        "links": [
            ("Tiffin Athletics", "https://gotiffindragons.com/"),
            ("TFRRS search", "https://www.tfrrs.org/"),
            ("Google schedule", "https://www.google.com/search?q=Tiffin+University+track+and+field+schedule"),
        ],
    },
}


def local_program_rows(team_key: str, kind: str = "schedule") -> List[dict]:
    prog = LOCAL_PROGRAMS.get(team_key) or {}
    label = prog.get("label") or team_key
    note = prog.get("note") or ""
    sport_hint = ""
    if "football" in team_key:
        sport_hint = "football"
    elif "mbb" in team_key or "basketball" in team_key:
        sport_hint = "basketball"
    elif "tf" in team_key or "track" in team_key:
        sport_hint = "track"

    # MaxPreps enrichment for OH high schools
    mp_rows: List[dict] = []
    if team_key.startswith("rhs_"):
        try:
            from .maxpreps import as_schedule_rows, as_standings_rows
            if kind == "standings":
                mp_rows = as_standings_rows("Reynoldsburg", "oh", sport_hint)
            else:
                mp_rows = as_schedule_rows("Reynoldsburg", "oh", sport_hint)
        except Exception:
            mp_rows = []

    if kind == "standings":
        base = [{
            "Team": label,
            "W": "—",
            "L": "—",
            "PCT": "—",
            "GB": "—",
            "STRK": note[:80] or "Local program",
        }] + [
            {"Team": name, "W": "link", "L": "", "PCT": "", "GB": "", "STRK": url}
            for name, url in (prog.get("links") or [])
        ]
        # merge maxpreps standings links (skip duplicate Team header)
        for r in mp_rows:
            if r.get("Team") and r.get("Team") != label:
                base.append(r)
        return base

    rows = [{
        "id": f"local-{team_key}",
        "name": label,
        "date": "",
        "status": "Program hub",
        "status_state": "pre",
        "detail": note,
        "home_team": label,
        "home_score": "–",
        "away_team": "See links",
        "away_score": "–",
        "venue": "",
        "broadcast": None,
        "source": "local-program",
    }]
    for name, url in (prog.get("links") or []):
        rows.append({
            "id": url,
            "name": name,
            "date": "",
            "status": "Link",
            "status_state": "pre",
            "detail": url,
            "home_team": name,
            "home_score": "–",
            "away_team": "Open",
            "away_score": "–",
            "venue": "",
            "broadcast": None,
            "source": "local-program",
        })
    for r in mp_rows:
        rows.append(r)
    return rows


class SportsAPIClient:
    """Multi-source client: memory + disk cache, exponential backoff, throttle."""

    def __init__(self, timeout: float = 7.0, cache_ttl: float = 45.0):
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.live_cache_ttl = 15.0
        self.schedule_ttl = 180.0
        self.standings_ttl = 300.0
        self.news_ttl = 120.0
        self._min_interval = 0.4
        self._last_request_ts = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "SOSBY-SportsHub/3.4 (+https://share.streamlit.io)",
                "Accept": "application/json",
            }
        )
        # memory: key -> (ts, data, ttl)
        self._cache: Dict[str, Tuple[float, Any, float]] = {}
        self.odds_api_key = (
            os.environ.get("ODDS_API_KEY")
            or os.environ.get("THE_ODDS_API_KEY")
            or ""
        )

    def _get_cached(self, key: str) -> Optional[Any]:
        hit = self._cache.get(key)
        if hit:
            ts, data, ttl = hit
            if (time.time() - ts) < ttl:
                return data
        # disk layer
        try:
            from .disk_cache import disk_get
            # use longest relevant default for disk
            disk_ttl = self.schedule_ttl
            if key.startswith("sb:"):
                disk_ttl = self.live_cache_ttl
            elif key.startswith("std:"):
                disk_ttl = self.standings_ttl
            elif key.startswith("news:"):
                disk_ttl = self.news_ttl
            data = disk_get(key, disk_ttl)
            if data is not None:
                self._cache[key] = (time.time(), data, disk_ttl)
                return data
        except Exception:
            pass
        return None

    def _set_cache(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        use_ttl = float(ttl if ttl is not None else self.cache_ttl)
        self._cache[key] = (time.time(), data, use_ttl)
        try:
            from .disk_cache import disk_set
            disk_set(key, data)
        except Exception:
            pass

    def clear_cache(self) -> None:
        self._cache.clear()
        try:
            from .disk_cache import disk_clear
            disk_clear()
        except Exception:
            pass

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_ts
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_ts = time.time()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=0.6, min=0.5, max=8.0),
        retry=retry_if_exception_type((requests.RequestException, APIError)),
        reraise=True,
    )
    def _request(self, url: str, params: Optional[dict] = None) -> Any:
        """HTTP GET with throttle + exponential backoff (tenacity)."""
        self._throttle()
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}") from e
        if resp.status_code == 429:
            # explicit backoff before tenacity also retries
            time.sleep(2.0)
            raise APIError(f"Rate limited: {url}")
        if resp.status_code >= 500:
            raise APIError(f"Server {resp.status_code}: {url}")
        if resp.status_code >= 400:
            # don't retry most 4xx except 429
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
        ttl: Optional[float] = None,
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
                use_ttl = ttl
                if use_ttl is None:
                    if cache_key.startswith("sb:"):
                        try:
                            live = any(
                                (g.get("status_state") or "") == "in"
                                for g in (data if isinstance(data, list) else [])
                            )
                            use_ttl = self.live_cache_ttl if live else self.cache_ttl
                        except Exception:
                            use_ttl = self.cache_ttl
                    elif cache_key.startswith("sch:"):
                        use_ttl = self.schedule_ttl
                    elif cache_key.startswith("std:"):
                        use_ttl = self.standings_ttl
                    elif cache_key.startswith("news:"):
                        use_ttl = self.news_ttl
                    else:
                        use_ttl = self.cache_ttl
                self._set_cache(cache_key, data, use_ttl)
                return data, name
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {e}")
                continue

        empty: Any = [] 
        self._set_cache(cache_key, empty, 20.0)
        return empty, "none:" + ";".join(errors[:3])

    def get_scoreboard(
        self, team_key: str, date: Optional[str] = None
    ) -> Tuple[List[dict], str]:
        """Real-time scoreboard — most reliable path with multi-source failover."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"sb:{team_key}:{date or 'today'}:v4"
        # HS / track: always-available local program rows (ESPN IDs unreliable)
        if team.get("hs") and team_key in LOCAL_PROGRAMS:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached, "cache"
            # still try ESPN/schedule once, then local
            try:
                if team.get("espn_id"):
                    pass  # fall through to normal sources
                else:
                    rows = local_program_rows(team_key, "schedule")
                    self._set_cache(cache_key, rows, self.cache_ttl)
                    return rows, "local-program"
            except Exception:
                rows = local_program_rows(team_key, "schedule")
                return rows, "local-program"
        path = team.get("espn_path") or ""
        tid = str(team.get("espn_id") or "")
        search = (
            team.get("search_name")
            or team.get("odds_team")
            or team.get("short")
            or team.get("name")
            or ""
        ).lower()
        name_l = (team.get("name") or "").lower()

        def _filter_events(events: List[dict]) -> List[dict]:
            out = []
            for e in events or []:
                g = self._norm_espn_event(e) if "competitions" in e or "status" in e else e
                if not isinstance(g, dict):
                    continue
                # already normalized path
                if "home_team" not in g and "competitions" in e:
                    g = self._norm_espn_event(e)
                blob = f"{g.get('name','')} {g.get('home_team','')} {g.get('away_team','')}".lower()
                if tid:
                    # prefer team id match when competitors available
                    comps = _safe_get(e, "competitions", 0, "competitors") or []
                    ids = [str(_safe_get(c, "team", "id") or "") for c in comps]
                    if tid in ids or (search and search in blob) or (name_l and name_l.split()[-1] in blob):
                        out.append(g if "home_team" in g else self._norm_espn_event(e))
                elif search and search in blob:
                    out.append(g if "home_team" in g else self._norm_espn_event(e))
                elif name_l and any(p in blob for p in name_l.split() if len(p) > 3):
                    out.append(g if "home_team" in g else self._norm_espn_event(e))
            # de-dupe by id/name
            seen = set()
            uniq = []
            for g in out:
                k = g.get("id") or g.get("name")
                if k in seen:
                    continue
                seen.add(k)
                uniq.append(g)
            return uniq

        def espn_scoreboard() -> Optional[List[dict]]:
            params = {}
            if date:
                params["dates"] = date.replace("-", "")
            data = self._request(f"{ESPN_BASE}/{path}/scoreboard", params)
            events = data.get("events") or []
            # also try dates=today explicitly
            if not events and not date:
                from datetime import datetime, timezone
                params["dates"] = datetime.now(timezone.utc).strftime("%Y%m%d")
                data = self._request(f"{ESPN_BASE}/{path}/scoreboard", params)
                events = data.get("events") or []
            filtered = _filter_events(events)
            if filtered:
                return filtered
            # if filter empty but events exist and team is national/olympic, return all limited
            if events and team.get("league") in ("mens-olympic-basketball", "soccer"):
                return [self._norm_espn_event(e) for e in events[:12]]
            return filtered if filtered else None

        def espn_team_schedule_scores() -> Optional[List[dict]]:
            if not tid:
                return None
            data = self._request(f"{ESPN_BASE}/{path}/teams/{tid}/schedule")
            events = data.get("events") or []
            out = []
            for e in events:
                g = self._norm_espn_event(e)
                st = (g.get("status_state") or "").lower()
                # prefer live + recent
                if st in ("in", "post", "pre"):
                    out.append(g)
            # put live first
            out.sort(key=lambda g: 0 if g.get("status_state") == "in" else 1)
            return out[:15] if out else None

        def espn_scoreboard_group() -> Optional[List[dict]]:
            # some leagues expose groups; soft attempt
            data = self._request(f"{ESPN_BASE}/{path}/scoreboard", {"limit": 50})
            events = data.get("events") or []
            filtered = _filter_events(events)
            return filtered if filtered else None

        def thesportsdb_next_last() -> Optional[List[dict]]:
            tsid = team.get("thesportsdb_id") or ""
            if not tsid:
                return None
            out = []
            for endpoint in ("eventslast.php", "eventsnext.php"):
                data = self._request(f"{THESPORTSDB_BASE}/{endpoint}", {"id": tsid})
                key = "results" if "last" in endpoint else "events"
                for e in data.get(key) or []:
                    g = self._norm_tsdb_event(e)
                    # mark finished last events
                    if "last" in endpoint and g.get("home_score") not in (None, "–"):
                        g["status_state"] = "post"
                        g["status"] = "Final"
                    out.append(g)
            return out[:12] if out else None

        def thesportsdb_livescore() -> Optional[List[dict]]:
            # league livescore when sport known
            sport = (team.get("sport") or "").lower()
            league_map = {
                "soccer": "soccer",
                "basketball": "basketball",
                "baseball": "baseball",
                "football": "americanfootball",
                "hockey": "icehockey",
            }
            s = league_map.get(sport)
            if not s:
                return None
            try:
                data = self._request(f"{THESPORTSDB_BASE}/livescore.php", {"s": s})
            except Exception:
                return None
            events = data.get("events") or data.get("livescore") or []
            if not events:
                return None
            out = []
            for e in events:
                g = self._norm_tsdb_event(e)
                blob = f"{g.get('name','')} {g.get('home_team','')} {g.get('away_team','')}".lower()
                if search in blob or (name_l and name_l.split()[0] in blob):
                    g["status_state"] = "in"
                    g["status"] = "LIVE"
                    out.append(g)
            return out if out else None

        return self._try_sources(
            [
                ("espn-scoreboard", espn_scoreboard),
                ("espn-team-schedule", espn_team_schedule_scores),
                ("espn-scoreboard-wide", espn_scoreboard_group),
                ("tsdb-live", thesportsdb_livescore),
                ("tsdb-next-last", thesportsdb_next_last),
            ],
            cache_key,
            allow_empty=True,
        )

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
        """Headlines only for the selected team (no long club descriptions)."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"news:{team_key}:{limit}:v3"
        needles = []
        for k in ("name", "short", "odds_team", "search_name", "mascot"):
            v = (team.get(k) or "").lower().strip()
            if v and len(v) > 2 and v not in needles:
                needles.append(v)
        for part in (team.get("name") or "").lower().split():
            if len(part) > 3 and part not in needles:
                needles.append(part)

        def _relevant(h: str, d: str = "") -> bool:
            text = f"{h} {d}".lower()
            return any(n in text for n in needles) if needles else True

        def espn_team_news() -> Optional[List[dict]]:
            tid, path = team.get("espn_id") or "", team.get("espn_path") or ""
            if not tid or not path or team.get("hs"):
                return None
            try:
                data = self._request(f"{ESPN_BASE}/{path}/teams/{tid}/news", {"limit": max(limit, 10)})
            except Exception:
                return None
            out = []
            for a in data.get("articles") or []:
                h, d = a.get("headline") or "", a.get("description") or ""
                out.append({
                    "headline": h or "Headline",
                    "description": (d or "")[:180],
                    "published": a.get("published") or "",
                    "url": _safe_get(a, "links", "web", "href") or "#",
                    "image": (a.get("images") or [{}])[0].get("url"),
                    "source": "ESPN",
                })
                if len(out) >= limit:
                    break
            return out or None

        def espn_filtered() -> Optional[List[dict]]:
            path = team.get("espn_path") or ""
            if not path or team.get("hs"):
                return None
            try:
                data = self._request(f"{ESPN_BASE}/{path}/news", {"limit": 50})
            except Exception:
                return None
            out = []
            for a in data.get("articles") or []:
                h, d = a.get("headline") or "", a.get("description") or ""
                if not _relevant(h, d):
                    continue
                out.append({
                    "headline": h,
                    "description": (d or "")[:180],
                    "published": a.get("published") or "",
                    "url": _safe_get(a, "links", "web", "href") or "#",
                    "image": (a.get("images") or [{}])[0].get("url"),
                    "source": "ESPN filtered",
                })
                if len(out) >= limit:
                    break
            return out or None

        def search_links() -> List[dict]:
            q = quote_plus(team.get("name") or team_key)
            return [
                {"headline": f"{team.get('name')} — Google News", "description": "", "published": "", "url": f"https://www.google.com/search?q={q}&tbm=nws", "image": None, "source": "Google"},
                {"headline": f"{team.get('name')} — ESPN", "description": "", "published": "", "url": f"https://www.espn.com/search/_/q/{q}", "image": None, "source": "ESPN"},
                {"headline": f"{team.get('name')} — CBS", "description": "", "published": "", "url": f"https://www.cbssports.com/search/{q}/", "image": None, "source": "CBS"},
            ]

        return self._try_sources(
            [("espn-team", espn_team_news), ("espn-filtered", espn_filtered), ("links", search_links)],
            cache_key,
        )

    def get_standings(self, team_key: str) -> Tuple[List[dict], str]:
        """Always return standings context for the selected team."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"std:{team_key}:v4"
        if team.get("hs") and team_key in LOCAL_PROGRAMS and not team.get("espn_id"):
            rows = local_program_rows(team_key, "standings")
            return rows, "local-program"
        path = team.get("espn_path") or ""
        tid = str(team.get("espn_id") or "")
        year = time.gmtime().tm_year
        focus = (team.get("name") or team.get("short") or "").lower()

        def _parse_entries(data: Any) -> List[dict]:
            rows: List[dict] = []

            def walk(node: Any) -> None:
                if isinstance(node, dict):
                    entries = node.get("entries") or _safe_get(node, "standings", "entries") or []
                    if isinstance(entries, list) and entries and isinstance(entries[0], dict) and "team" in (entries[0] or {}):
                        for entry in entries:
                            team_obj = entry.get("team") or {}
                            stats = {
                                s.get("name"): s.get("displayValue")
                                for s in (entry.get("stats") or [])
                                if s.get("name")
                            }
                            rows.append({
                                "Team": team_obj.get("displayName") or team_obj.get("name") or "—",
                                "W": stats.get("wins") or stats.get("overallWins") or stats.get("wins") or "—",
                                "L": stats.get("losses") or stats.get("overallLosses") or "—",
                                "PCT": stats.get("winPercent") or stats.get("avgPointsFor") or "—",
                                "GB": stats.get("gamesBehind") or "—",
                                "STRK": stats.get("streak") or stats.get("total") or "—",
                            })
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for item in node:
                        walk(item)

            walk(data)
            seen = set()
            uniq = []
            for r in rows:
                if r["Team"] not in seen:
                    seen.add(r["Team"])
                    uniq.append(r)
            return uniq

        def espn_standings() -> Optional[List[dict]]:
            for url in (
                f"{ESPN_BASE}/{path}/standings",
                f"{ESPN_BASE}/{path}/standings?season={year}",
                f"{ESPN_BASE}/{path}/standings?season={year-1}",
            ):
                try:
                    data = self._request(url)
                except Exception:
                    continue
                rows = _parse_entries(data)
                if rows:
                    return rows[:40]
            return None

        def espn_team_record_row() -> Optional[List[dict]]:
            if not tid:
                return None
            try:
                data = self._request(f"{ESPN_BASE}/{path}/teams/{tid}")
            except Exception:
                return None
            t0 = data.get("team") or {}
            rec = "—"
            for item in (t0.get("record") or {}).get("items") or []:
                if item.get("type") == "total" or item.get("description") == "Overall Summary":
                    rec = item.get("summary") or rec
                    break
            standing = t0.get("standingSummary") or ""
            return [{
                "Team": t0.get("displayName") or team.get("name"),
                "W": rec.split("-")[0] if "-" in str(rec) else rec,
                "L": rec.split("-")[1] if "-" in str(rec) and len(rec.split("-")) > 1 else "—",
                "PCT": "—",
                "GB": "—",
                "STRK": standing or "Team record",
            }]

        def curated_fallback() -> List[dict]:
            q = quote_plus(team.get("name") or team_key)
            return [
                {
                    "Team": team.get("name") or team_key,
                    "W": "—",
                    "L": "—",
                    "PCT": "—",
                    "GB": "—",
                    "STRK": f"Selected team · {team.get('league')}",
                },
                {"Team": "ESPN standings", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.espn.com/search/_/q/{q}%20standings"},
                {"Team": "CBS Sports", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.cbssports.com/search/{q}/"},
                {"Team": "FOX Sports", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.foxsports.com/search?q={q}"},
                {"Team": "Google", "W": "link", "L": "", "PCT": "", "GB": "", "STRK": f"https://www.google.com/search?q={q}+standings"},
            ]

        rows, src = self._try_sources(
            [
                ("espn-standings", espn_standings),
                ("espn-team-record", espn_team_record_row),
                ("fallback", curated_fallback),
            ],
            cache_key,
        )
        rows = rows or curated_fallback()
        # Move selected team to top when present
        if focus and rows:
            def score(r):
                name = (r.get("Team") or "").lower()
                return 0 if any(p in name for p in focus.split() if len(p) > 2) else 1
            rows = sorted(rows, key=score)
        return rows, src

    def get_schedule(self, team_key: str) -> Tuple[List[dict], str]:
        """Always populate selected team's schedule."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        cache_key = f"sch:{team_key}:v4"
        if team.get("hs") and team_key in LOCAL_PROGRAMS and not team.get("espn_id"):
            return local_program_rows(team_key, "schedule"), "local-program"
        path = team.get("espn_path") or ""
        tid = str(team.get("espn_id") or "")

        def espn_team_schedule() -> Optional[List[dict]]:
            if not tid:
                return None
            try:
                data = self._request(f"{ESPN_BASE}/{path}/teams/{tid}/schedule")
            except Exception:
                return None
            events = data.get("events") or []
            out = [self._norm_espn_event(e) for e in events]
            return out[-30:] if out else None

        def espn_scoreboard_as_schedule() -> Optional[List[dict]]:
            try:
                games, _ = self.get_scoreboard(team_key)
            except Exception:
                games = []
            return games if games else None

        def tsdb_schedule() -> Optional[List[dict]]:
            tsid = team.get("thesportsdb_id") or ""
            if not tsid:
                return None
            out = []
            for endpoint, key in (("eventslast.php", "results"), ("eventsnext.php", "events")):
                try:
                    data = self._request(f"{THESPORTSDB_BASE}/{endpoint}", {"id": tsid})
                except Exception:
                    continue
                for e in data.get(key) or []:
                    out.append(self._norm_tsdb_event(e))
            return out if out else None

        def link_fallback() -> List[dict]:
            q = quote_plus(team.get("name") or team_key)
            return [{
                "id": "link",
                "name": f"{team.get('name')} schedule (search)",
                "date": "",
                "status": "See link",
                "status_state": "pre",
                "detail": f"https://www.google.com/search?q={q}+schedule",
                "home_team": team.get("short") or "",
                "home_score": "–",
                "away_team": "Schedule",
                "away_score": "–",
                "venue": "",
                "broadcast": None,
                "source": "search",
            }]

        return self._try_sources(
            [
                ("espn-team-schedule", espn_team_schedule),
                ("espn-scoreboard", espn_scoreboard_as_schedule),
                ("thesportsdb", tsdb_schedule),
                ("search-link", link_fallback),
            ],
            cache_key,
        )

    def get_recent_form(self, team_key: str) -> Tuple[List[dict], str]:
        """Recent finished games for selected team only; falls back to broader history."""
        if team_key not in TEAMS:
            return [], "unknown-team"
        team = TEAMS[team_key]
        name = (team.get("name") or "").lower()
        short = (team.get("short") or "").lower()

        def _involves_team(g: dict) -> bool:
            blob = f"{g.get('name','')} {g.get('home_team','')} {g.get('away_team','')}".lower()
            return (name and name in blob) or (short and short in blob) or not name

        try:
            schedule, src = self.get_schedule(team_key)
            finished = [
                g for g in schedule
                if (
                    (g.get("status_state") or "") in ("post", "final")
                    or "final" in str(g.get("status", "")).lower()
                )
                and _involves_team(g)
            ]
            if finished:
                return finished[-12:], src
        except Exception:
            pass

        # TheSportsDB last events
        try:
            tid = team.get("thesportsdb_id") or ""
            if tid:
                past = self._request(f"{THESPORTSDB_BASE}/eventslast.php", {"id": tid})
                events = past.get("results") or []
                out = [self._norm_tsdb_event(e) for e in events if e]
                out = [g for g in out if _involves_team(g)]
                if out:
                    return out[-12:], "thesportsdb-last"
        except Exception:
            pass

        return [], "none"

    def get_all_time_trends(self, team_key: str) -> Tuple[List[dict], str]:
        """Curated / historical trend points when live form is empty."""
        from .curated_data import ALL_TIME_LEADERS, CHAMPIONSHIP_GREATS
        rows: List[dict] = []
        greats = (CHAMPIONSHIP_GREATS or {}).get(team_key) or []
        for g in greats[:8]:
            rows.append({
                "era": g.get("era") or "",
                "player": g.get("player") or "",
                "note": g.get("why") or g.get("titles") or "Historical marker",
                "kind": "great",
            })
        leaders = (ALL_TIME_LEADERS or {}).get(team_key) or {}
        for cat, entries in list(leaders.items())[:4]:
            for e in (entries or [])[:3]:
                rows.append({
                    "era": cat,
                    "player": e.get("player") or "",
                    "note": f"{e.get('value','')} — all-time leader context",
                    "kind": "leader",
                })
        if not rows:
            team = TEAMS.get(team_key, {})
            rows = [{
                "era": "franchise",
                "player": team.get("short") or team_key,
                "note": f"Historical trend data limited for {team.get('name') or team_key}.",
                "kind": "meta",
            }]
        return rows, "curated-all-time"

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
